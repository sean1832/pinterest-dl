"""Pinterest-DL: An unofficial Pinterest media downloader.

This package provides a simple API for scraping and downloading media from Pinterest.

Example:
    >>> from pinterest_dl import PinterestDL
    >>> scraper = PinterestDL.with_api()
    >>> media = scraper.scrape("https://pinterest.com/pin/123456/")
    >>> scraper.download(media, "output/")
"""

import warnings

__version__ = "0.0.0.dev0"
__description__ = "An unofficial Pinterest image downloader"
__all__ = [
    "PinterestDL",
    "ApiScraper",
    "PlaywrightScraper",
    "WebDriverScraper",
    "PinterestMedia",
    "__version__",
    "__description__",
]

from typing import Literal

from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.scrapers.api_scraper import ApiScraper
from pinterest_dl.scrapers.playwright_scraper import PlaywrightScraper
from pinterest_dl.scrapers.webdriver_scraper import WebDriverScraper


class PinterestDL:
    """Factory for creating Pinterest scrapers.

    PinterestDL provides multiple scraping strategies:
    - API-based: Fast, uses reverse-engineered Pinterest API (default)
    - Playwright-based: Browser automation, stable and cross-platform (recommended for browser mode)
    - Selenium-based: Legacy browser automation (for backward compatibility)
    """

    @staticmethod
    def with_api(
        timeout: float = 10,
        verbose: bool = False,
        ensure_alt: bool = False,
        debug_mode: bool = False,
        debug_dir: str = "debug",
    ) -> "ApiScraper":
        """Scrape pinterest using unofficial API. This is faster than but may be less reliable.

        Args:
            timeout (float): Timeout in seconds for requests.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.
            debug_mode (bool): Enable debug mode to dump all requests and responses to JSON files.
            debug_dir (str): Directory to save debug files when debug_mode is enabled.

        Returns:
            ApiScraper: Instance of ApiScraper with the requests library.
        """
        return ApiScraper(
            verbose=verbose,
            timeout=timeout,
            ensure_alt=ensure_alt,
            debug_mode=debug_mode,
            debug_dir=debug_dir,
        )

    @staticmethod
    def with_browser(
        browser_type: Literal["chromium", "firefox"] = "chromium",
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
        ensure_alt: bool = False,
        enable_images: bool = True,
    ) -> "PlaywrightScraper":
        """Scrape Pinterest using Playwright browser automation.

        This is the recommended browser-based scraping method. Playwright provides
        better stability, automatic browser management, and cross-platform support
        (including headless servers like Alpine/Ubuntu).

        Args:
            browser_type: Browser to use ('chromium' or 'firefox').
            timeout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.
            enable_images (bool): Enable image loading (default: True for login, can disable for scraping).

        Returns:
            PlaywrightScraper: Instance of PlaywrightScraper with Playwright browser.

        Note:
            Requires `playwright install chromium` (or firefox) to be run first.
        """
        return PlaywrightScraper.create(
            browser_type=browser_type,
            timeout=timeout,
            headless=headless,
            incognito=incognito,
            verbose=verbose,
            ensure_alt=ensure_alt,
            enable_images=enable_images,
        )

    @staticmethod
    def with_selenium(
        browser_type: Literal["chrome", "firefox"] = "chrome",
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> "WebDriverScraper":
        """Scrape Pinterest using Selenium WebDriver (legacy).

        This method is provided for backward compatibility. For new projects,
        consider using `with_browser()` which uses Playwright instead.

        Args:
            browser_type: Browser type to use ('chrome' or 'firefox').
            timeout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.

        Returns:
            WebDriverScraper: Instance of WebDriverScraper with Selenium WebDriver.

        Note:
            Selenium requires separate driver installation (ChromeDriver/GeckoDriver).
            For easier setup, use `with_browser()` which uses Playwright.
        """
        warnings.warn(
            "with_selenium() uses Selenium which requires manual driver setup. "
            "Consider using with_browser() which uses Playwright for easier setup. "
            "Selenium support may be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        webdriver = WebDriverScraper._initialize_webdriver(browser_type, headless, incognito)
        return WebDriverScraper(webdriver, timeout, verbose, ensure_alt=ensure_alt)
