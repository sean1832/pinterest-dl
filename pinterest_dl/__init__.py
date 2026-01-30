"""Pinterest-DL: An unofficial Pinterest media downloader.

This package provides a simple API for scraping and downloading media from Pinterest.

Example:
    >>> from pinterest_dl import PinterestDL
    >>> scraper = PinterestDL.with_api()
    >>> media = scraper.scrape("https://pinterest.com/pin/123456/")
    >>> scraper.download(media, "output/")
"""

__version__ = "0.0.0.dev0"
__description__ = "An unofficial Pinterest image downloader"
__all__ = [
    "PinterestDL",
    "ApiScraper",
    "WebDriverScraper",
    "PinterestMedia",
    "__version__",
    "__description__",
]

from typing import Literal

from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.scrapers.api_scraper import ApiScraper
from pinterest_dl.scrapers.webdriver_scraper import WebDriverScraper


class PinterestDL:
    """Factory for creating Pinterest scrapers.

    PinterestDL provides two scraping strategies:
    - API-based: Fast, uses reverse-engineered Pinterest API
    - WebDriver-based: Slower but more reliable, uses Selenium
    """

    @staticmethod
    def with_api(
        timeout: float = 10, verbose: bool = False, ensure_alt: bool = False
    ) -> "ApiScraper":
        """Scrape pinterest using unofficial API. This is faster than but may be less reliable.

        Args:
            timeout (float): Timeout in seconds for requests.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.

        Returns:
            ApiScraper: Instance of ApiScraper with the requests library.
        """
        return ApiScraper(verbose=verbose, timeout=timeout, ensure_alt=ensure_alt)

    @staticmethod
    def with_browser(
        browser_type: Literal["chrome", "firefox"],
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> "WebDriverScraper":
        """Scrape Pinterest using a webdriver (Selenium). This is slower but more reliable.

        Args:
            browser_type (Literal["chrome", "firefox"]): Browser type to use ('chrome' or 'firefox').
            timeout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.

        Returns:
            WebDriverScraper: Instance of WebDriverScraper with an initialized browser.
        """
        webdriver = WebDriverScraper._initialize_webdriver(browser_type, headless, incognito)
        return WebDriverScraper(webdriver, timeout, verbose, ensure_alt=ensure_alt)
