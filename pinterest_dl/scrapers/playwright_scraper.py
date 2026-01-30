"""Playwright-based Pinterest scraper.

This module provides the PlaywrightScraper class which uses Playwright
for browser automation, offering better stability and cross-platform
compatibility compared to Selenium.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Union

from playwright.sync_api import Page

from pinterest_dl.common import io
from pinterest_dl.domain.cookies import CookieJar
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.webdriver.playwright_browser import PlaywrightBrowser
from pinterest_dl.webdriver.playwright_driver import PlaywrightDriver

from . import operations

logger = logging.getLogger(__name__)


class PlaywrightScraper:
    """Pinterest scraper using Playwright browser automation.

    This scraper provides better stability and cross-platform compatibility
    compared to the Selenium-based WebDriverScraper. Playwright handles
    browser binaries automatically via `playwright install`.

    Example:
        >>> scraper = PlaywrightScraper.create(browser_type="chromium", headless=True)
        >>> media = scraper.scrape("https://pinterest.com/user/board/", num=50)
        >>> scraper.close()
    """

    def __init__(
        self,
        browser: PlaywrightBrowser,
        page: Page,
        timeout: float = 3,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> None:
        """Initialize scraper with Playwright browser and page.

        Args:
            browser: PlaywrightBrowser instance managing the browser lifecycle.
            page: Playwright Page object for interactions.
            timeout: Timeout in seconds for scraping operations.
            verbose: Enable verbose logging.
            ensure_alt: Only include images that have alt text.
        """
        self.browser = browser
        self.page = page
        self.timeout = timeout
        self.verbose = verbose
        self.ensure_alt = ensure_alt

    @classmethod
    def create(
        cls,
        browser_type: Literal["chromium", "firefox"] = "chromium",
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
        ensure_alt: bool = False,
        enable_images: bool = False,
    ) -> "PlaywrightScraper":
        """Factory method to create a PlaywrightScraper with initialized browser.

        Args:
            browser_type: Browser to use ('chromium' or 'firefox').
            timeout: Timeout in seconds for scraping operations.
            headless: Run browser in headless mode.
            incognito: Use incognito/private browsing mode.
            verbose: Enable verbose logging.
            ensure_alt: Only include images that have alt text.
            enable_images: Enable image loading (needed for login, disabled for performance).

        Returns:
            PlaywrightScraper instance ready for use.
        """
        browser = PlaywrightBrowser()
        browser.launch(
            browser_type=browser_type,
            headless=headless,
            incognito=incognito,
            image_enable=enable_images,  # Control image loading
        )
        return cls(
            browser=browser,
            page=browser.page,
            timeout=timeout,
            verbose=verbose,
            ensure_alt=ensure_alt,
        )

    def with_cookies(
        self, cookies: List[dict[str, Any]], wait_sec: float = 1
    ) -> "PlaywrightScraper":
        """Load cookies to the current browser context.

        Args:
            cookies: List of cookies in Selenium format (will be converted).
            wait_sec: Time in seconds to wait after loading cookies.

        Returns:
            PlaywrightScraper: Self for method chaining.
        """
        if isinstance(cookies, (str, Path)):
            raise ValueError(
                "Invalid cookies format. Expected a list of dictionaries. "
                "If you want to load cookies from a file, use `with_cookies_path` method."
            )
        if not isinstance(cookies, list):
            raise ValueError("Invalid cookies format. Expected a list of dictionaries.")

        # Sanitize and convert cookies
        cookies = self._sanitize_cookies(cookies)
        pw_cookies = CookieJar.selenium_to_playwright(cookies)

        # Add cookies to context (type: ignore for Playwright's strict typing)
        self.browser.context.add_cookies(pw_cookies)  # type: ignore[arg-type]
        time.sleep(wait_sec)
        return self

    def with_cookies_path(
        self, cookies_path: Optional[Union[str, Path]], wait_sec: float = 1
    ) -> "PlaywrightScraper":
        """Load cookies from a file to the current browser context.

        Args:
            cookies_path: Path to cookies file (Selenium format JSON).
            wait_sec: Time in seconds to wait after loading cookies.

        Returns:
            PlaywrightScraper: Self for method chaining.
        """
        if cookies_path is None:
            return self

        if not Path(cookies_path).exists():
            raise FileNotFoundError(f"Cookies file not found: {cookies_path}")

        cookies = io.read_json(cookies_path)
        if not isinstance(cookies, list):
            raise ValueError("Invalid cookies file format. Expected a list of cookies.")

        if self.verbose:
            print("Navigate to Pinterest homepage before loading cookies.")

        # Navigate to Pinterest first (required before adding cookies)
        self.page.goto("https://www.pinterest.com")
        self.page.wait_for_load_state("networkidle")

        # Sanitize and convert cookies
        cookies = self._sanitize_cookies(cookies)
        pw_cookies = CookieJar.selenium_to_playwright(cookies)

        # Add cookies to context (type: ignore for Playwright's strict typing)
        self.browser.context.add_cookies(pw_cookies)  # type: ignore[arg-type]
        print(f"Loaded cookies from {cookies_path}")

        time.sleep(wait_sec)
        return self

    def scrape(self, url: str, num: int) -> List[PinterestMedia]:
        """Scrape pins from Pinterest.

        Args:
            url: Pinterest URL to scrape (board, search, or pin URL).
            num: Maximum number of images to scrape.

        Returns:
            List of PinterestMedia objects with scraped data.
        """
        driver = PlaywrightDriver(self.page)
        return driver.scrape(
            url,
            num=num,
            verbose=self.verbose,
            timeout=self.timeout,
            ensure_alt=self.ensure_alt,
        )

    def scrape_and_download(
        self,
        url: str,
        output_dir: Optional[Union[str, Path]],
        num: int,
        min_resolution: Optional[Tuple[int, int]] = None,
        cache_path: Optional[Union[str, Path]] = None,
        caption: Literal["txt", "json", "metadata", "none"] = "none",
    ) -> Optional[List[PinterestMedia]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url: Pinterest URL to scrape.
            output_dir: Directory to store downloaded images. None prints to console.
            num: Maximum number of images to scrape.
            min_resolution: Minimum resolution for pruning (width, height).
            cache_path: Path to cache scraped data as JSON.
            caption: Caption mode for downloaded images.

        Returns:
            List of downloaded PinterestMedia objects, or None if no output_dir.
        """
        min_resolution = min_resolution or (0, 0)
        scraped_imgs = self.scrape(url, num)

        imgs_dict = [img.to_dict() for img in scraped_imgs]

        if not output_dir:
            print("Scraped: ")
            print(json.dumps(imgs_dict, indent=2))

        if cache_path:
            output_path = Path(cache_path)
            io.write_json(imgs_dict, output_path, indent=4)
            print(f"Scraped data cached to {output_path}")

        if not output_dir:
            return None

        downloaded_imgs = operations.download_media(scraped_imgs, output_dir, False)
        kept_imgs = operations.prune_images(downloaded_imgs, min_resolution, self.verbose)

        if caption == "txt" or caption == "json":
            operations.add_captions_to_file(kept_imgs, output_dir, caption, self.verbose)
        elif caption == "metadata":
            operations.add_captions_to_meta(kept_imgs, self.verbose)
        elif caption != "none":
            raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")

        return kept_imgs

    def login(self, email: str, password: str) -> PlaywrightDriver:
        """Login to Pinterest using the given credentials.

        Args:
            email: Pinterest email.
            password: Pinterest password.

        Returns:
            PlaywrightDriver for further operations (e.g., get_cookies).
        """
        try:
            return PlaywrightDriver(self.page).login(email, password)
        except Exception as e:
            raise RuntimeError(f"Failed to login to Pinterest: {e}") from e

    def close(self) -> None:
        """Close browser and cleanup resources."""
        self.browser.close()

    @staticmethod
    def _sanitize_cookies(cookies: List[dict]) -> List[dict]:
        """Clean cookies to ensure they are compatible with Pinterest.

        Args:
            cookies: List of cookies to clean.

        Returns:
            Cleaned list of cookies with Pinterest domain.
        """
        for cookie in cookies:
            if cookie.get("domain") != ".pinterest.com":
                cookie["domain"] = ".pinterest.com"
        return cookies

    def __enter__(self) -> "PlaywrightScraper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
