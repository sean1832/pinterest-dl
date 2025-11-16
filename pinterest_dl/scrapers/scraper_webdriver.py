import json
import logging
import time
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Union

from selenium.webdriver.remote.webdriver import WebDriver

from pinterest_dl.low_level.webdriver.browser import Browser
from pinterest_dl.low_level.webdriver.pinterest_driver import PinterestDriver, PinterestMedia
from pinterest_dl.utils import io

from .scraper_base import _ScraperBase

logger = logging.getLogger(__name__)


class _ScraperWebdriver(_ScraperBase):
    def __init__(
        self,
        webdriver: WebDriver,
        timeout: float = 3,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> None:
        self.timeout = timeout
        self.verbose = verbose
        self.webdriver: WebDriver = webdriver
        self.ensure_alt = ensure_alt

    def with_cookies(
        self, cookies: list[dict[str, Any]], wait_sec: float = 1
    ) -> "_ScraperWebdriver":
        """Load cookies to the current browser session.

        Args:
            cookies (list[dict]): List of cookies to load.
            wait_sec (float): Time in seconds to wait after loading cookies.

        Returns:
            _ScraperWebdriver: Instance of ScraperWebdriver with cookies loaded.
        """
        if isinstance(cookies, str) or isinstance(cookies, Path):
            raise ValueError(
                "Invalid cookies format. Expected a list of dictionary. In Selenium format."
                + "If you want to load cookies from a file, use `with_cookies_path` method instead."
            )
        if not isinstance(cookies, list):
            raise ValueError(
                "Invalid cookies format. Expected a list of dictionary. In Selenium format."
            )
        cookies = self._sanitize_cookies(cookies)
        for cookie in cookies:
            self.webdriver.add_cookie(cookie)
        time.sleep(wait_sec)
        return self

    def with_cookies_path(
        self, cookies_path: Optional[Union[str, Path]], wait_sec: float = 1
    ) -> "_ScraperWebdriver":
        """Load cookies from a file to the current browser session.

        Args:
            cookies_path (Optional[Union[str, Path]]): Path to cookies file.
            wait_sec (float): Time in seconds to wait after loading cookies.

        Returns:
            _ScraperWebdriver: Instance of ScraperWebdriver with cookies loaded.
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

        # Navigate to Pinterest homepage to load cookies
        # Selenium requires the page to be loaded before adding cookies
        self.webdriver.get("https://www.pinterest.com")

        cookies = self._sanitize_cookies(cookies)
        for cookie in cookies:
            self.webdriver.add_cookie(cookie)
        print(f"Loaded cookies from {cookies_path}")

        time.sleep(wait_sec)
        return self

    def scrape(self, url: str, num: int) -> List[PinterestMedia]:
        """Scrape pins from Pinterest using a WebDriver.

        Args:
            url (str): Pinterest URL to scrape.
            num (int): Maximum number of images to scrape.

        Returns:
            List[PinterestMedia]: List of scraped PinterestMedia objects.
        """
        try:
            pin_scraper = PinterestDriver(self.webdriver)
            return pin_scraper.scrape(
                url, num=num, verbose=self.verbose, timeout=self.timeout, ensure_alt=self.ensure_alt
            )
        finally:
            self.webdriver.close()

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
            url (str): Pinterest URL to scrape.
            output_dir (Union[str, Path]): Directory to store downloaded images. 'None' print to console.
            num (int): Maximum number of images to scrape.
            min_resolution (Optional[Tuple[int, int]]): Minimum resolution for pruning.
            cache_path (Optional[Union[str, Path]]): Path to cache scraped data as json
            caption (Literal["txt", "json", "metadata", "none"]): Caption mode for downloaded images.
                'txt' for alt text in separate files,
                'json' for full image data,
                'metadata' embeds in image files,
                'none' skips captions
        Returns:
            Optional[List[PinterestMedia]]: List of downloaded PinterestMedia objects.
        """
        min_resolution = min_resolution or (0, 0)
        scraped_imgs = self.scrape(url, num)

        imgs_dict = [img.to_dict() for img in scraped_imgs]

        if not output_dir:
            # no output_dir provided, print the scraped image data to console
            print("Scraped: ")
            print(json.dumps(imgs_dict, indent=2))

        if cache_path:
            output_path = Path(cache_path)
            io.write_json(imgs_dict, output_path, indent=4)
            print(f"Scraped data cached to {output_path}")

        if not output_dir:
            return None

        downloaded_imgs = self.download_media(scraped_imgs, output_dir, False)

        kept_imgs = self.prune_images(downloaded_imgs, min_resolution or (0, 0), self.verbose)

        if caption == "txt" or caption == "json":
            self.add_captions_to_file(kept_imgs, output_dir, caption, self.verbose)
        elif caption == "metadata":
            self.add_captions_to_meta(kept_imgs, self.verbose)
        elif caption != "none":
            raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")

        return kept_imgs

    def login(self, email: str, password: str) -> PinterestDriver:
        """Login to Pinterest using the given credentials.

        Args:
            email (str): Pinterest email.
            password (str): Pinterest password.

        Returns:
            Pinterest: Pinterest object.
        """
        try:
            return PinterestDriver(self.webdriver).login(email, password)
        except Exception as e:
            raise RuntimeError(f"Failed to login to Pinterest: {e}") from e

    @staticmethod
    def _sanitize_cookies(cookies: List[dict]) -> List[dict]:
        """Clean cookies to ensure they are compatible with Pinterest.

        Args:
            cookies (List[dict]): List of cookies to clean.

        Returns:
            List[dict]: Cleaned list of cookies.
        """
        for cookie in cookies:
            if cookie.get("domain") != ".pinterest.com":
                cookie["domain"] = ".pinterest.com"
        return cookies

    @staticmethod
    def _initialize_webdriver(
        browser_type: Literal["chrome", "firefox"], headless: bool, incognito: bool
    ) -> WebDriver:
        if browser_type.lower() == "firefox":
            return Browser().Firefox(incognito=incognito, headful=not headless)
        elif browser_type.lower() == "chrome":
            return Browser().Chrome(
                exe_path=io.get_appdata_dir("chromedriver.exe"),
                incognito=incognito,
                headful=not headless,
            )
        else:
            raise ValueError("Unsupported browser type. Choose 'chrome' or 'firefox'.")
