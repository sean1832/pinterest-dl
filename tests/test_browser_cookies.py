"""Tests for Firefox browser cookie extraction."""

import os
import sqlite3
from pathlib import Path

import pytest

from pinterest_dl.domain import browser_cookies


def _make_cookie_db(path: Path, rows: list[tuple]) -> None:
    """Write a minimal Firefox-style cookies.sqlite at path.

    Only the columns the extractor SELECTs are created; a real Firefox schema
    has more, but the query names columns explicitly so extras are irrelevant.
    Rows are (host, name, value, path, expiry, isSecure).
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE moz_cookies "
            "(host TEXT, name TEXT, value TEXT, path TEXT, expiry INTEGER, isSecure INTEGER)"
        )
        conn.executemany(
            "INSERT INTO moz_cookies (host, name, value, path, expiry, isSecure) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


class TestFindFirefoxDb:
    """Profile discovery and the mtime heuristic."""

    def test_missing_profile_dir(self, tmp_path, monkeypatch):
        """FileNotFoundError when the profiles root does not exist."""
        missing = tmp_path / "no-firefox-here"
        monkeypatch.setattr(browser_cookies, "_firefox_profiles_root", lambda: missing)

        with pytest.raises(FileNotFoundError, match="profiles directory not found"):
            browser_cookies._find_firefox_db()

    def test_no_db_in_profiles(self, tmp_path, monkeypatch):
        """FileNotFoundError when the root exists but holds no cookies.sqlite."""
        root = tmp_path / "Profiles"
        (root / "abc.default").mkdir(parents=True)
        monkeypatch.setattr(browser_cookies, "_firefox_profiles_root", lambda: root)

        with pytest.raises(FileNotFoundError, match="No Firefox cookies.sqlite"):
            browser_cookies._find_firefox_db()

    def test_picks_highest_mtime(self, tmp_path, monkeypatch):
        """Returns the cookies.sqlite from the most recently used profile."""
        root = tmp_path / "Profiles"
        old_db = root / "old.default" / "cookies.sqlite"
        new_db = root / "new.default" / "cookies.sqlite"
        old_db.parent.mkdir(parents=True)
        new_db.parent.mkdir(parents=True)
        old_db.touch()
        new_db.touch()
        # explicit mtimes so the assertion does not depend on creation order
        os.utime(old_db, (1000, 1000))
        os.utime(new_db, (2000, 2000))
        monkeypatch.setattr(browser_cookies, "_firefox_profiles_root", lambda: root)

        assert browser_cookies._find_firefox_db() == new_db


class TestQueryCookies:
    """SQL extraction against a real on-disk sqlite copy."""

    @pytest.fixture
    def db(self, tmp_path) -> Path:
        path = tmp_path / "cookies.sqlite"
        _make_cookie_db(
            path,
            [
                ("pinterest.com", "a", "1", "/", 111, 1),
                (".pinterest.com", "b", "2", "/", 222, 0),
                ("www.pinterest.com", "c", "3", "/", 333, 1),
                ("google.com", "d", "4", "/", 444, 1),
            ],
        )
        return path

    def test_no_filter_returns_all_rows(self, db):
        """domain=None returns every row in moz_cookies."""
        rows = browser_cookies._query_cookies(db, None)
        assert len(rows) == 4

    def test_domain_filter_matches_apex_and_dot(self, db):
        """A domain filter matches both 'domain' and '.domain' hosts."""
        rows = browser_cookies._query_cookies(db, "pinterest.com")
        hosts = {row[0] for row in rows}
        # 'www.pinterest.com' is deliberately excluded; only exact + dot-prefixed match
        assert hosts == {"pinterest.com", ".pinterest.com"}

    def test_domain_filter_excludes_others(self, db):
        """Unrelated domains are not returned."""
        rows = browser_cookies._query_cookies(db, "pinterest.com")
        assert all(row[0] != "google.com" for row in rows)


class TestRowToDict:
    """Row tuple to stored-cookie dict mapping."""

    def test_field_mapping(self):
        """host -> domain and column order map onto the expected keys."""
        row = (".pinterest.com", "_auth", "1", "/", 1735689600, 1)
        assert browser_cookies._row_to_dict(row) == {
            "name": "_auth",
            "value": "1",
            "domain": ".pinterest.com",
            "path": "/",
            "secure": True,
            "expiry": 1735689600,
        }

    def test_secure_coercion(self):
        """isSecure integer is coerced to bool."""
        assert browser_cookies._row_to_dict((".x.com", "n", "v", "/", 1, 0))["secure"] is False
        assert browser_cookies._row_to_dict((".x.com", "n", "v", "/", 1, 1))["secure"] is True

    def test_session_cookie_expiry_none(self):
        """expiry == 0 (session cookie) maps to None."""
        assert browser_cookies._row_to_dict((".x.com", "n", "v", "/", 0, 1))["expiry"] is None

    def test_null_expiry_none(self):
        """A NULL expiry also maps to None."""
        assert browser_cookies._row_to_dict((".x.com", "n", "v", "/", None, 1))["expiry"] is None


class TestLoadFirefoxCookies:
    """End-to-end pipeline with discovery stubbed at the db seam."""

    def test_full_pipeline_with_domain_filter(self, tmp_path, monkeypatch):
        path = tmp_path / "cookies.sqlite"
        _make_cookie_db(
            path,
            [
                (".pinterest.com", "_auth", "1", "/", 1735689600, 1),
                ("google.com", "SID", "x", "/", 1735689600, 1),
            ],
        )
        monkeypatch.setattr(browser_cookies, "_find_firefox_db", lambda: path)

        cookies = browser_cookies.load_firefox_cookies(domain="pinterest.com")

        assert cookies == [
            {
                "name": "_auth",
                "value": "1",
                "domain": ".pinterest.com",
                "path": "/",
                "secure": True,
                "expiry": 1735689600,
            }
        ]
