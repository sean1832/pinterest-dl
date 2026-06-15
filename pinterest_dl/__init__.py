"""Pinterest-DL: An unofficial Pinterest media downloader.

This package provides a simple API for scraping and downloading media from Pinterest.

Example:
    >>> from pinterest_dl import PinterestDL
    >>> scraper = PinterestDL.with_api()
    >>> media = scraper.scrape("https://pinterest.com/user/board/", num=10)
    >>> scraper.download(media, "output/")
"""

import logging
from typing import TYPE_CHECKING, Literal, Optional

__version__ = "0.0.0.dev0"
__description__ = "An unofficial Pinterest image downloader"
__all__ = [
    "PinterestDL",
    "ApiScraper",
    "PlaywrightScraper",
    "PinterestMedia",
    "__version__",
    "__description__",
]

from pinterest_dl.common.ensure_playwright import ensure_playwright
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.exceptions import BrowserDependencyError
from pinterest_dl.scrapers.api_scraper import ApiScraper

if TYPE_CHECKING:
    # Playwright is an optional dependency; import only for type checking so that
    # `import pinterest_dl` stays usable without it installed.
    from pinterest_dl.scrapers.playwright_scraper import PlaywrightScraper

logger = logging.getLogger(__name__)


def __getattr__(name: str) -> object:
    # PEP 562: lazily expose PlaywrightScraper so the API path never imports
    # playwright. Raises BrowserDependencyError with install guidance if missing.
    if name == "PlaywrightScraper":
        ensure_playwright()
        from pinterest_dl.scrapers.playwright_scraper import PlaywrightScraper

        return PlaywrightScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class PinterestDL:
    """Factory for creating Pinterest scrapers.

    PinterestDL provides multiple scraping strategies:
    - API-based: Fast, uses reverse-engineered Pinterest API (default)
    - Playwright-based: Browser automation, stable and cross-platform (recommended for browser mode)
    """

    @staticmethod
    def with_api(
        timeout: float = 10,
        verbose: bool = False,
        ensure_alt: bool = False,
        dump: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> "ApiScraper":
        """Scrape pinterest using unofficial API. This is faster than but may be less reliable.

        Args:
            timeout (float): Timeout in seconds for requests.
            verbose (bool): Enable verbose logging.
            ensure_alt (bool): Ensure that alt text is included in the scraped data.
            dump (Optional[str]): Directory to dump API requests/responses. None to disable (default).
            max_retries (int): Maximum number of retry attempts for failed API calls. Defaults to 3.
            retry_delay (float): Initial delay between retries in seconds (uses exponential backoff). Defaults to 1.0.

        Returns:
            ApiScraper: Instance of ApiScraper with the requests library.
        """
        return ApiScraper(
            verbose=verbose,
            timeout=timeout,
            ensure_alt=ensure_alt,
            dump=dump,
            max_retries=max_retries,
            retry_delay=retry_delay,
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
            Requires the optional `browser` extra (`pip install pinterest-dl[browser]`)
            and `playwright install chromium` (or firefox) to be run first.

        Raises:
            BrowserDependencyError: If the optional `playwright` dependency is missing.
        """
        try:
            ensure_playwright()
        except BrowserDependencyError as e:
            logger.error("%s", e)
            raise

        from pinterest_dl.scrapers.playwright_scraper import PlaywrightScraper

        return PlaywrightScraper.create(
            browser_type=browser_type,
            timeout=timeout,
            headless=headless,
            incognito=incognito,
            verbose=verbose,
            ensure_alt=ensure_alt,
            enable_images=enable_images,
        )
