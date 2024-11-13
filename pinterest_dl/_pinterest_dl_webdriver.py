import time
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from selenium.webdriver.remote.webdriver import WebDriver

import pinterest_dl.utils as utils
from pinterest_dl.low_level.ops import io
from pinterest_dl.low_level.webdriver.browser import Browser
from pinterest_dl.low_level.webdriver.pinterest_driver import PinterestDriver, PinterestImage


class _PinterestDLWebdriver:
    def __init__(self, webdriver: WebDriver, timeout: float = 3, verbose: bool = False) -> None:
        self.timeout = timeout
        self.verbose = verbose
        self.webdriver: WebDriver = webdriver

    def with_cookies(
        self, cookies_path: Optional[Union[str, Path]], wait_sec: float = 1
    ) -> "_PinterestDLWebdriver":
        """Load cookies from a file to the current browser session.

        Args:
            cookies_path (Optional[Union[str, Path]]): Path to cookies file.
            wait_sec (float): Time in seconds to wait after loading cookies.

        Returns:
            PinterestDL: Instance of PinterestDL with cookies loaded.
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

        # TODO: redundant get cookies if provided
        # Navigate to Pinterest homepage to load cookies
        self.webdriver.get("https://www.pinterest.com")

        cookies = _PinterestDLWebdriver._sanitize_cookies(cookies)
        for cookie in cookies:
            self.webdriver.add_cookie(cookie)
        print(f"Loaded cookies from {cookies_path}")

        time.sleep(wait_sec)
        return self

    def scrape(self, url: str, limit: int) -> List[PinterestImage]:
        """Scrape pins from Pinterest using a WebDriver.

        Args:
            url (str): Pinterest URL to scrape.
            limit (int): Maximum number of images to scrape.

        Returns:
            List[PinterestImage]: List of scraped PinterestImage objects.
        """
        try:
            pin_scraper = PinterestDriver(self.webdriver)
            return pin_scraper.scrape(url, limit=limit, verbose=self.verbose, timeout=self.timeout)
        finally:
            self.webdriver.close()

    def scrape_and_download(
        self,
        url: str,
        output_dir: Union[str, Path],
        limit: int,
        min_resolution: Optional[Tuple[int, int]] = None,
        json_output: Optional[Union[str, Path]] = None,
        dry_run: bool = False,
        add_captions: bool = False,
    ) -> Optional[List[PinterestImage]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Union[str, Path]): Directory to store downloaded images.
            limit (int): Maximum number of images to scrape.
            min_resolution (Optional[Tuple[int, int]]): Minimum resolution for pruning.
            json_output (Optional[Union[str, Path]]): Path to save scraped data as JSON.
            dry_run (bool): Only scrape URLs without downloading images.
            add_captions (bool): Add captions to downloaded images.

        Returns:
            Optional[List[PinterestImage]]: List of downloaded PinterestImage objects.
        """
        min_resolution = min_resolution or (0, 0)
        scraped_imgs = self.scrape(url, limit)

        if json_output:
            output_path = Path(json_output)
            imgs_dict = [img.to_dict() for img in scraped_imgs]
            io.write_json(imgs_dict, output_path, indent=4)

        if dry_run:
            if self.verbose:
                print("Scraped data (dry run):", imgs_dict)
            return None

        downloaded_imgs = utils.download_images(scraped_imgs, output_dir, self.verbose)

        valid_indices = utils.prune_images(downloaded_imgs, min_resolution or (0, 0), self.verbose)

        if add_captions:
            utils.add_captions(downloaded_imgs, valid_indices, self.verbose)

        return downloaded_imgs

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
            raise RuntimeError("Failed to login to Pinterest.") from e

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
