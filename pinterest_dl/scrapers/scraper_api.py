import time
from pathlib import Path
from typing import List, Optional, Tuple, Union, Any

from tqdm import tqdm

from pinterest_dl.data_model.cookie import PinterestCookieJar
from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.api.pinterest_api import PinterestAPI
from pinterest_dl.low_level.ops import io
from pinterest_dl.low_level.ops.bookmark_manager import BookmarkManager
from pinterest_dl.low_level.ops.request_builder import RequestBuilder

from .scraper_base import _ScraperBase


class _ScraperAPI(_ScraperBase):
    """Pinterest scraper using the unofficial Pinterest API."""

    def __init__(self, timeout: float = 5, verbose: bool = False) -> None:
        """Initialize PinterestDL with API.

        Args:
            timeout (float, optional): timeout in seconds. Defaults to 3.
            verbose (bool, optional): show detail messages. Defaults to False.
        """
        self.timeout = timeout
        self.verbose = verbose
        self.cookies = None

    def with_cookies(self, cookies:list[dict[str, Any]]) -> "_ScraperAPI":
        """Load cookies to the current session.

        Args:
            cookies (list[dict]): List of cookies in Selenium format.

        Returns:
            _ScraperAPI: Instance of ScraperAPI with cookies loaded.
        """
        if isinstance(cookies, str) or isinstance(cookies, Path):
            raise ValueError("Invalid cookies format. Expected a list of dictionary. In Selenium format."+
                             "If you want to load cookies from a file, use `with_cookies_path` method instead.")
        if not isinstance(cookies, list):
            raise ValueError("Invalid cookies format. Expected a list of dictionary. In Selenium format.")
        self.cookies = PinterestCookieJar().from_selenium_cookies(cookies)
        return self

    def with_cookies_path(self, cookies_path: Optional[Union[str, Path]]) -> "_ScraperAPI":
        """Load cookies from a file to the current session.

        Args:
            cookies_path (Optional[Union[str, Path]]): Path to cookies file.

        Returns:
            _ScraperAPI: Instance of ScraperAPI with cookies loaded.
        """
        if cookies_path is None:
            return self

        if not Path(cookies_path).exists():
            raise FileNotFoundError(f"Cookies file not found: {cookies_path}")

        cookies = io.read_json(cookies_path)
        if not isinstance(cookies, list):
            raise ValueError(
                "Invalid cookies file format. Expected a list of dictionary. In Selenium format."
            )

        self.cookies = PinterestCookieJar().from_selenium_cookies(cookies)
        return self

    def scrape(
        self, url: str, num: int, min_resolution: Tuple[int, int] = (0, 0), delay: float = 0.2
    ) -> List[PinterestImage]:
        """Scrape pins from Pinterest using the API.

        Args:
            url (str): Pinterest URL to scrape.
            num (int): Maximum number of images to scrape.
            delay (float): Delay in seconds between requests.

        Returns:
            List[PinterestImage]: List of scraped PinterestImage objects.
        """

        images: List[PinterestImage] = []
        api = PinterestAPI(url, self.cookies, timeout=self.timeout)
        bookmarks = BookmarkManager(2)

        if api.is_pin:
            images = self._scrape_pins(api, num, min_resolution, delay, bookmarks)
        else:
            images = self._scrape_board(api, num, min_resolution, delay, bookmarks)

        if self.verbose:
            self._display_images(images)

        if self.verbose:
            self._display_images(images)
        return images

    def scrape_and_download(
        self,
        url: str,
        output_dir: Union[str, Path],
        num: int,
        min_resolution: Tuple[int, int] = (0, 0),
        json_output: Optional[Union[str, Path]] = None,
        dry_run: bool = False,
        add_captions: bool = False,
    ) -> Optional[List[PinterestImage]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Union[str, Path]): Directory to store downloaded images.
            num (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            json_output (Optional[Union[str, Path]]): Path to save scraped data as JSON.
            dry_run (bool): Only scrape URLs without downloading images.
            add_captions (bool): Add captions to downloaded images.

        Returns:
            Optional[List[PinterestImage]]: List of downloaded PinterestImage objects.
        """
        scraped_imgs = self.scrape(url, num, min_resolution)

        imgs_dict = [img.to_dict() for img in scraped_imgs]
        
        if json_output:
            output_path = Path(json_output)
            io.write_json(imgs_dict, output_path, indent=4)

        if dry_run:
            if self.verbose:
                print("Scraped data (dry run):", imgs_dict)
            return None

        downloaded_imgs = self.download_images(scraped_imgs, output_dir, self.verbose)

        valid_indices = []

        if add_captions:
            self.add_captions(downloaded_imgs, valid_indices, self.verbose)

        return downloaded_imgs

    def search(
        self,
        query: str,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float = 0.2,
        bookmarksCount: int = 1,
    ) -> List[PinterestImage]:
        """Scrape pins from a Pinterest search query using the API.

        Args:
            query (str): query to search.
            num (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            delay (float): Delay in seconds between requests in second. Defaults to 0.2.
            bookmarksCount (int, optional): Number of bookmarks to keep. Defaults to 1.

        Returns:
            List[PinterestImage]: List of scraped PinterestImage objects.
        """
        images = []
        remains = num
        batch_count = 0

        if " " in query:
            query = RequestBuilder.url_encode(query)
        url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"

        if self.verbose:
            print(f"Scraping URL: {url}")
        api = PinterestAPI(url, self.cookies, timeout=self.timeout)
        bookmarks = BookmarkManager(bookmarksCount)

        with tqdm(total=num, desc="Scraping Search", disable=self.verbose) as pbar:
            while remains > 0:
                batch_size = min(50, remains)
                current_img_batch, bookmarks = self._search_images(
                    api, batch_size, bookmarks, min_resolution, query
                )

                images.extend(current_img_batch)
                remains -= len(current_img_batch)
                pbar.update(len(current_img_batch))

                if "-end-" in bookmarks.get():
                    break

                if self.verbose:
                    for img in current_img_batch:
                        print(f"[Batch {batch_count}] ({img.src})")
                    print(f"[Batch {batch_count}] bookmarks: {bookmarks.get()}")

                time.sleep(delay)
                remains = self._handle_missing_search_images(
                    api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                )
                batch_count += 1

        return images

    def search_and_download(
        self,
        query: str,
        output_dir: Union[str, Path],
        num: int,
        min_resolution: Tuple[int, int] = (0, 0),
        json_output: Optional[Union[str, Path]] = None,
        dry_run: bool = False,
        add_captions: bool = False,
    ) -> Optional[List[PinterestImage]]:
        """Search for images on Pinterest and download them.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Union[str, Path]): Directory to store downloaded images.
            num (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            json_output (Optional[Union[str, Path]]): Path to save scraped data as JSON.
            dry_run (bool): Only scrape URLs without downloading images.
            add_captions (bool): Add captions to downloaded images.

        Returns:
            Optional[List[PinterestImage]]: List of downloaded PinterestImage objects.
        """
        scraped_imgs = self.search(query, num, min_resolution)

        if json_output:
            output_path = Path(json_output)
            imgs_dict = [img.to_dict() for img in scraped_imgs]
            io.write_json(imgs_dict, output_path, indent=4)

        if dry_run:
            # if self.verbose:
            #     print("Scraped data (dry run):", imgs_dict)
            return None

        downloaded_imgs = self.download_images(scraped_imgs, output_dir, self.verbose)

        valid_indices = []

        if add_captions:
            self.add_captions(downloaded_imgs, valid_indices, self.verbose)

        return downloaded_imgs

    def _scrape_pins(
        self,
        api: PinterestAPI,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
    ) -> List[PinterestImage]:
        """Scrape pins from a specific Pinterest pin URL."""
        images = []
        remains = num

        with tqdm(total=num, desc="Scraping Pins", disable=self.verbose) as pbar:
            while remains > 0:
                batch_size = min(50, remains)
                current_img_batch, bookmarks = self._get_images(
                    api, batch_size, bookmarks, min_resolution
                )

                images.extend(current_img_batch)
                remains -= len(current_img_batch)
                pbar.update(len(current_img_batch))

                if "-end-" in bookmarks.get():
                    break
                if self.verbose:
                    print(f"bookmarks: {bookmarks.get()}")
                time.sleep(delay)
                remains = self._handle_missing_related_images(
                    api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                )

        return images

    def _scrape_board(
        self,
        api: PinterestAPI,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
    ) -> List[PinterestImage]:
        """Scrape pins from a Pinterest board URL."""
        images = []
        board_info = api.get_board()
        board_id = board_info.get_board_id()
        pin_count = board_info.get_pin_count()
        num = min(num, pin_count)
        remains = num

        if self.verbose:
            print(f"Scraping board resource with {pin_count} pins (ID: {board_id})...")

        with tqdm(total=num, desc="Scraping Board", disable=self.verbose) as pbar:
            while remains > 0:
                batch_size = min(50, remains)
                current_img_batch, bookmarks = self._get_images(
                    api, batch_size, bookmarks, min_resolution, board_id
                )

                images.extend(current_img_batch)
                remains -= len(current_img_batch)
                pbar.update(len(current_img_batch))

                if "-end-" in bookmarks.get():
                    break

                time.sleep(delay)
                remains = self._handle_missing_related_images(
                    api,
                    batch_size,
                    remains,
                    bookmarks,
                    min_resolution,
                    images,
                    pbar,
                    delay,
                    board_id,
                )

        return images

    def _get_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        board_id: Optional[str] = None,
    ) -> Tuple[List[PinterestImage], BookmarkManager]:
        """Fetch images based on API response, either from a pin or a board."""
        response = (
            api.get_related_images(batch_size, bookmarks.get())
            if not board_id
            else api.get_board_feed(board_id, batch_size, bookmarks.get())
        )

        # parse response data
        response_data = response.resource_response.get("data", [])

        current_img_batch = PinterestImage.from_response(response_data, min_resolution)
        bookmarks.add_all(response.get_bookmarks())
        return current_img_batch, bookmarks

    def _search_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        query: str,
    ) -> Tuple[List[PinterestImage], BookmarkManager]:
        """Fetch images based on API response, either from a pin or a board."""
        response = api.get_search(batch_size, bookmarks.get())

        # parse response data
        response_data = response.resource_response.get("data", {}).get("results", [])

        current_img_batch = PinterestImage.from_response(response_data, min_resolution)
        bookmarks.add_all(response.get_bookmarks())
        return current_img_batch, bookmarks

    def _handle_missing_search_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        remains: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        images: List[PinterestImage],
        pbar,
        delay: float,
    ) -> int:
        """Handle cases where a batch does not return enough images."""
        difference = batch_size - len(images[-batch_size:])
        while difference > 0 and remains > 0:
            next_response = api.get_search(difference, bookmarks.get())
            next_response_data = next_response.resource_response.get("data", {}).get("results", [])
            additional_images = PinterestImage.from_response(next_response_data, min_resolution)
            images.extend(additional_images)
            bookmarks.add_all(next_response.get_bookmarks())
            remains -= len(additional_images)
            difference -= len(additional_images)
            pbar.update(len(additional_images))
            time.sleep(delay)

        return remains

    def _handle_missing_related_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        remains: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        images: List[PinterestImage],
        pbar,
        delay: float,
        board_id: Optional[str] = None,
    ) -> int:
        """Handle cases where a batch does not return enough images."""
        difference = batch_size - len(images[-batch_size:])
        while difference > 0 and remains > 0:
            next_response = (
                api.get_related_images(difference, bookmarks.get())
                if not board_id
                else api.get_board_feed(board_id, difference, bookmarks.get())
            )
            next_response_data = next_response.resource_response.get("data", [])
            additional_images = PinterestImage.from_response(next_response_data, min_resolution)
            images.extend(additional_images)
            bookmarks.add_all(next_response.get_bookmarks())
            remains -= len(additional_images)
            difference -= len(additional_images)
            pbar.update(len(additional_images))
            time.sleep(delay)

        return remains

    def _display_images(self, images: List[PinterestImage]):
        """Print scraped image URLs if verbosity is enabled."""
        for i, img in enumerate(images):
            print(f"({i + 1}) {img.src}")
