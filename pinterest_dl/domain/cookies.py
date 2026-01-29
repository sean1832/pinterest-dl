from typing import List

import requests
import requests.cookies


class PinterestCookieJar(requests.cookies.RequestsCookieJar):
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

    @staticmethod
    def from_selenium_cookies(cookies: List[dict]) -> "PinterestCookieJar":
        """Convert Selenium cookies to RequestsCookieJar"""
        jar = PinterestCookieJar()
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
