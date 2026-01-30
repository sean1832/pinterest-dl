from typing import List

import requests
import requests.cookies


class CookieJar(requests.cookies.RequestsCookieJar):
    def to_selenium_cookies(self) -> List[dict]:
        """Convert each cookie in the RequestsCookieJar to Selenium format"""
        pinterest_cookies = []
        for cookie in self:
            pinterest_cookie = {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expiry": cookie.expires,
                "secure": cookie.secure,
            }
            pinterest_cookies.append(pinterest_cookie)
        return pinterest_cookies

    def to_playwright_cookies(self) -> List[dict]:
        """Convert each cookie in the RequestsCookieJar to Playwright format.

        Playwright uses 'expires' (float) instead of Selenium's 'expiry' (int),
        and includes additional fields like 'httpOnly' and 'sameSite'.
        """
        playwright_cookies = []
        for cookie in self:
            pw_cookie = {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "httpOnly": getattr(cookie, "httpOnly", False),
                "sameSite": "Lax",  # Default to Lax for compatibility
            }
            # Playwright uses 'expires' as float, Selenium uses 'expiry' as int
            if cookie.expires:
                pw_cookie["expires"] = float(cookie.expires)
            playwright_cookies.append(pw_cookie)
        return playwright_cookies

    @staticmethod
    def from_selenium_cookies(cookies: List[dict]) -> "CookieJar":
        """Convert Selenium cookies to RequestsCookieJar"""
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
    def from_playwright_cookies(cookies: List[dict]) -> "CookieJar":
        """Convert Playwright cookies to RequestsCookieJar.

        Args:
            cookies: List of Playwright cookie dictionaries.

        Returns:
            CookieJar populated with the provided cookies.
        """
        jar = CookieJar()
        for cookie in cookies:
            # Playwright uses 'expires' (float), convert to int for RequestsCookieJar
            expires = cookie.get("expires")
            if expires is not None:
                expires = int(expires)
            jar.set(
                name=cookie.get("name", ""),
                value=cookie.get("value", ""),
                domain=cookie.get("domain", None),
                path=cookie.get("path", "/"),
                secure=cookie.get("secure", False),
                expires=expires,
            )
        return jar

    @staticmethod
    def selenium_to_playwright(cookies: List[dict]) -> List[dict]:
        """Convert Selenium cookie format to Playwright format.

        This is useful when loading existing Selenium-format cookie files
        with Playwright.

        Args:
            cookies: List of Selenium-format cookie dictionaries.

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
            # Convert 'expiry' (Selenium) to 'expires' (Playwright)
            if "expiry" in cookie and cookie["expiry"]:
                pw_cookie["expires"] = float(cookie["expiry"])
            playwright_cookies.append(pw_cookie)
        return playwright_cookies

    @staticmethod
    def playwright_to_selenium(cookies: List[dict]) -> List[dict]:
        """Convert Playwright cookie format to Selenium format.

        Args:
            cookies: List of Playwright-format cookie dictionaries.

        Returns:
            List of Selenium-format cookie dictionaries.
        """
        selenium_cookies = []
        for cookie in cookies:
            sel_cookie = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
            }
            # Convert 'expires' (Playwright) to 'expiry' (Selenium)
            if "expires" in cookie and cookie["expires"]:
                sel_cookie["expiry"] = int(cookie["expires"])
            selenium_cookies.append(sel_cookie)
        return selenium_cookies


# # ==============================================
# # Example usage [Requests -> Selenium]:
# # ==============================================

# # Step 1: Use the custom cookie jar to make a request and store cookies
# session = requests.Session()
# session.cookies = PinterestCookieJar()  # Use the custom cookie jar
# response = session.get("https://example.com")

# # Step 2: Get cookies in Selenium format
# selenium_cookies = session.cookies.to_selenium_cookies()

# # Step 3: Use Selenium and add cookies
# driver = webdriver.Chrome()
# driver.get("https://example.com")
# for cookie in selenium_cookies:
#     driver.add_cookie(cookie)

# # Step 4: Refresh or navigate as needed
# driver.refresh()


# # ==============================================
# # Example usage [Selenium -> Requests]:
# # ==============================================

# # Step 1: Use Selenium to navigate and collect cookies
# driver = webdriver.Chrome()
# driver.get("https://example.com")

# # Step 2: Get cookies from Selenium and convert to RequestsCookieJar
# selenium_cookies = driver.get_cookies()
# cookie_jar = PinterestCookieJar.from_selenium_cookies(selenium_cookies)

# # Step 3: Use the Requests session with the transferred cookies
# session = requests.Session()
# session.cookies.update(cookie_jar)

# # Now `session` contains the cookies from Selenium
# response = session.get("https://example.com")
# print(response.text)
