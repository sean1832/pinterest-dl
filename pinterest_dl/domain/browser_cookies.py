import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Optional


def load_firefox_cookies(domain: Optional[str] = None) -> list[dict]:
    """Extract cookies from an installed browser's on-disk storage.

    Only Firefox is supported.
    For Chromium-based browsers, use Playwright's cookie extraction instead.

    _Chromium's App-Bound Encryption (v20, rolling out in 2024) makes direct cookie extraction infeasible._

    Args:
        domain (str | None, optional): Domain for which to extract cookies. Defaults to None.

    Returns:
        list[dict]: dicts compatible with CookieJar.from_cookies():
        [{"name", "value", "domain", "path", "secure", "expiry"}, ...]
    """
    db = _find_firefox_db()
    rows = _query_cookies(db, domain)
    return [_row_to_dict(row) for row in rows]


def _firefox_profiles_root() -> Path:
    # explicit per-platform root. Avoid leaking `%APPDATA%` onto posix
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise FileNotFoundError("APPDATA is not set; cannot locate Firefox profiles.")
        return Path(appdata) / "Mozilla" / "Firefox" / "Profiles"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"

    # assume Linux/Unix
    return Path.home() / ".mozilla" / "firefox"


def _find_firefox_db() -> Path:
    root = _firefox_profiles_root()
    if not root.is_dir():
        raise FileNotFoundError(
            f"Firefox profiles directory not found at {root}. Is Firefox installed?"
        )

    # mtime heuristic: most recently used profile = the one logged into
    dbs = sorted(root.glob("*/cookies.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dbs:
        raise FileNotFoundError(f"No Firefox cookies.sqlite files found in {root}.")
    return dbs[0]


def _query_cookies(db: Path, domain: Optional[str]) -> list[tuple]:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "cookies.sqlite"
        shutil.copy(db, copy)
        conn = sqlite3.connect(copy)
        try:
            sql = "SELECT host, name, value, path, expiry, isSecure FROM moz_cookies"
            if domain is None:
                rows = conn.execute(sql).fetchall()
            else:
                # match both apex and dot-prefixed host forms
                rows = conn.execute(
                    sql + " WHERE host IN (?, ?)", (domain, "." + domain)
                ).fetchall()
            return rows
        finally:
            conn.close()


def _row_to_dict(row: tuple) -> dict:
    host, name, value, path, expiry, is_secure = row
    return {
        "name": name,
        "value": value,
        "domain": host,
        "path": path,
        "secure": bool(is_secure),
        "expiry": expiry if expiry else None,  # 0 / NULL session cookies -> None
    }
