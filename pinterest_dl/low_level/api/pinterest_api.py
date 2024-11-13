import re
from typing import List, Tuple

import requests
from git import Optional

from pinterest_dl.data_model.cookie import PinterestCookieJar
from pinterest_dl.low_level.api.endpoints import Endpoint
from pinterest_dl.low_level.api.pinterest_response import PinResponse
from pinterest_dl.low_level.ops.request_builder import RequestBuilder


class PinterestAPI:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    )

    def __init__(
        self, url: str, cookies: Optional[PinterestCookieJar] = None, timeout: float = 5
    ) -> None:
        """Pinterest API client.

        Args:
            url (str): Pinterest URL. (e.g. "https://www.pinterest.com/pin/123456789/")
            cookies (Optional[PinterestCookieJar], optional): Pinterest cookies. Defaults to None.
            timeout (float, optional): Request timeout in seconds. Defaults to 5.
        """
        self.url = url
        self.timeout = timeout
        try:
            self.pin_id = self._parse_pin_id(self.url)
        except ValueError:
            self.pin_id = None

        try:
            self.username, self.boardname = self._parse_board_url(self.url)
        except ValueError:
            self.username = None
            self.boardname = None

        self.endpoint = Endpoint()
        self.cookies = cookies if cookies else self._get_default_cookies(self.endpoint._BASE)

        # Initialize session
        self._session = requests.Session()
        self._session.cookies.update(self.cookies)  # Update session cookies
        self._session.headers.update({"User-Agent": self.USER_AGENT})
        self._req_builder = RequestBuilder()
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
        try:
            request_url = self._req_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Failed to request related images: {e}")

        try:
            response_raw_json = response_raw.json()
        except requests.exceptions.JSONDecodeError as e:
            print(response_raw.text)
            raise requests.JSONDecodeError(f"Failed to decode JSON response: {e}")

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

        try:
            request_url = self._req_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
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

        try:
            request_url = self._req_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Failed to request board: {e}")

        return PinResponse(request_url, response_raw.json())

    def get_board_feed(self, board_id: str, num: int, bookmark: List[str]) -> PinResponse:
        if num < 1:
            raise ValueError("Number of images must be greater than 0")
        if num > 50:
            raise ValueError("Number of images must not exceed 50 per request")

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

        try:
            request_url = self._req_builder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Failed to request board feed: {e}")

        return PinResponse(request_url, response_raw.json())

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
            raise ValueError(f"Invalid Pinterest URL: {url}")
        return result.group(1)

    @staticmethod
    def _parse_board_url(url: str) -> Tuple[str, str]:
        """Parse Pinterest board URL to username and boardname.

        Args:
            url (str): Pinterest board URL. (e.g. "https://www.pinterest.com/username/boardname/")

        Returns:
            result (str, str): (username, boardname)
        """
        result = re.search(r"https://www.pinterest.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)/?", url)
        if not result:
            raise ValueError(f"Invalid Pinterest board URL: {url}")
        return result.group(1), result.group(2)
