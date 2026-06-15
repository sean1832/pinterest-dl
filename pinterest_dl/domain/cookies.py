from typing import List

import requests
import requests.cookies


class CookieJar(requests.cookies.RequestsCookieJar):
    """RequestsCookieJar with helpers for pinterest-dl's on-disk cookie format.

    Cookies are persisted as a list of dicts with the keys
    ``name``, ``value``, ``domain``, ``path``, ``secure`` and ``expiry``.
    """

    @staticmethod
    def from_cookies(cookies: List[dict]) -> "CookieJar":
        """Build a CookieJar from stored cookie dicts."""
        jar = CookieJar()
        for cookie in cookies:
            jar.set(
                name=cookie.get("name", ""),
                value=cookie.get("value", ""),
                domain=cookie.get("domain", None),
                path=cookie.get("path", "/"),
                secure=cookie.get("secure", False),
                expires=cookie.get("expiry"),
            )
        return jar

    @staticmethod
    def to_playwright(cookies: List[dict]) -> List[dict]:
        """Convert stored cookie dicts to Playwright's cookie format.

        Playwright uses ``expires`` (float) instead of the stored ``expiry`` (int)
        and expects ``httpOnly`` and ``sameSite`` fields.

        Args:
            cookies: List of stored cookie dictionaries.

        Returns:
            List of Playwright-format cookie dictionaries.
        """
        playwright_cookies = []
        for cookie in cookies:
            pw_cookie = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
                "httpOnly": cookie.get("httpOnly", False),
                "sameSite": cookie.get("sameSite", "Lax"),
            }
            if "expiry" in cookie and cookie["expiry"]:
                pw_cookie["expires"] = float(cookie["expiry"])
            playwright_cookies.append(pw_cookie)
        return playwright_cookies
