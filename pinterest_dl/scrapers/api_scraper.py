import json
import time
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Union

from tqdm import tqdm

from pinterest_dl.api.api import Api
from pinterest_dl.api.bookmark_manager import BookmarkManager
from pinterest_dl.common import io
from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.cookies import CookieJar
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.download import request_builder
from pinterest_dl.exceptions import EmptyResponseError
from pinterest_dl.parsers.response import ResponseParser

from . import operations

logger = get_logger(__name__)


class ApiScraper:
    """Pinterest scraper using the unofficial Pinterest API."""

    def __init__(
        self,
        timeout: float = 5,
        verbose: bool = False,
        ensure_alt: bool = False,
        dump: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize ApiScraper.

        Args:
            timeout (float, optional): timeout in seconds. Defaults to 3.
            verbose (bool, optional): show detail messages. Defaults to False.
            ensure_alt (bool, optional): whether to remove images without alt text. Defaults to False.
            dump (Optional[str], optional): directory to dump API requests/responses. None to disable (default).
            max_retries (int, optional): maximum number of retry attempts for failed API calls. Defaults to 3.
            retry_delay (float, optional): initial delay between retries in seconds (uses exponential backoff). Defaults to 1.0.
        """
        self.timeout = timeout
        self.verbose = verbose
        self.ensure_alt = ensure_alt
        self.dump = dump
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cookies = None

    def with_cookies(self, cookies: list[dict[str, Any]]) -> "ApiScraper":
        """Load cookies to the current session.

        Args:
            cookies (list[dict]): List of cookies in Selenium format.

        Returns:
            ApiScraper: Instance of ApiScraper with cookies loaded.
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
        self.cookies = CookieJar().from_selenium_cookies(cookies)
        return self

    def with_cookies_path(self, cookies_path: Optional[Union[str, Path]]) -> "ApiScraper":
        """Load cookies from a file to the current session.

        Args:
            cookies_path (Optional[Union[str, Path]]): Path to cookies file.

        Returns:
            ApiScraper: Instance of ApiScraper with cookies loaded.
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

        self.cookies = CookieJar().from_selenium_cookies(cookies)
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
        api = Api(
            url,
            self.cookies,
            timeout=self.timeout,
            dump=self.dump,
        )
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

        logger.info(f"Successfully scraped {len(medias[:num])} media items from {url}")
        return medias[:num]

    def scrape_and_download(
        self,
        url: str,
        output_dir: Optional[Union[str, Path]],
        num: int,
        download_streams: bool = False,
        skip_remux: bool = False,
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
            skip_remux (bool): If True, output raw .ts file without ffmpeg remux.
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
            logger.info(f"Cached {len(items_as_dict)} items to {output_path}")

        if not output_dir:
            return None

        try:
            downloaded_items = operations.download_media(
                scraped_outputs, output_dir, download_streams, skip_remux
            )
        except Exception as e:
            logger.error(f"Failed to download media: {e}", exc_info=self.verbose)
            raise

        if caption == "txt" or caption == "json":
            try:
                operations.add_captions_to_file(downloaded_items, output_dir, caption, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to file: {e}", exc_info=self.verbose)
                raise
        elif caption == "metadata":
            try:
                operations.add_captions_to_meta(downloaded_items, self.verbose)
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
            query = request_builder.url_encode(query)
        url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"

        logger.info(f"Starting search scrape for query: '{query}', target: {num} items")
        if self.verbose:
            logger.debug(f"Search URL: {url}")
        api = Api(
            url,
            self.cookies,
            timeout=self.timeout,
            dump=self.dump,
        )
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
                        logger.debug(f"[Batch {batch_count}] ({img.src})")
                    logger.debug(f"[Batch {batch_count}] bookmarks: {bookmarks.get()}")

                time.sleep(delay)
                try:
                    remains = self._handle_missing_search_images(
                        api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(
                        f"Search scraping interrupted while handling missing images: {e}"
                    )
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
        skip_remux: bool = False,
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
            skip_remux (bool): If True, output raw .ts file without ffmpeg remux.
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
            logger.info(f"Cached {len(items_as_dict)} search results to {output_path}")

        if not output_dir:
            return None

        try:
            downloaded_items = operations.download_media(
                scraped_outputs, output_dir, download_streams, skip_remux
            )
        except Exception as e:
            logger.error(f"Failed to download media: {e}", exc_info=self.verbose)
            raise

        # Caption handling
        if caption in ("txt", "json"):
            try:
                operations.add_captions_to_file(downloaded_items, output_dir, caption, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to file: {e}", exc_info=self.verbose)
                raise
        elif caption == "metadata":
            try:
                # if metadata embedding needs some indices/selection, decide and supply them here explicitly
                operations.add_captions_to_meta(downloaded_items, self.verbose)
            except Exception as e:
                logger.error(f"Failed to add captions to metadata: {e}", exc_info=self.verbose)
                raise
        elif caption != "none":
            raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")

        return downloaded_items

    def _scrape_pins(
        self,
        api: Api,
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
                    logger.debug(f"bookmarks: {bookmarks.get()}")
                time.sleep(delay)
                try:
                    remains = self._handle_missing_images(
                        api, batch_size, remains, bookmarks, min_resolution, images, pbar, delay
                    )
                except (ValueError, EmptyResponseError) as e:
                    logger.warning(f"Scraping interrupted while handling missing images: {e}")
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
        api: Api,
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

        logger.info(f"Scraping board with {pin_count} pins (ID: {board_id}), target: {num} items")
        if self.verbose:
            logger.debug(f"Board URL: {api.url}")

        with tqdm(total=num, desc="Scraping Board", disable=self.verbose) as pbar:
            consecutive_empty_responses = 0
            max_consecutive_failures = 3

            while remains > 0:
                batch_size = min(50, remains)
                try:
                    current_img_batch, bookmarks = self._get_images_with_retry(
                        api,
                        batch_size,
                        bookmarks,
                        min_resolution,
                        board_id=board_id,
                        caption_from_title=caption_from_title,
                    )
                    # Reset consecutive failure counter on success
                    consecutive_empty_responses = 0
                except EmptyResponseError as e:
                    consecutive_empty_responses += 1
                    logger.warning(
                        f"Failed to fetch batch after retries: {e} "
                        f"(consecutive failures: {consecutive_empty_responses}/{max_consecutive_failures})"
                    )

                    # Stop if we hit too many consecutive failures
                    if consecutive_empty_responses >= max_consecutive_failures:
                        logger.warning(
                            f"Stopping: {max_consecutive_failures} consecutive empty responses. "
                            f"Scraped {len(medias)} items so far."
                        )
                        break

                    # Continue to next batch - might be a transient issue
                    time.sleep(delay)
                    continue
                except ValueError as e:
                    logger.warning(f"Board scraping interrupted: {e}")
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

                # Check if we've reached the end before trying to fetch more
                if "-end-" in bookmarks.get():
                    logger.debug("Reached end of board (bookmark indicates no more items)")
                    break

                time.sleep(delay)

                # Only try to fetch missing images if we haven't reached the end
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
                    break
                except EmptyResponseError as e:
                    # Empty response when trying to fill gaps - likely reached the end
                    logger.debug(f"Empty response while filling batch gaps: {e}")
                    # Don't break - we got some images, just can't fill the gap
                    break

        return medias

    def _get_images_with_retry(
        self,
        api: Api,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        board_id: Optional[str] = None,
        caption_from_title: bool = False,
    ) -> Tuple[List[PinterestMedia], BookmarkManager]:
        """Fetch images with retry logic for transient failures.

        Implements exponential backoff retry strategy for API calls.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._get_images(
                    api,
                    batch_size,
                    bookmarks,
                    min_resolution,
                    board_id=board_id,
                    caption_from_title=caption_from_title,
                )
            except EmptyResponseError as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff: 1s, 2s, 4s...
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Empty response received (attempt {attempt + 1}/{self.max_retries + 1}). "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        f"Empty response persists after {self.max_retries + 1} attempts. "
                        f"Skipping this batch."
                    )
            except Exception as e:
                # For other errors, fail immediately without retry
                logger.error(f"Non-retryable error during API call: {e}", exc_info=self.verbose)
                raise

        # If all retries failed, raise the last error
        if last_error:
            raise last_error

        # Fallback (shouldn't reach here)
        raise EmptyResponseError("Failed to fetch images after all retry attempts")

    def _get_images(
        self,
        api: Api,
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
            img_batch = ResponseParser.from_responses(
                response_data, min_resolution, caption_from_title=caption_from_title
            )
        except EmptyResponseError:
            logger.warning("Empty response received from Pinterest API")
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
                    logger.debug(f"Removed {culled_count} images with no alt text from batch.")
        bookmarks.add_all(response.get_bookmarks())
        return img_batch, bookmarks

    def _search_images(
        self,
        api: Api,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> Tuple[List[PinterestMedia], BookmarkManager]:
        """Fetch images based on API response, either from a pin or a board."""
        response = api.get_search(batch_size, bookmarks.get())

        # parse response data
        response_data = response.resource_response.get("data", {}).get("results", [])

        img_batch = ResponseParser.from_responses(
            response_data, min_resolution, caption_from_title=caption_from_title
        )
        if self.ensure_alt:
            batch_count = len(img_batch)
            img_batch = self._cull_no_alt(img_batch)

            if self.verbose:
                culled_count = batch_count - len(img_batch)
                if culled_count:
                    logger.debug(f"Removed {culled_count} images with no alt text from batch.")
        bookmarks.add_all(response.get_bookmarks())
        return img_batch, bookmarks

    def _cull_no_alt(self, images: List[PinterestMedia]) -> List[PinterestMedia]:
        """Remove images with no alt text."""
        return [img for img in images if img.alt and img.alt.strip() != ""]

    def _handle_missing_search_images(
        self,
        api: Api,
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
            additional_images = ResponseParser.from_responses(next_response_data, min_resolution)
            images.extend(additional_images)
            bookmarks.add_all(next_response.get_bookmarks())
            remains -= len(additional_images)
            difference -= len(additional_images)
            pbar.update(len(additional_images))
            time.sleep(delay)

        return remains

    def _handle_missing_images(
        self,
        api: Api,
        batch_size: int,
        remains: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        images: List[PinterestMedia],
        pbar: tqdm,
        delay: float,
        board_id: Optional[str] = None,
    ) -> int:
        """Handle cases where a batch does not return enough images.

        Returns the updated remains count.
        """
        difference = batch_size - len(images[-batch_size:])

        while difference > 0 and remains > 0:
            # Check if we've reached the end before making more requests
            if "-end-" in bookmarks.get():
                logger.debug("Cannot fetch more images: reached end of available content")
                break

            try:
                next_response = (
                    api.get_related_images(difference, bookmarks.get())
                    if not board_id
                    else api.get_board_feed(board_id, difference, bookmarks.get())
                )
                next_response_data = next_response.resource_response.get("data", [])

                # Handle empty response gracefully
                if not next_response_data:
                    logger.debug("No additional images available to fill batch")
                    break

                additional_images = ResponseParser.from_responses(
                    next_response_data, min_resolution
                )
                images.extend(additional_images)
                bookmarks.add_all(next_response.get_bookmarks())
                remains -= len(additional_images)
                difference -= len(additional_images)
                pbar.update(len(additional_images))
                time.sleep(delay)

            except EmptyResponseError as e:
                # Empty response is expected when no more images are available
                logger.debug(f"No more images to fetch: {e}")
                break
            except Exception as e:
                # Log other errors but don't fail the entire scrape
                logger.warning(f"Error while fetching additional images: {e}")
                break

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
        """Print scraped media URLs if verbosity is enabled."""
        for i, img in enumerate(images):
            if img.video_stream:
                logger.debug(f"({i + 1}) [VIDEO] {img.video_stream.url}")
            else:
                logger.debug(f"({i + 1}) {img.src}")
