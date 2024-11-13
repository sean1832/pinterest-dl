import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

from tqdm import tqdm

from pinterest_dl.data_model.cookie import PinterestCookieJar
from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.api.pinterest_api import PinterestAPI
from pinterest_dl.low_level.ops import io
from pinterest_dl.low_level.ops.bookmark_manager import BookmarkManager

from .scraper_base import _ScraperBase


class _ScraperAPI(_ScraperBase):
    """Pinterest scraper using the unofficial Pinterest API."""

    def __init__(self, timeout: float = 3, verbose: bool = False) -> None:
        """Initialize PinterestDL with API.

        Args:
            timeout (float, optional): timeout in seconds. Defaults to 3.
            verbose (bool, optional): show detail messages. Defaults to False.
        """
        self.timeout = timeout
        self.verbose = verbose
        self.cookies = None

    def with_cookies(self, cookies_path: Optional[Union[str, Path]]) -> "_ScraperAPI":
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
        self, url: str, limit: int, min_resolution: Tuple[int, int] = (0, 0), delay: float = 0.2
    ) -> List[PinterestImage]:
        """Scrape pins from Pinterest using the API.

        Args:
            url (str): Pinterest URL to scrape.
            limit (int): Maximum number of images to scrape.
            delay (float): Delay in seconds between requests.

        Returns:
            List[PinterestImage]: List of scraped PinterestImage objects.
        """

        images: List[PinterestImage] = []
        api = PinterestAPI(url, self.cookies)
        bookmarks = BookmarkManager(2)

        if api.is_pin:
            images = self._scrape_pins(api, limit, min_resolution, delay, bookmarks)
        else:
            images = self._scrape_board(api, limit, min_resolution, delay, bookmarks)

        if self.verbose:
            self._display_images(images)

        if self.verbose:
            self._display_images(images)
        return images

    def scrape_and_download(
        self,
        url: str,
        output_dir: Union[str, Path],
        limit: int,
        min_resolution: Tuple[int, int] = (0, 0),
        json_output: Optional[Union[str, Path]] = None,
        dry_run: bool = False,
        add_captions: bool = False,
    ) -> Optional[List[PinterestImage]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Union[str, Path]): Directory to store downloaded images.
            limit (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            json_output (Optional[Union[str, Path]]): Path to save scraped data as JSON.
            dry_run (bool): Only scrape URLs without downloading images.
            add_captions (bool): Add captions to downloaded images.

        Returns:
            Optional[List[PinterestImage]]: List of downloaded PinterestImage objects.
        """
        scraped_imgs = self.scrape(url, limit, min_resolution)

        if json_output:
            output_path = Path(json_output)
            imgs_dict = [img.to_dict() for img in scraped_imgs]
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

    def _scrape_pins(
        self,
        api: PinterestAPI,
        limit: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
    ) -> List[PinterestImage]:
        """Scrape pins from a specific Pinterest pin URL."""
        images = []
        remains = limit

        with tqdm(total=limit, desc="Scraping Pins", disable=self.verbose) as pbar:
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

                time.sleep(delay)
                remains = self._handle_missing_images(
                    api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                )

        return images

    def _scrape_board(
        self,
        api: PinterestAPI,
        limit: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
    ) -> List[PinterestImage]:
        """Scrape pins from a Pinterest board URL."""
        images = []
        board_info = api.get_board()
        board_id = board_info.get_board_id()
        pin_count = board_info.get_pin_count()
        limit = min(limit, pin_count)
        remains = limit

        if self.verbose:
            print(f"Scraping board resource with {pin_count} pins (ID: {board_id})...")

        with tqdm(total=limit, desc="Scraping Board", disable=self.verbose) as pbar:
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
                remains = self._handle_missing_images(
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
        current_img_batch = PinterestImage.from_response(response, min_resolution)
        bookmarks.add_all(response.get_bookmarks())
        return current_img_batch, bookmarks

    def _handle_missing_images(
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
            additional_images = PinterestImage.from_response(next_response, min_resolution)
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
