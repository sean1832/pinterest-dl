__version__ = "0.0.0.dev0"
__description__ = "An unofficial Pinterest image downloader"

from typing import Literal

from pinterest_dl.scrapers import _ScraperAPI, _ScraperWebdriver


class PinterestDL:
    """Factory for creating Pinterest scrapers.

    PinterestDL provides two scraping strategies:
    - API-based: Fast, uses reverse-engineered Pinterest API
    - WebDriver-based: Slower but more reliable, uses Selenium
    """

    @staticmethod
    def with_api(
        timeout: float = 10, verbose: bool = False, ensure_alt: bool = False
    ) -> "_ScraperAPI":
        """Scrape pinterest using unofficial API. This is faster than but may be less reliable.

        Args:
            timeout (float): Timeout in seconds for requests.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.

        Returns:
            PinterestDL: Instance of PinterestDL with the requests library.
        """
        return _ScraperAPI(verbose=verbose, timeout=timeout, ensure_alt=ensure_alt)

    @staticmethod
    def with_browser(
        browser_type: Literal["chrome", "firefox"],
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> "_ScraperWebdriver":
        """Scrape Pinterest using a webdriver (Selenium). This is slower but more reliable.

        Args:
            browser_type (Literal["chrome", "firefox"]): Browser type to use ('chrome' or 'firefox').
            timeout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.

        Returns:
            PinterestDL: Instance of PinterestDL with an initialized browser.
        """
        webdriver = _ScraperWebdriver._initialize_webdriver(browser_type, headless, incognito)
        return _ScraperWebdriver(webdriver, timeout, verbose, ensure_alt=ensure_alt)
