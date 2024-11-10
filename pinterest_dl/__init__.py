__version__ = "0.0.28"
__description__ = "An unofficial Pinterest image downloader"

from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from pinterest_dl import downloader, io, scraper, utils


class PinterestDL:
    """
    PinterestDL is a class for scraping, downloading, and managing images from Pinterest.
    Users can scrape pins, download images, add captions, and prune by resolution.

    Args:
        output_dir (str | Path): Directory to store downloaded images.
        verbose (bool): Enable verbose logging.
    """

    def __init__(self, output_dir: Union[str, Path], verbose: bool = False, timeout: float = 3):
        """
        Initializes PinterestDL.

        Args:
            output_dir (str | Path): Directory to store downloaded images.
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
    ):
        """
        Create an instance of PinterestDL with an initialized browser.

        Args:
            output_dir (str | Path): Directory to store downloaded images.
            browser_type (Literal): Browser type to use ('chrome' or 'firefox').
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.

        Returns:
            PinterestDL: Instance of PinterestDL with an initialized browser.

        Example:
            ```python
            pdl = PinterestDL.with_browser(
                "output",
                browser_type="firefox",
                headless=True,
                incognito=False,
                verbose=True,
            )
            pdl.scrape_pins(...)
            ```
        """
        instance = cls(output_dir, verbose, timout)
        instance.browser = instance._initialize_browser(browser_type, headless, incognito)
        return instance

    def download_images(
        self, urls: Union[str, List[str]], fallback_urls: Union[str, List[str]]
    ) -> List[Path]:
        """
        Download images from Pinterest.

        Args:
            urls (str | List[str]): URL(s) of images to download.
            fallback_urls (str | List[str]): URL(s) of fallback images.

        Returns:
            List[Path]: List of paths to downloaded images.
        """
        if isinstance(urls, str):
            return [downloader.download_with_fallback(urls, self.output_dir, fallback_urls[0])]
        return downloader.download_concurrent(urls, self.output_dir, verbose=self.verbose)

    def add_captions(
        self,
        files: Union[Path, List[Path]],
        captions: Union[str, List[str]],
        origins: Union[str, List[str]],
        indices: Optional[Union[int, List[int]]] = None,
    ) -> None:
        """
        Add captions and origin information to downloaded images.

        Args:
            files (str | List[str | Path]): File(s) to add captions to.
            captions (str | List[str]): Caption(s) to be added.
            origins (str | List[str]): Origin URL(s) to be added.
            indices (int | List[int], optional): Specific indices to add captions for.
        """
        if isinstance(files, Path):
            files = [files]
        if isinstance(captions, str):
            captions = [captions]
        if isinstance(origins, str):
            origins = [origins]
        if isinstance(indices, int):
            indices = [indices]

        for index in indices or range(len(files)):
            try:
                file = files[index]
                caption = captions[index]
                origin = origins[index]
                utils.write_img_comment(file, origin)
                utils.write_img_subject(file, caption)

                if self.verbose:
                    print(f"Caption added to {file}: '{caption}'")
            except Exception as e:
                print(f"Error captioning {file}: {e}")

    def prune_images(self, images: List[Path], min_resolution: Tuple[int, int]) -> List[int]:
        """
        Prune images that do not meet minimum resolution requirements.

        Args:
            images (List[str | Path]): List of image paths to prune.
            min_resolution (Tuple[int, int]): Minimum resolution requirement (width, height).

        Returns:
            List[int]: List of indices of images that meet the resolution requirements.
        """
        valid_indices = []
        for index, img in tqdm(enumerate(images), desc="Pruning"):
            if utils.prune_by_resolution(img, min_resolution, verbose=self.verbose):
                valid_indices.append(index)

        if self.verbose:
            pruned_count = len(images) - len(valid_indices)
            print(f"Pruned {pruned_count} images that didn't meet resolution requirements.")

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
        """
        Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            limit (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int], optional): Minimum resolution for pruning.
            json_output (str | Path, optional): Path to save scraped data as JSON.
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
            scraped_data = pin_scraper.scrape(
                url, limit=limit, verbose=self.verbose, timeout=self.timeout
            )

            if json_output:
                output_path = Path(json_output)
                io.write_json(scraped_data, output_path, indent=4)

            if dry_run:
                if self.verbose:
                    print("Scraped data (dry run):", scraped_data)
                return None

            srcs = [img["src"] for img in scraped_data]
            captions = [img["alt"] for img in scraped_data]
            origins = [img["origin"] for img in scraped_data]
            fallback_urls = [img["fallback"] for img in scraped_data]

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
        """
        Initialize a browser for scraping.

        Args:
            browser_type (Literal): Type of browser ('chrome' or 'firefox').
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
