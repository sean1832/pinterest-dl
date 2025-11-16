import json
import logging
import time
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Union

from tqdm import tqdm

from pinterest_dl.data_model.cookie import PinterestCookieJar
from pinterest_dl.data_model.pinterest_media import PinterestMedia
from pinterest_dl.exceptions import EmptyResponseError
from pinterest_dl.low_level.api.bookmark_manager import BookmarkManager
from pinterest_dl.low_level.api.pinterest_api import PinterestAPI
from pinterest_dl.low_level.http.request_builder import RequestBuilder
from pinterest_dl.utils import io

from .scraper_base import _ScraperBase

logger = logging.getLogger(__name__)


class _ScraperAPI(_ScraperBase):
    """Pinterest scraper using the unofficial Pinterest API."""

    def __init__(self, timeout: float = 5, verbose: bool = False, ensure_alt: bool = False) -> None:
        """Initialize PinterestDL with API.

        Args:
            timeout (float, optional): timeout in seconds. Defaults to 3.
            verbose (bool, optional): show detail messages. Defaults to False.
            ensure_alt (bool, optional): whether to remove images without alt text. Defaults to False.
        """
        self.timeout = timeout
        self.verbose = verbose
        self.ensure_alt = ensure_alt
        self.cookies = None

    def with_cookies(self, cookies: list[dict[str, Any]]) -> "_ScraperAPI":
        """Load cookies to the current session.

        Args:
            cookies (list[dict]): List of cookies in Selenium format.

        Returns:
            _ScraperAPI: Instance of ScraperAPI with cookies loaded.
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
        self,
        url: str,
        num: int,
        min_resolution: Tuple[int, int] = (0, 0),
        delay: float = 0.2,
        caption_from_title: bool = False,
    ) -> List[PinterestMedia]:
        """Scrape pins from Pinterest using the API.

        Args:
            url (str): Pinterest URL to scrape.
            num (int): Maximum number of images to scrape.
            delay (float): Delay in seconds between requests.

        Returns:
            List[PinterestMedia]: List of scraped PinterestMedia objects.
        """

        medias: List[PinterestMedia] = []
        api = PinterestAPI(url, self.cookies, timeout=self.timeout)
        bookmarks = BookmarkManager(3)

        if api.is_pin:
            medias = self._scrape_pins(
                api, num, min_resolution, delay, bookmarks, caption_from_title=caption_from_title
            )
        else:
            medias = self._scrape_board(
                api, num, min_resolution, delay, bookmarks, caption_from_title=caption_from_title
            )

        if self.verbose:
            self._display_images(medias)

        if self.verbose:
            self._display_images(medias)
        return medias[:num]

    def scrape_and_download(
        self,
        url: str,
        output_dir: Optional[Union[str, Path]],
        num: int,
        download_streams: bool = False,
        min_resolution: Tuple[int, int] = (0, 0),
        cache_path: Optional[Union[str, Path]] = None,
        caption: Literal["txt", "json", "metadata", "none"] = "none",
        caption_from_title: bool = False,
        delay: float = 0.2,
    ) -> Optional[List[PinterestMedia]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Optional[Union[str, Path]]): Directory to store downloaded images. 'None' print to console.
            num (int): Maximum number of images to scrape.
            download_streams (bool): Whether to download video streams if available.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            cache_path (Optional[Union[str, Path]]): Path to cache scraped data as json
            caption (Literal["txt", "json", "metadata", "none"]): Caption mode for downloaded images.
                'txt' for alt text in separate files,
                'json' for full image data,
                'metadata' embeds in image files,
                'none' skips captions
            caption_from_title (bool): Use the image title as the caption.
            delay (float): Delay in seconds between requests.

        Returns:
            Optional[List[PinterestMedia]]: List of downloaded PinterestMedia objects.
        """
        scraped_outputs = self.scrape(
            url,
            num,
            min_resolution,
            delay,
            caption_from_title=caption_from_title,
        )

        # Prepare for caching / console output
        items_as_dict = [item.to_dict() for item in scraped_outputs]

        if not output_dir and not cache_path:
            # no output_dir and cache_path provided, print the scraped image data to console
            print("Scraped: ")
            print(json.dumps(items_as_dict, indent=2))

        if cache_path:
            output_path = Path(cache_path)
            io.write_json(items_as_dict, output_path, indent=4)
            print(f"Scraped data cached to {output_path}")

        if not output_dir:
            return None

        try:
            downloaded_items = self.download_media(scraped_outputs, output_dir, download_streams)
        except Exception as e:
            logger.error(f"Failed to download media: {e}", exc_info=self.verbose)
            raise

        if caption == "txt" or caption == "json":
            try:
                self.add_captions_to_file(downloaded_items, output_dir, caption, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to file: {e}", exc_info=self.verbose)
                raise
        elif caption == "metadata":
            try:
                self.add_captions_to_meta(downloaded_items, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to metadata: {e}", exc_info=self.verbose)
                raise
        elif caption != "none":
            raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")

        return downloaded_items

    def search(
        self,
        query: str,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float = 0.2,
        bookmarksCount: int = 1,
        caption_from_title: bool = False,
    ) -> List[PinterestMedia]:
        """Scrape pins from a Pinterest search query using the API.

        Args:
            query (str): query to search.
            num (int): Maximum number of images to scrape.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            delay (float): Delay in seconds between requests in second. Defaults to 0.2.
            bookmarksCount (int, optional): Number of bookmarks to keep. Defaults to 1.

        Returns:
            List[PinterestMedia]: List of scraped PinterestMedia objects.
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
                try:
                    current_img_batch, bookmarks = self._search_images(
                        api,
                        batch_size,
                        bookmarks,
                        min_resolution,
                        caption_from_title=caption_from_title,
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(f"Search scraping interrupted: {e}")
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except Exception as e:
                    logger.error(
                        f"Unexpected error during search scraping: {e}", exc_info=self.verbose
                    )
                    raise

                old_count = len(images)
                images.extend(current_img_batch)
                images = self._unique_images(images)
                new_images_count = len(images) - old_count
                remains -= new_images_count
                pbar.update(new_images_count)

                if "-end-" in bookmarks.get():
                    break

                if self.verbose:
                    for img in current_img_batch:
                        print(f"[Batch {batch_count}] ({img.src})")
                    print(f"[Batch {batch_count}] bookmarks: {bookmarks.get()}")

                time.sleep(delay)
                try:
                    remains = self._handle_missing_search_images(
                        api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(
                        f"Search scraping interrupted while handling missing images: {e}"
                    )
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except Exception as e:
                    logger.error(
                        f"Unexpected error while handling missing search images: {e}",
                        exc_info=self.verbose,
                    )
                    raise
                batch_count += 1

        return images[:num]

    def search_and_download(
        self,
        query: str,
        output_dir: Optional[Union[str, Path]],
        num: int,
        download_streams: bool = False,
        min_resolution: Tuple[int, int] = (0, 0),
        cache_path: Optional[Union[str, Path]] = None,
        caption: Literal["txt", "json", "metadata", "none"] = "none",
        delay: float = 0.2,
        caption_from_title: bool = False,
    ) -> Optional[List[PinterestMedia]]:
        """Search for images on Pinterest and download them.

        Args:
            url (str): Pinterest URL to scrape.
            output_dir (Optional[Union[str, Path]]): Directory to store downloaded images. 'None' print to console.
            num (int): Maximum number of images to scrape.
            download_streams (bool): Whether to download video streams if available.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            cache_path (Optional[Union[str, Path]]): Path to cache scraped data as json
            caption (Literal["txt", "json", "metadata", "none"]): Caption mode for downloaded images.
                'txt' for alt text in separate files,
                'json' for full image data,
                'metadata' embeds in image files,
                'none' skips captions
            delay (float): Delay in seconds between requests.


        Returns:
            Optional[List[PinterestMedia]]: List of downloaded PinterestMedia objects.
        """
        scraped_outputs = self.search(
            query, num, min_resolution, delay, caption_from_title=caption_from_title
        )

        # Prepare for caching / console output
        items_as_dict = [item.to_dict() for item in scraped_outputs]

        if not output_dir:
            print("Scraped:")
            print(json.dumps(items_as_dict, indent=2))

        if cache_path:
            output_path = Path(cache_path)
            io.write_json(items_as_dict, output_path, indent=4)
            print(f"Scraped data cached to {output_path}")

        if not output_dir:
            return None

        try:
            downloaded_items = self.download_media(scraped_outputs, output_dir, download_streams)
        except Exception as e:
            logger.error(f"Failed to download media: {e}", exc_info=self.verbose)
            raise

        # Caption handling
        if caption in ("txt", "json"):
            try:
                self.add_captions_to_file(downloaded_items, output_dir, caption, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to file: {e}", exc_info=self.verbose)
                raise
        elif caption == "metadata":
            try:
                # if metadata embedding needs some indices/selection, decide and supply them here explicitly
                self.add_captions_to_meta(downloaded_items, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to metadata: {e}", exc_info=self.verbose)
                raise
        elif caption != "none":
            raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")

        return downloaded_items

    def _scrape_pins(
        self,
        api: PinterestAPI,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
        caption_from_title: bool = False,
    ) -> List[PinterestMedia]:
        """Scrape pins from a specific Pinterest pin URL."""
        images: List[PinterestMedia] = []
        remains = num

        with tqdm(total=num, desc="Scraping Pins", disable=self.verbose) as pbar:
            while remains > 0:
                batch_size = min(50, remains)
                try:
                    current_img_batch, bookmarks = self._get_images(
                        api,
                        batch_size,
                        bookmarks,
                        min_resolution,
                        caption_from_title=caption_from_title,
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(f"Scraping interrupted: {e}")
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error while scraping: {e}", exc_info=self.verbose)
                    raise

                old_count = len(images)
                images.extend(current_img_batch)
                images = self._unique_images(images)
                new_images_count = len(images) - old_count
                remains -= new_images_count
                pbar.update(new_images_count)

                if "-end-" in bookmarks.get():
                    break
                if self.verbose:
                    print(f"bookmarks: {bookmarks.get()}")
                time.sleep(delay)
                try:
                    remains = self._handle_missing_images(
                        api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(f"Scraping interrupted while handling missing images: {e}")
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except Exception as e:
                    logger.error(
                        f"Unexpected error while handling missing images: {e}",
                        exc_info=self.verbose,
                    )
                    raise

        return images

    def _scrape_board(
        self,
        api: PinterestAPI,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float,
        bookmarks: BookmarkManager,
        caption_from_title: bool = False,
    ) -> List[PinterestMedia]:
        """Scrape pins from a Pinterest board URL."""
        medias: List[PinterestMedia] = []
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
                try:
                    current_img_batch, bookmarks = self._get_images(
                        api,
                        batch_size,
                        bookmarks,
                        min_resolution,
                        board_id=board_id,
                        caption_from_title=caption_from_title,
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(f"Board scraping interrupted: {e}")
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except Exception as e:
                    logger.error(
                        f"Unexpected error while scraping board: {e}", exc_info=self.verbose
                    )
                    raise

                old_count = len(medias)
                medias.extend(current_img_batch)
                medias = self._unique_images(medias)
                new_images_count = len(medias) - old_count
                remains -= new_images_count
                pbar.update(new_images_count)

                if "-end-" in bookmarks.get():
                    break

                time.sleep(delay)
                try:
                    remains = self._handle_missing_images(
                        api,
                        batch_size,
                        remains,
                        bookmarks,
                        min_resolution,
                        medias,
                        pbar,
                        delay,
                        board_id,
                    )
                except ValueError as e:
                    logger.error(f"Scraping error: {e}", exc_info=self.verbose)
                    print(f"\nError: {e}. Exiting scraping.")
                    break
                except EmptyResponseError as e:
                    logger.warning(f"Empty response error: {e}")
                    print(f"\nEmptyResponseError: {e}. Exiting scraping.")
                    break

        return medias

    def _get_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        board_id: Optional[str] = None,
        caption_from_title: bool = False,
    ) -> Tuple[List[PinterestMedia], BookmarkManager]:
        """Fetch images based on API response, either from a pin or a board."""
        response = (
            api.get_related_images(batch_size, bookmarks.get())
            if not board_id
            else api.get_board_feed(board_id, batch_size, bookmarks.get())
        )

        # parse response data
        response_data = response.resource_response.get("data", [])
        try:
            img_batch = PinterestMedia.from_responses(
                response_data, min_resolution, caption_from_title=caption_from_title
            )
        except EmptyResponseError:
            logger.warning("Empty response received from Pinterest API")
            print("Empty response received.")
            return [], bookmarks
        except Exception as e:
            # Log unexpected errors during response parsing
            logger.error(f"Failed to parse Pinterest response: {e}", exc_info=self.verbose)
            raise
        if self.ensure_alt:
            batch_count = len(img_batch)
            img_batch = self._cull_no_alt(img_batch)

            if self.verbose:
                culled_count = batch_count - len(img_batch)
                if culled_count:
                    print(f"Removed {culled_count} images with no alt text from batch.")
        bookmarks.add_all(response.get_bookmarks())
        return img_batch, bookmarks

    def _search_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> Tuple[List[PinterestMedia], BookmarkManager]:
        """Fetch images based on API response, either from a pin or a board."""
        response = api.get_search(batch_size, bookmarks.get())

        # parse response data
        response_data = response.resource_response.get("data", {}).get("results", [])

        img_batch = PinterestMedia.from_responses(
            response_data, min_resolution, caption_from_title=caption_from_title
        )
        if self.ensure_alt:
            batch_count = len(img_batch)
            img_batch = self._cull_no_alt(img_batch)

            if self.verbose:
                culled_count = batch_count - len(img_batch)
                if culled_count:
                    print(f"Removed {culled_count} images with no alt text from batch.")
        bookmarks.add_all(response.get_bookmarks())
        return img_batch, bookmarks

    def _cull_no_alt(self, images: List[PinterestMedia]) -> List[PinterestMedia]:
        """Remove images with no alt text."""
        return [img for img in images if img.alt and img.alt.strip() != ""]

    def _handle_missing_search_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        remains: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        images: List[PinterestMedia],
        pbar: tqdm,
        delay: float,
    ) -> int:
        """Handle cases where a batch does not return enough images."""
        difference = batch_size - len(images[-batch_size:])
        while difference > 0 and remains > 0:
            next_response = api.get_search(difference, bookmarks.get())
            next_response_data = next_response.resource_response.get("data", {}).get("results", [])
            additional_images = PinterestMedia.from_responses(next_response_data, min_resolution)
            images.extend(additional_images)
            bookmarks.add_all(next_response.get_bookmarks())
            remains -= len(additional_images)
            difference -= len(additional_images)
            pbar.update(len(additional_images))
            time.sleep(delay)

        return remains

    def _handle_missing_images(
        self,
        api: PinterestAPI,
        batch_size: int,
        remains: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        images: List[PinterestMedia],
        pbar: tqdm,
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
            additional_images = PinterestMedia.from_responses(next_response_data, min_resolution)
            images.extend(additional_images)
            bookmarks.add_all(next_response.get_bookmarks())
            remains -= len(additional_images)
            difference -= len(additional_images)
            pbar.update(len(additional_images))
            time.sleep(delay)

        return remains

    def _unique_images(self, images: List[PinterestMedia]) -> List[PinterestMedia]:
        """Return a list of unique PinterestMedia objects based on their 'src' attribute."""
        unique = []
        seen = set()
        for img in images:
            if img.src not in seen:
                unique.append(img)
                seen.add(img.src)
        return unique

    def _display_images(self, images: List[PinterestMedia]):
        """Print scraped image URLs if verbosity is enabled."""
        for i, img in enumerate(images):
            print(f"({i + 1}) {img.src}")
