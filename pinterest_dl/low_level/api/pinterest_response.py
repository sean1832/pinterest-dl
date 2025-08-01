from typing import List, Union

from pinterest_dl.exceptions import (
    BoardIDException,
    BookmarkException,
    HttpResponseError,
    PinCountException,
    PinResponseError,
)
from pinterest_dl.low_level.http.request_builder import RequestBuilder


class PinResponse:
    def __init__(self, request_url: str, raw_response: dict) -> None:
        self.raw_response = raw_response
        self.request_url = RequestBuilder().url_decode(request_url)

        try:
            self.resource_response: dict = self.raw_response["resource_response"]
        except KeyError:
            raise PinResponseError(
                "Invalid response format: 'resource_response' key not found.", raw_response
            )

        # validate network error
        try:
            self.error_info = self.resource_response["error"]
            self._handle_failed_request_response()
        except KeyError:
            # no error info, proceed with normal response
            self.error_info = {}

        try:
            self.resource: dict = self.raw_response["resource"]
        except KeyError:
            raise PinResponseError(
                "Invalid response format: 'resource' key not found.", raw_response
            )

        try:
            self.data: Union[dict, List[dict]] = self.resource_response["data"]
        except KeyError:
            raise PinResponseError("Invalid response format: 'data' key not found.", raw_response)

        # endpoint name
        self.endpoint_name = self.resource_response.get("endpoint_name", None)

    def get_bookmarks(self) -> List[str]:
        try:
            return self.resource["options"]["bookmarks"]
        except KeyError:
            raise BookmarkException("Failed to parse bookmarks from response", self.raw_response)

    def get_board_id(self) -> str:
        data = self.data
        if data is None:
            raise BoardIDException("No data in response", self.raw_response)

        if not isinstance(data, dict):
            raise BoardIDException(
                "Expected a single board object, got list or other type", self.raw_response
            )

        try:
            board_id = data["id"]
        except KeyError:
            raise BoardIDException("Missing 'id' field in response data", self.raw_response)

        if not isinstance(board_id, str) or not board_id:
            raise BoardIDException(f"Invalid board id: {board_id!r}", self.raw_response)

        return board_id

    def get_pin_count(self) -> int:
        data = self.data
        if data is None:
            raise PinCountException("No data in response", self.raw_response)

        if not isinstance(data, dict):
            raise PinCountException(
                f"Expected single board object, got {type(data).__name__}", self.raw_response
            )

        try:
            pin_count = data["pin_count"]
        except KeyError:
            raise PinCountException("Missing 'pin_count' field in response", self.raw_response)

        if not isinstance(pin_count, int):
            raise PinCountException(
                f"Invalid type for pin_count: expected int, got {type(pin_count).__name__}",
                self.raw_response,
            )

        return pin_count

    def _handle_failed_request_response(self) -> None:
        self.http_status = self.error_info.get("http_status", None)
        self.code = self.error_info.get("code", None)
        self.message = self.error_info.get("message", None)
        self.status = self.error_info.get("status", None)

        raise HttpResponseError(
            self.message or "Unknown error",
            status_code=self.http_status,
            dump_data={
                "error": self.error_info,
                "request_url": self.request_url,
                "response_raw": self.raw_response,
            },
        )
