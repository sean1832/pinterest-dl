import json
import time  # noqa: F401
from typing import List, NoReturn, Optional  # noqa: F401

from pinterest_dl.low_level.ops.request_builder import RequestBuilder


class PinResponse:
    def __init__(self, request_url: str, raw_response: dict) -> None:
        self.raw_response = raw_response
        self.request_url = RequestBuilder().url_decode(request_url)

        self.resource_response: dict = self.raw_response.get("resource_response", None)
        if self.resource_response is None:
            # All pinterest responses should have a resource_response key regardless of success or failure
            raise ValueError("resource_response is None. Invalid pinterest response.")

        # validate network error
        self.error_info = self.resource_response.get("error", None)
        if self.error_info is not None:
            self._handle_failed_request_response()

        self.resource: dict = self.raw_response.get("resource", None)
        if self.resource is None:
            raise ValueError("resource is None.")

        self.data: Optional[dict | List[dict]] = self.resource_response.get("data", None)
        if self.data is None:
            raise ValueError("data is None.")

        # endpoint name
        self.endpoint_name = self.resource_response.get("endpoint_name", None)

    def get_bookmarks(self) -> List[str]:
        try:
            return self.resource["options"]["bookmarks"]
        except KeyError:
            raise KeyError("Failed to parse bookmarks from response")

    def get_board_id(self) -> str:
        try:
            if self.data is None:
                raise KeyError("Failed to parse board id from response")
            if isinstance(self.data, list):
                raise ValueError("Multiple boards found in response. Expected single board.")

            board_id = self.data.get("id", None)
            return board_id
        except KeyError or ValueError:
            # self.dump_at(f"failed_{self.endpoint_name}_{time.time()}.json")
            raise KeyError("Failed to parse board id from response")
        except Exception as e:
            # self.dump_at(f"failed_{self.endpoint_name}_{time.time()}.json")
            raise e

    def get_pin_count(self) -> int:
        try:
            if self.data is None:
                raise KeyError("Failed to parse board id from response")
            if isinstance(self.data, list):
                raise ValueError("Multiple boards found in response. Expected single board.")

            pin_count = self.data.get("pin_count", None)
            return pin_count
        except KeyError or ValueError:
            # self.dump_at(f"failed_{self.endpoint_name}_{time.time()}.json")
            raise KeyError("Failed to parse pin count from response")
        except Exception as e:
            # self.dump_at(f"failed_{self.endpoint_name}_{time.time()}.json")
            raise e

    def _handle_failed_request_response(self) -> None:
        self.http_status = self.error_info.get("http_status", None)
        self.code = self.error_info.get("code", None)
        self.message: str = self.error_info.get("message", None)
        self.status = self.error_info.get("status", None)

        # # clean message for file name
        # message_name = self.message.lower().replace(" ", "-").replace(".", "")
        # dump_file = f"failure_{message_name}_{time.time()}.json"

        # data = {
        #     "error": self.error_info,
        #     "request_url": self.request_url,
        #     "response_raw": self.raw_response,
        # }

        # self._dump_data_at(dump_file, data)
        raise ValueError(
            f"Invalid response (http_status: {self.http_status}, message: {self.message})"
        )

    # def _handle_parsing_error(self, field: str, error: Exception) -> NoReturn:
    #     data = {
    #         "error": {
    #             "message": f"{str(error)}",
    #             "field": field,
    #         },
    #         "request_url": self.request_url,
    #         "response_raw": self.raw_response,
    #     }
    #     filename = f"failed_parsing-error_{field}_{time.time()}.json"
    #     self._dump_data_at(filename, data)
    #     raise AttributeError(
    #         f"Failed to parse '{field}' in response. See dumped file for details at './{filename}'"
    #     )

    def _get_status(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "status": self.status,
            "endpoint_name": self.endpoint_name,
        }

    def dump_at(self, path: str) -> None:
        with open(path, "w") as file:
            file.write(json.dumps(self.raw_response, indent=4))

    def _dump_data_at(self, path: str, data: dict) -> None:
        with open(path, "w") as file:
            file.write(json.dumps(data, indent=4))
