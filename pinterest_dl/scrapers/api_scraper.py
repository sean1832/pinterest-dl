import itertools
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterator, List, Literal, Optional, Tuple, Union

from pinterest_dl.api.api import Api
from pinterest_dl.api.bookmark_manager import BookmarkManager
from pinterest_dl.common import io
from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.cookies import CookieJar
from pinterest_dl.domain.media import PinterestMedia, VideoStreamInfo
from pinterest_dl.download import request_builder
from pinterest_dl.exceptions import EmptyResponseError, HttpResponseError
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
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
    ) -> List[PinterestMedia]:
        """Scrape pins from Pinterest using the API.

        Args:
            url (str): Pinterest URL to scrape. Supports:
                - Pin URL: scrapes the requested pin itself, then fills the
                  remainder of `num` with related pins when `num > 1`
                - Board URL: scrapes pins from the board
                - Section URL: scrapes pins from a specific board section
            num (int): Maximum number of images to scrape.
            delay (float): Delay in seconds between requests.
            caption_from_title (bool): Use the image title as the caption.
            on_progress (Optional[Callable[[PinterestMedia], None]]): Optional callback function to be called for each scraped media item for progress reporting.

        Returns:
            List[PinterestMedia]: List of scraped PinterestMedia objects.
        """
        api = self._create_api(url)
        if api.query is not None:
            source = self.iter_search(api.query, min_resolution, delay, caption_from_title)
            medias = self._collect(source, num, on_progress)
        elif api.is_pin:
            # The main pin is always the first result. Related pins only fill
            # the remainder when num > 1; a filtered-out pin returns [] not a related pin.
            main = self._scrape_one_pin(api, min_resolution, caption_from_title)
            medias = [main] if main else []
            if main and on_progress:
                on_progress(main)
            if num > 1:
                source = self._pump(
                    lambda size, bm: self._get_images(
                        api, size, bm, min_resolution, caption_from_title=caption_from_title
                    ),
                    delay,
                )
                medias.extend(self._collect(source, num - len(medias), on_progress))
        elif api.is_section:
            source = self._iter_section(api, min_resolution, delay, caption_from_title)
            medias = self._collect(source, num, on_progress)
        else:
            source = self._iter_board(api, min_resolution, delay, caption_from_title)
            medias = self._collect(source, num, on_progress)
        if self.verbose:
            self._display_images(medias)
        logger.info(f"Successfully scraped {len(medias)} media items from {url}")
        return medias

    def related(
        self,
        url: str,
        num: int,
        min_resolution: Tuple[int, int] = (0, 0),
        delay: float = 0.2,
        caption_from_title: bool = False,
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
    ) -> List[PinterestMedia]:
        """Scrape related pins from a pin URL.

        Args:
            url (str): Pinterest pin URL to scrape related pins from.
            num (int): Maximum number of related pins to scrape.
            min_resolution (Tuple[int, int], optional): Minimum resolution for pruning. Defaults to (0, 0).
            delay (float, optional): Delay in seconds between requests. Defaults to 0.2.
            caption_from_title (bool, optional): Use the image title as the caption. Defaults to False.
            on_progress (Optional[Callable[[PinterestMedia], None]], optional): Optional callback function to be called for each scraped media item for progress reporting. Defaults to None.

        Returns:
            List[PinterestMedia]: List of scraped PinterestMedia objects related to the given pin URL.
        """
        api = self._create_api(url)
        if not api.is_pin:
            raise ValueError("related only supports Pinterest pin URLs")
        source = self._pump(
            lambda size, bm: self._get_images(
                api, size, bm, min_resolution, caption_from_title=caption_from_title
            ),
            delay,
        )
        medias = self._collect(source, num, on_progress)
        if self.verbose:
            self._display_images(medias)
        logger.info(f"Successfully scraped {len(medias)} related media items from {url}")
        return medias

    def search(
        self,
        query: str,
        num: int,
        min_resolution: Tuple[int, int],
        delay: float = 0.2,
        bookmarksCount: int = 1,
        caption_from_title: bool = False,
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
    ) -> List[PinterestMedia]:
        """Search for pins on Pinterest and return results.

        Args:
            query (str): The search query.
            num (int): The number of results to return.
            min_resolution (Tuple[int, int]): The minimum resolution for the images.
            delay (float, optional): The delay between requests. Defaults to 0.2.
            bookmarksCount (int, optional): The number of bookmarks to fetch. Defaults to 1.
            caption_from_title (bool, optional): Whether to use the title as the caption. Defaults to False.
            on_progress (Optional[Callable[[PinterestMedia], None]], optional): A callback function to be called for each scraped media item. Defaults to None.

        Returns:
            List[PinterestMedia]: A list of PinterestMedia objects matching the search query, up to the specified count.
        """
        source = self.iter_search(query, min_resolution, delay, bookmarksCount, caption_from_title)
        medias = self._collect(source, num, on_progress)
        logger.info(f"Successfully scraped {len(medias)} media items for search query: '{query}'")
        return medias

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
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
    ) -> Optional[List[PinterestMedia]]:
        """Scrape pins from Pinterest and download images.

        Args:
            url (str): Pinterest URL to scrape. Supports:
                - Pin URL: scrapes the requested pin itself, then fills the
                  remainder of `num` with related pins when `num > 1`
                - Board URL: scrapes pins from the board
                - Section URL: scrapes pins from a specific board section
            output_dir (Optional[Union[str, Path]]): Directory to store downloaded images. 'None' print to console.
            num (int): Maximum number of images to scrape.
            download_streams (bool): Whether to download video streams if available.
            skip_remux (bool): If True, output raw .ts file without ffmpeg remux.
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to download all images.
            cache_path (Optional[Union[str, Path]]): Path to cache scraped data as json
            caption (Literal["txt", "json", "metadata", "none"]): Caption mode for downloaded images.
                - 'txt' for alt text in separate files,
                - 'json' for full image data,
                - 'metadata' embeds in image files,
                - 'none' skips captions
            caption_from_title (bool): Use the image title as the caption.
            delay (float): Delay in seconds between requests.
            on_progress (Optional[Callable[[PinterestMedia], None]]): Optional callback invoked with each scraped media item for progress reporting.

        Returns:
            Optional[List[PinterestMedia]]: List of downloaded PinterestMedia objects.
        """
        scraped_outputs = self.scrape(
            url,
            num,
            min_resolution,
            delay,
            caption_from_title=caption_from_title,
            on_progress=on_progress,
        )
        return self._download_and_save(
            scraped_outputs, output_dir, download_streams, skip_remux, cache_path, caption
        )

    def related_and_download(
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
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
    ) -> Optional[List[PinterestMedia]]:
        """Scrape related pins from a pin URL and download them."""
        scraped_outputs = self.related(
            url,
            num,
            min_resolution,
            delay,
            caption_from_title=caption_from_title,
            on_progress=on_progress,
        )
        return self._download_and_save(
            scraped_outputs, output_dir, download_streams, skip_remux, cache_path, caption
        )

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
        on_progress: Optional[Callable[[PinterestMedia], None]] = None,
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
                - 'txt' for alt text in separate files,
                - 'json' for full image data,
                - 'metadata' embeds in image files,
                - 'none' skips captions
            delay (float): Delay in seconds between requests.
            on_progress (Optional[Callable[[PinterestMedia], None]]): Optional callback invoked with each scraped media item for progress reporting.

        Returns:
            Optional[List[PinterestMedia]]: List of downloaded PinterestMedia objects.
        """
        scraped_outputs = self.search(
            query,
            num,
            min_resolution,
            delay,
            caption_from_title=caption_from_title,
            on_progress=on_progress,
        )
        return self._download_and_save(
            scraped_outputs, output_dir, download_streams, skip_remux, cache_path, caption
        )

    def iter_scrape(
        self,
        url: str,
        min_resolution: Tuple[int, int] = (0, 0),
        delay: float = 0.2,
        caption_from_title: bool = False,
    ) -> Iterator[PinterestMedia]:
        """Lazily yield media for any supported URL (pin, board, or section).

        Args:
            url (str): Pinterest URL to scrape. Supports:
                - Pin URL: scrapes the requested pin itself, then continues with related pins
                - Board URL: scrapes pins from the board
                - Section URL: scrapes pins from a specific board section
            min_resolution (Tuple[int, int]): Minimum resolution for pruning. (width, height). (0, 0) to include all images.
            delay (float): Delay in seconds between requests.
            caption_from_title (bool): Use the image title as the caption.
        Returns:
            Iterator[PinterestMedia]: An iterator over scraped PinterestMedia objects.
        """
        api = self._create_api(url)
        if api.query is not None:
            # Search URL detected - delegate to iter_search
            yield from self.iter_search(api.query, min_resolution, delay, caption_from_title)
        elif api.is_pin:
            main = self._scrape_one_pin(api, min_resolution, caption_from_title)
            if main is not None:
                yield main
            yield from self._pump(
                lambda size, bm: self._get_images(
                    api, size, bm, min_resolution, caption_from_title=caption_from_title
                ),
                delay,
            )
        elif api.is_section:
            yield from self._iter_section(api, min_resolution, delay, caption_from_title)
        else:
            yield from self._iter_board(api, min_resolution, delay, caption_from_title)

    def iter_search(
        self,
        query: str,
        min_resolution: Tuple[int, int] = (0, 0),
        delay: float = 0.2,
        bookmarksCount: int = 1,
        caption_from_title: bool = False,
    ) -> Iterator[PinterestMedia]:
        """Search for pins on Pinterest and yield results lazily.

        Args:
            query (str): query to search.
            min_resolution (Tuple[int, int], optional): Minimum resolution for the images. Defaults to (0, 0).
            delay (float, optional): Delay between requests. Defaults to 0.2.
            bookmarksCount (int, optional): Number of bookmarks to fetch. Defaults to 1.
            caption_from_title (bool, optional): Whether to use the title as the caption. Defaults to False.

        Yields:
            Iterator[PinterestMedia]: An iterator over search results as PinterestMedia objects.
        """
        if " " in query:
            query = request_builder.url_encode(query)
        url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"
        logger.info(f"Starting search scrape for query: '{query}'")
        api = Api(url, self.cookies, self.timeout, self.dump)
        yield from self._pump(
            lambda size, bm: self._search_images(
                api, size, bm, min_resolution, caption_from_title=caption_from_title
            ),
            delay,
            bookmarks=BookmarkManager(bookmarksCount),
        )

    def _pump(
        self,
        fetch_batch: Callable[[int, BookmarkManager], Tuple[List[PinterestMedia], BookmarkManager]],
        delay: float,
        bookmarks: Optional[BookmarkManager] = None,
    ) -> Iterator[PinterestMedia]:
        """Page through a Pinterest bookmark stream, yielding unique media lazily.

        Args:
            fetch_batch (fetch_batch(batch_size, bookmarks)): Function that fetches the next batch of media given a batch size and current bookmarks, returning (media_list, new_bookmarks).
            delay (float): Delay in seconds between batch fetches to avoid hitting rate limits.
            bookmarks (Optional[BookmarkManager]): Initial bookmarks to start from. If None, starts from the beginning of the stream.

        Yields:
            Iterator[PinterestMedia]: An iterator over unique PinterestMedia objects from the stream.
        """
        bookmarks = bookmarks or BookmarkManager(3)
        seen: set[str] = set()
        while True:
            try:
                batch, bookmarks = fetch_batch(
                    50, bookmarks
                )  # pinterest API seems to max out at 50 items per request
            except (ValueError, EmptyResponseError) as e:
                logger.warning(f"Scraping interrupted: {e}")
                return
            except Exception as e:
                logger.error(f"Unexpected error while scraping: {e}", exc_info=self.verbose)
                raise

            for media in batch:
                if media.src not in seen:
                    seen.add(media.src)
                    yield media

            # "-end-" is a special bookmark value indicating no more results
            if "-end-" in bookmarks.get():
                return
            time.sleep(delay)

    def _collect(
        self,
        source: Iterator[PinterestMedia],
        num: int,
        on_progress: Optional[Callable[[PinterestMedia], None]],
    ) -> List[PinterestMedia]:
        """Drain up to `num` items from a media iterator, reporting each one.

        Args:
            source (Iterator[PinterestMedia]): An iterator that yields PinterestMedia objects.
            num (int): Maximum number of items to collect from the source iterator.
            on_progress (Optional[Callable[[PinterestMedia], None]]): Optional callback function that is called with each new media item for progress reporting.
        Returns:
            List[PinterestMedia]: A list of collected PinterestMedia objects, up to the target count.
        """
        medias: List[PinterestMedia] = []
        for media in itertools.islice(source, num):
            medias.append(media)
            if on_progress is not None:
                on_progress(media)
        return medias

    def _iter_section(
        self,
        api: Api,
        min_resolution: Tuple[int, int],
        delay: float,
        caption_from_title: bool,
    ) -> Iterator[PinterestMedia]:
        board_id = api.get_board().get_board_id()
        if not api.section_slug:
            logger.error("Section slug is not set in the API client")
            return
        section_id = api.get_section_id_by_slug(board_id, api.section_slug)
        if not section_id:
            logger.warning(f"Section '{api.section_slug}' not found in board '{api.boardname}'")
            return
        logger.info(f"Scraping section '{api.section_slug}' (ID: {section_id})")
        yield from self._pump(
            lambda size, bm: self._get_section_images(
                api,
                section_id,
                size,
                bm,
                min_resolution,
                caption_from_title=caption_from_title,
            ),
            delay,
        )

    def _iter_board(
        self, api: Api, min_resolution: Tuple[int, int], delay: float, caption_from_title: bool
    ) -> Iterator[PinterestMedia]:
        board_info = api.get_board()
        board_id = board_info.get_board_id()
        logger.info(f"Scraping board (ID: {board_id}) with {board_info.get_pin_count()} pins")

        bookmarks = BookmarkManager(3)
        seen: set[str] = set()
        consecutive_empty = 0
        while True:
            try:
                batch, bookmarks = self._get_images_with_retry(
                    api, 50, bookmarks, min_resolution, board_id, caption_from_title
                )
                consecutive_empty = 0  # reset on successful fetch
            except EmptyResponseError as e:
                consecutive_empty += 1
                logger.warning(
                    f"Failed to fetch batch after retries: {e} (consecutive: {consecutive_empty}/3)"
                )
                if consecutive_empty >= 3:
                    logger.warning("Stopping after 3 consecutive empty responses")
                    return
                time.sleep(delay)
                continue
            except ValueError as e:
                logger.warning(f"Board scraping interrupted: {e}")
                return
            except Exception as e:
                logger.error(f"Unexpected error while scraping board: {e}", exc_info=self.verbose)
                raise

            for media in batch:
                if media.src not in seen:
                    seen.add(media.src)
                    yield media

            if "-end-" in bookmarks.get():
                logger.debug("Reached end of board stream")
                return
            time.sleep(delay)

    def _scrape_one_pin(
        self,
        api: Api,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> Optional[PinterestMedia]:
        """Scrape the requested Pinterest pin from a pin URL."""
        try:
            return self._get_main_pin(
                api,
                min_resolution,
                caption_from_title=caption_from_title,
            )
        except EmptyResponseError as e:
            logger.warning(f"Scraping interrupted: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while scraping pin: {e}", exc_info=self.verbose)
            raise

    def _create_api(self, url: str) -> Api:
        return Api(
            url,
            self.cookies,
            timeout=self.timeout,
            dump=self.dump,
        )

    def _get_main_pin(
        self,
        api: Api,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> PinterestMedia:
        """Fetch the requested pin from a pin URL."""
        try:
            response = api.get_main_image()
            response_data = response.resource_response.get("data")
            candidate_items = self._extract_pin_candidates(response_data)

            if candidate_items:
                matching_items = [
                    item for item in candidate_items if str(item.get("id")) == str(api.pin_id)
                ]
                items_to_parse = matching_items or candidate_items

                parsed_items = ResponseParser.from_responses(
                    items_to_parse,
                    min_resolution,
                    caption_from_title=caption_from_title,
                )

                if self.ensure_alt:
                    parsed_items = self._cull_no_alt(parsed_items)

                if parsed_items:
                    for item in parsed_items:
                        if str(item.id) == str(api.pin_id):
                            return item
                    return parsed_items[0]
        except HttpResponseError as e:
            logger.debug(f"Pin API lookup failed, falling back to page HTML: {e}")
        except EmptyResponseError:
            logger.debug("Pin API lookup returned no pin data, falling back to page HTML")
        except ValueError as e:
            logger.debug(f"Pin API lookup returned invalid data, falling back to page HTML: {e}")

        return self._get_main_pin_from_page(
            api,
            min_resolution,
            caption_from_title=caption_from_title,
        )

    def _extract_pin_candidates(self, data: Any) -> List[dict[str, Any]]:
        """Collect pin-like dictionaries from a Pinterest API response."""
        candidates: List[dict[str, Any]] = []

        def visit(value: Any) -> None:
            if isinstance(value, dict):
                if value.get("id") is not None and value.get("images", {}).get("orig"):
                    candidates.append(value)
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(data)
        return candidates

    def _get_main_pin_from_page(
        self,
        api: Api,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> PinterestMedia:
        """Parse pin metadata from the public pin page HTML."""
        pin_id = api.pin_id
        if pin_id is None:
            raise ValueError(f"Cannot parse pin page without a pin id (url={api.url!r})")

        html = api.get_pin_page()
        meta = self._extract_meta_tags(html)

        src = meta.get("og:image") or meta.get("twitter:image") or meta.get("twitter:image:src")
        if not src:
            raise EmptyResponseError("No image found in pin page metadata.")

        width = self._parse_int(meta.get("og:image:width"))
        height = self._parse_int(meta.get("og:image:height"))
        resolution = (width, height) if width and height else (0, 0)

        min_width, min_height = min_resolution
        if (min_width > 0 or min_height > 0) and resolution == (0, 0):
            raise EmptyResponseError(
                "Requested pin does not include dimensions required for min_resolution."
            )
        if width < min_width or height < min_height:
            raise EmptyResponseError("Requested pin does not meet min_resolution.")

        description = meta.get("og:description") or meta.get("description") or ""
        title = meta.get("og:title") or meta.get("twitter:title") or ""
        alt = title if caption_from_title and title else description

        if self.ensure_alt and not alt.strip():
            raise EmptyResponseError("Requested pin has no alt text.")

        video_stream = self._extract_video_stream_from_meta(
            meta
        ) or self._extract_video_stream_from_html(html)

        return PinterestMedia(
            id=int(pin_id),
            src=src,
            alt=alt,
            origin=api.url,
            resolution=resolution,
            video_stream=video_stream,
        )

    def _extract_meta_tags(self, html: str) -> dict[str, str]:
        """Extract HTML meta tags into a lowercase key-value mapping."""
        meta: dict[str, str] = {}

        for tag in re.findall(r"<meta\b[^>]*>", html, flags=re.IGNORECASE):
            attrs = {
                key.lower(): value
                for key, value in re.findall(
                    r'([A-Za-z_:.-]+)\s*=\s*["\']([^"\']*)["\']',
                    tag,
                )
            }
            key = attrs.get("property") or attrs.get("name")
            content = attrs.get("content")
            if key and content:
                meta[key.lower()] = content

        return meta

    def _extract_video_stream_from_meta(self, meta: dict[str, str]) -> Optional[VideoStreamInfo]:
        """Extract video metadata from page meta tags when available."""
        video_url = meta.get("og:video") or meta.get("og:video:url")
        if not video_url:
            return None

        width = self._parse_int(meta.get("og:video:width"))
        height = self._parse_int(meta.get("og:video:height"))

        return VideoStreamInfo(
            url=video_url,
            resolution=(width, height),
            duration=0,
        )

    def _extract_video_stream_from_html(self, html: str) -> Optional[VideoStreamInfo]:
        """Extract video URLs directly from raw page HTML."""
        html = html.replace("\\/", "/")
        candidates = re.findall(
            r'https?://[^"\'<>\s]+(?:\.m3u8|\.mp4)(?:\?[^"\'<>\s]*)?',
            html,
            flags=re.IGNORECASE,
        )
        candidates = [url for url in candidates if "pinimg.com" in url or "pinterest" in url]
        if not candidates:
            return None

        def score(url: str) -> tuple[int, int]:
            is_hls = 1 if ".m3u8" in url.lower() else 0
            return (is_hls, len(url))

        best_url = max(candidates, key=score)
        return VideoStreamInfo(
            url=best_url,
            resolution=(0, 0),
            duration=0,
        )

    def _parse_int(self, value: Optional[str]) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _download_and_save(
        self,
        scraped_outputs: List[PinterestMedia],
        output_dir: Optional[Union[str, Path]],
        download_streams: bool,
        skip_remux: bool,
        cache_path: Optional[Union[str, Path]],
        caption: Literal["txt", "json", "metadata", "none"],
    ) -> Optional[List[PinterestMedia]]:
        """Download scraped media and optionally save captions.

        Handles caching, console output, downloading, and caption embedding.
        Used by both scrape_and_download() and search_and_download().

        Args:
            scraped_outputs: List of scraped PinterestMedia objects.
            output_dir: Directory to store downloaded images. None to skip download.
            download_streams: Whether to download video streams if available.
            skip_remux: If True, output raw .ts file without ffmpeg remux.
            cache_path: Path to cache scraped data as json.
            caption: Caption mode for downloaded images.

        Returns:
            List of downloaded PinterestMedia objects, or None if output_dir is None.
        """
        items_as_dict = [item.to_dict() for item in scraped_outputs]

        if not output_dir and not cache_path:
            print("Scraped:")
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

        if caption in ("txt", "json"):
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

    # TODO: _get_section_images() and _get_images() share similar logic.
    # Consider extracting common pagination/parsing logic if a third similar
    # method is needed in the future.
    def _get_section_images(
        self,
        api: Api,
        section_id: str,
        batch_size: int,
        bookmarks: BookmarkManager,
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> Tuple[List[PinterestMedia], BookmarkManager]:
        """Fetch images from a board section.

        Args:
            api: Pinterest API client.
            section_id: Section ID to fetch pins from.
            batch_size: Number of pins to fetch per request.
            bookmarks: Bookmark manager for pagination.
            min_resolution: Minimum resolution filter (width, height).
            caption_from_title: Use title as caption.

        Returns:
            Tuple of (list of media items, updated bookmark manager).
        """
        response = api.get_board_section_pins(section_id, batch_size, bookmarks.get())

        response_data = response.resource_response.get("data", [])
        try:
            img_batch = ResponseParser.from_responses(
                response_data, min_resolution, caption_from_title=caption_from_title
            )
        except EmptyResponseError:
            return [], bookmarks

        if self.ensure_alt:
            img_batch = self._cull_no_alt(img_batch)

        bookmarks.add_all(response.get_bookmarks())
        return img_batch, bookmarks

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
            else api.get_board_pins(board_id, batch_size, bookmarks.get())
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

    def _display_images(self, images: List[PinterestMedia]):
        """Print scraped media URLs if verbosity is enabled."""
        for i, img in enumerate(images):
            if img.video_stream:
                logger.debug(f"({i + 1}) [VIDEO] {img.video_stream.url}")
            else:
                logger.debug(f"({i + 1}) {img.src}")
