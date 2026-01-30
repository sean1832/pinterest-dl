import re
from typing import List, Optional, Tuple

import requests

from pinterest_dl.api.endpoints import Endpoint
from pinterest_dl.api.pinterest_response import PinResponse
from pinterest_dl.common.dump import RequestDumper
from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.cookies import CookieJar
from pinterest_dl.download import request_builder
from pinterest_dl.exceptions import (
    InvalidBoardUrlError,
    InvalidPinterestUrlError,
    InvalidSearchUrlError,
)

logger = get_logger(__name__)


class Api:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    )

    def __init__(
        self,
        url: str,
        cookies: Optional[CookieJar] = None,
        timeout: float = 5,
        dump: Optional[str] = None,
    ) -> None:
        """Pinterest API client.

        Args:
            url (str): Pinterest URL. (e.g. "https://www.pinterest.com/pin/123456789/")
            cookies (Optional[CookieJar], optional): Pinterest cookies. Defaults to None.
            timeout (float, optional): Request timeout in seconds. Defaults to 5.
            dump (Optional[str], optional): Directory to dump API requests/responses. Defaults to None (disabled).
        """
        self.url = url
        self.timeout = timeout
        self.dumper = RequestDumper(dump) if dump else None
        try:
            self.pin_id = self._parse_pin_id(self.url)
        except InvalidPinterestUrlError:
            self.pin_id = None
            try:
                self.query = self._parse_search_query(self.url)
            except InvalidSearchUrlError:
                # Neither pin nor search URL - will try board parsing next
                self.query = None

        try:
            self.username, self.boardname = self._parse_board_url(self.url)
        except InvalidBoardUrlError:
            self.username = None
            self.boardname = None

        self.endpoint = Endpoint()
        self.cookies = cookies if cookies else self._get_default_cookies(self.endpoint._BASE)

        # Initialize session
        self._session = requests.Session()
        self._session.cookies.update(self.cookies)  # Update session cookies
        self._session.headers.update({"User-Agent": self.USER_AGENT})
        self._session.headers.update(
            {"x-pinterest-pws-handler": "www/pin/[id].js"}
        )  # required since 2025-03-07. See https://github.com/sean1832/pinterest-dl/issues/30
        self.is_pin = bool(self.pin_id)

    def get_related_images(self, num: int, bookmark: List[str]) -> PinResponse:
        if not self.pin_id:
            raise ValueError("Invalid Pinterest URL")
        if num < 1:
            raise ValueError("Number of images must be greater than 0")
        if num > 50:
            raise ValueError("Number of images must not exceed 50 per request")

        endpoint = self.endpoint.GET_RELATED_MODULES
        source_url = f"/pin/{self.pin_id}/"
        options = {
            "pin_id": f"{self.pin_id}",
            "context_pin_ids": [],
            "page_size": num,
            "bookmarks": bookmark,
            "search_query": "",
            "source": "deep_linking",
            "top_level_source": "deep_linking",
            "top_level_source_depth": 1,
            "is_pdp": False,
        }
        request_url = None
        try:
            request_url = request_builder.build_get(endpoint, options, source_url)
            logger.debug(f"Fetching related images for pin {self.pin_id} (page_size={num})")
            response_raw = self._session.get(request_url, timeout=self.timeout)
            response_raw.raise_for_status()

            # Dump API call if enabled
            if self.dumper:
                dump_path = self.dumper.dump_api_call(
                    endpoint=endpoint,
                    options=options,
                    response=response_raw,
                    filename=f"get_related_images_pin_{self.pin_id}",
                )
                logger.info(f"API dump saved to: {dump_path}")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for pin {self.pin_id}: {e}")

            # Dump error if enabled
            if self.dumper:
                dump_path = self.dumper.dump_error(
                    error=e,
                    request_url=request_url,
                    filename=f"error_get_related_images_pin_{self.pin_id}",
                )
                logger.info(f"Error dump saved to: {dump_path}")

            raise requests.RequestException(f"Failed to request related images: {e}")

        try:
            response_raw_json = response_raw.json()
        except requests.exceptions.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to decode JSON response: {e}. Response: {response_raw.text}"
            )

        return PinResponse(request_url, response_raw_json)

    def get_main_image(self) -> PinResponse:
        if not self.pin_id:
            raise ValueError("Invalid Pinterest URL")
        endpoint = self.endpoint.GET_MAIN_IMAGE

        source_url = f"/pin/{self.pin_id}/"
        options = {
            "url": "/v3/users/me/recent/engaged/pin/stories/",
            "data": {
                "fields": "pin.description,pin.id,pin.images[236x]",
                "pin_preview_count": 1,
            },
        }

        request_url = None
        try:
            request_url = request_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)

            # Dump API call if enabled
            if self.dumper:
                dump_path = self.dumper.dump_api_call(
                    endpoint=endpoint,
                    options=options,
                    response=response_raw,
                    filename=f"get_main_image_pin_{self.pin_id}",
                )
                logger.info(f"API dump saved to: {dump_path}")

        except requests.exceptions.RequestException as e:
            if self.dumper:
                dump_path = self.dumper.dump_error(
                    error=e,
                    request_url=request_url,
                    filename=f"error_get_main_image_pin_{self.pin_id}",
                )
                logger.info(f"Error dump saved to: {dump_path}")
            raise requests.RequestException(f"Failed to request main image: {e}")

        return PinResponse(request_url, response_raw.json())

    def get_board(self) -> PinResponse:
        if not self.username or not self.boardname:
            username, boardname = self._parse_board_url(self.url)
        else:
            username, boardname = self.username, self.boardname

        endpoint = self.endpoint.GET_BOARD_RESOURCE

        source_url = f"/{username}/{boardname}/"
        options = {
            "username": username,
            "slug": boardname,
            "field_set_key": "detailed",
        }

        request_url = None
        try:
            request_url = request_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)

            # Dump API call if enabled
            if self.dumper:
                dump_path = self.dumper.dump_api_call(
                    endpoint=endpoint,
                    options=options,
                    response=response_raw,
                    filename=f"get_board_{username}_{boardname}",
                )
                logger.info(f"API dump saved to: {dump_path}")

        except requests.exceptions.RequestException as e:
            if self.dumper:
                dump_path = self.dumper.dump_error(
                    error=e,
                    request_url=request_url,
                    filename=f"error_get_board_{username}_{boardname}",
                )
                logger.info(f"Error dump saved to: {dump_path}")
            raise requests.RequestException(f"Failed to request board: {e}")

        return PinResponse(request_url, response_raw.json())

    def get_board_feed(self, board_id: str, num: int, bookmark: List[str]) -> PinResponse:
        self._validate_num(num)

        board_url = f"/{self.username}/{self.boardname}/"

        endpoint = self.endpoint.GET_BOARD_FEED_RESOURCE
        source_url = board_url
        options = {
            "board_id": board_id,
            "board_url": board_url,
            "page_size": num,
            "bookmarks": bookmark,
            "currentFilter": -1,
            "field_set_key": "react_grid_pin",  # "react_grid_pin" | "grid_item" | "board_pin"
            "filter_section_pins": True,  # flag to tell the server to filter section pins
            "sort": "default",  # "default" | "newest" | "oldest" | "popular"
            "layout": "default",  # "default" | "custom"
            "redux_normalize_feed": True,  # flag to tell the server to return the data in a format that is easy to use in the frontend
        }

        request_url = None
        try:
            request_url = request_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)

            # Dump API call if enabled
            if self.dumper:
                dump_path = self.dumper.dump_api_call(
                    endpoint=endpoint,
                    options=options,
                    response=response_raw,
                    filename=f"get_board_feed_{board_id}",
                )
                logger.info(f"API dump saved to: {dump_path}")

        except requests.exceptions.RequestException as e:
            if self.dumper:
                dump_path = self.dumper.dump_error(
                    error=e,
                    request_url=request_url,
                    filename=f"error_get_board_feed_{board_id}",
                )
                logger.info(f"Error dump saved to: {dump_path}")
            raise requests.RequestException(f"Failed to request board feed: {e}")

        return PinResponse(request_url, response_raw.json())

    def get_search(self, num: int, bookmark: List[str]) -> PinResponse:
        if not self.query:
            raise ValueError("Invalid Pinterest search URL")
        self._validate_num(num)

        source_url = f"/search/pins/?q={self.query}rs=typed"

        endpoint = self.endpoint.GET_SEARCH_RESOURCE
        options = {
            "appliedProductFilters": "---",
            "auto_correction_disabled": False,
            "bookmarks": bookmark,
            "page_size": num,
            "query": self.query,
            "redux_normalize_feed": True,
            "rs": "typed",  # is user typed or not
            "scope": "pins",
            "source_url": source_url,
        }

        request_url = None
        try:
            request_url = request_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)

            # Dump API call if enabled
            if self.dumper:
                dump_path = self.dumper.dump_api_call(
                    endpoint=endpoint,
                    options=options,
                    response=response_raw,
                    filename=f"get_search_{self.query}",
                )
                logger.info(f"API dump saved to: {dump_path}")

        except requests.exceptions.RequestException as e:
            if self.dumper:
                dump_path = self.dumper.dump_error(
                    error=e,
                    request_url=request_url,
                    filename=f"error_get_search_{self.query}",
                )
                logger.info(f"Error dump saved to: {dump_path}")
            raise requests.RequestException(f"Failed to request search: {e}")
        try:
            json_response = response_raw.json()
        except requests.exceptions.JSONDecodeError as e:
            # Include response snippet in exception for debugging
            response_snippet = response_raw.text[:500] if response_raw.text else "<empty>"
            raise requests.JSONDecodeError(
                f"Failed to decode JSON response: {e}. Response snippet: {response_snippet}"
            )
        return PinResponse(request_url, json_response)

    def _validate_num(self, num: int) -> None:
        if num < 1:
            raise ValueError("Number of images must be greater than 0")
        if num > 50:
            raise ValueError("Number of images must not exceed 50 per request")

    @staticmethod
    def _get_default_cookies(url: str) -> dict:
        try:
            response = requests.get(url)
            return response.cookies.get_dict()
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Failed to get default cookies: {e}")

    @staticmethod
    def _parse_pin_id(url: str) -> str:
        result = re.search(r"pin/(\d+)/", url)
        if not result:
            raise InvalidPinterestUrlError(f"Invalid Pinterest URL: {url}")
        return result.group(1)

    @staticmethod
    def _parse_search_query(url: str) -> str:
        # /search/pins/?q={query} - query can contain Unicode chars or percent-encoded text
        result = re.search(r"/search/pins/\?q=([^&]+)", url)
        if not result:
            raise InvalidSearchUrlError(f"Invalid Pinterest search URL: {url}")
        query = result.group(1)
        return request_builder.url_decode(query)

    @staticmethod
    def _parse_board_url(url: str) -> Tuple[str, str]:
        """Parse Pinterest board URL to username and boardname.

        Args:
            url (str): Pinterest board URL. (e.g. "https://www.pinterest.com/username/boardname/")

        Returns:
            result (str, str): (username, boardname)
        """
        result = re.search(
            r"https://(?:[a-z0-9-]+\.)?pinterest\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)/?$", url
        )
        if not result:
            raise InvalidBoardUrlError(f"Invalid Pinterest board URL: {url}")
        return result.group(1), result.group(2)
