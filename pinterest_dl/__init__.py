__version__ = "0.0.28"
__description__ = "An unofficial Pinterest image downloader"

from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from pinterest_dl import downloader, io, scraper, utils


class PinterestDL:
    """PinterestDL is a class for scraping, downloading, and managing images from Pinterest.

    Users can scrape pins, download images, add captions, and prune by resolution.

    Attributes:
        output_dir (Path): Directory to store downloaded images.
        verbose (bool): Enable verbose logging.
        timeout (float): Timeout in seconds for various operations.
        browser (Optional[WebDriver]): Selenium browser instance for scraping.
    """

    def __init__(
        self, output_dir: Union[str, Path], verbose: bool = False, timeout: float = 3
    ) -> None:
        """Initializes an instance of PinterestDL.

        Args:
            output_dir (Union[str, Path]): Directory to store downloaded images.
            verbose (bool): Enable verbose logging.
            timeout (float): Timeout in seconds for various operations.
        """
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.timeout = timeout
        self.browser: Optional[WebDriver] = None

    @classmethod
    def with_browser(
        cls,
        output_dir: Union[str, Path],
        browser_type: Literal["chrome", "firefox"],
        timout: float = 3,
        headless: bool = True,
        incognito: bool = False,
        verbose: bool = False,
    ) -> "PinterestDL":
        """Create an instance of PinterestDL with an initialized browser.

        Args:
            output_dir (Union[str, Path]): Directory to store downloaded images.
            browser_type (Literal["chrome", "firefox"]): Browser type to use ('chrome' or 'firefox').
            timout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.

        Returns:
            PinterestDL: Instance of PinterestDL with an initialized browser.
        """
        instance = cls(output_dir, verbose, timout)
        instance.browser = instance._initialize_browser(browser_type, headless, incognito)
        return instance

    def download_images(self, urls: List[str], fallback_urls: List[List[str]]) -> List[Path]:
        """Download images from Pinterest using given URLs and fallbacks.

        Args:
            urls (List[str]): URL(s) of images to download.
            fallback_urls (List[List[str]]): URL(s) of fallback images.

        Returns:
            List[Path]: List of paths to downloaded images.
        """
        return downloader.download_concurrent_with_fallback(
            urls, self.output_dir, verbose=self.verbose, fallback_urls=fallback_urls
        )

    def add_captions(
        self,
        files: List[Path],
        captions: List[Optional[str]],
        origins: List[Optional[str]],
        indices: List[int],
    ) -> None:
        """Add captions and origin information to downloaded images.

        Args:
            files (List[Path]): File(s) to add captions to.
            captions (List[Optional[str]]): Caption(s) to be added.
            origins (List[Optional[str]]): Origin URL(s) to be added.
            indices (List[int]): Specific indices to add captions for.
        """
        for index in indices or range(len(files)):
            try:
                file = files[index]
                caption = captions[index]
                origin = origins[index]
                if origin:
                    utils.write_img_comment(file, origin)
                    if self.verbose:
                        print(f"Origin added to {file}: '{origin}'")
                if caption:
                    utils.write_img_subject(file, caption)
                    if self.verbose:
                        print(f"Caption added to {file}: '{caption}'")

            except Exception as e:
                print(f"Error captioning {file}: {e}")

    def prune_images(self, images: List[Path], min_resolution: Tuple[int, int]) -> List[int]:
        """Prune images that do not meet minimum resolution requirements.

        Args:
            images (List[Path]): List of image paths to prune.
            min_resolution (Tuple[int, int]): Minimum resolution requirement (width, height).

        Returns:
            List[int]: List of indices of images that meet the resolution requirements.
        """
        valid_indices = []
        for index, img in tqdm(enumerate(images), desc="Pruning"):
            if utils.prune_by_resolution(img, min_resolution, verbose=self.verbose):
                continue
            valid_indices.append(index)

        pruned_count = len(images) - len(valid_indices)
        print(f"Pruned ({pruned_count}) images")

        if self.verbose:
            print("Pruned images index:", valid_indices)

        return valid_indices

    def scrape_pins(
        self,
        url: str,
        limit: int,
        min_resolution: Optional[Tuple[int, int]] = None,
        json_output: Optional[Union[str, Path]] = None,
        dry_run: bool = False,
        add_captions: bool = True,
    ) -> Optional[List[Path]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            limit (int): Maximum number of images to scrape.
            min_resolution (Optional[Tuple[int, int]]): Minimum resolution for pruning.
            json_output (Optional[Union[str, Path]]): Path to save scraped data as JSON.
            dry_run (bool): Only scrape URLs without downloading images.
            add_captions (bool): Add captions to downloaded images.

        Returns:
            Optional[List[Path]]: List of paths to downloaded images or None if dry_run is True.
        """
        if self.browser is None:
            raise RuntimeError(
                "Browser is not initialized. Use 'with_browser' to create an instance with a browser."
            )

        try:
            pin_scraper = scraper.Pinterest(self.browser)
            scraped_imgs = pin_scraper.scrape(
                url, limit=limit, verbose=self.verbose, timeout=self.timeout
            )

            imgs_dict = [img.to_dict() for img in scraped_imgs]

            if json_output:
                output_path = Path(json_output)
                io.write_json(imgs_dict, output_path, indent=4)

            if dry_run:
                if self.verbose:
                    print("Scraped data (dry run):", imgs_dict)
                return None

            srcs = [img.src for img in scraped_imgs]
            captions = [img.alt for img in scraped_imgs]
            origins = [img.origin for img in scraped_imgs]
            fallback_urls = [img.fallback_urls for img in scraped_imgs]

            downloaded_files = self.download_images(srcs, fallback_urls)
            valid_indices = self.prune_images(downloaded_files, min_resolution or (0, 0))

            if add_captions:
                self.add_captions(downloaded_files, captions, origins, valid_indices)

            return downloaded_files

        finally:
            self.browser.close()
            self.browser = None

    def _initialize_browser(
        self, browser_type: Literal["chrome", "firefox"], headless: bool, incognito: bool
    ) -> WebDriver:
        """Initialize a browser for scraping.

        Args:
            browser_type (Literal["chrome", "firefox"]): Type of browser ('chrome' or 'firefox').
            headless (bool): Run in headless mode.
            incognito (bool): Run in incognito mode.

        Returns:
            WebDriver: Browser instance.
        """
        if browser_type.lower() == "firefox":
            return scraper.Browser().Firefox(incognito=incognito, headful=not headless)
        elif browser_type.lower() == "chrome":
            return scraper.Browser().Chrome(
                exe_path=utils.get_appdata_dir("chromedriver.exe"),
                incognito=incognito,
                headful=not headless,
            )
        else:
            raise ValueError("Unsupported browser type. Choose 'chrome' or 'firefox'.")
