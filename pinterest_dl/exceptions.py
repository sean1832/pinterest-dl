import json
from pathlib import Path
from typing import Optional


class InvalidBrowser(Exception):
    """Exception raised when the browser is not supported or invalid."""


class ExecutableNotFoundError(Exception):
    """Exception raised when a required binary is not found in the system PATH."""


class UnsupportedMediaTypeError(Exception):
    """Exception raised when the media type is not supported."""


class DownloadError(Exception):
    """Exception raised for errors in the download process."""


class HlsDownloadError(Exception):
    """Exception raised for errors in the HLS download process."""


class PinterestAPIError(Exception):
    """Base exception for Pinterest API errors."""


class HttpResponseError(PinterestAPIError):
    """Network-level failure when performing an HTTP request."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, dump_data: Optional[dict] = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.dump_data = dump_data

    def dump(self, dump_file: Path) -> Path:
        """Dump error data to a file."""
        if self.dump_data:
            dump_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dump_file, "w") as f:
                json.dump(self.dump_data, f, indent=4)
            return dump_file
        return Path()


class UrlParseError(PinterestAPIError):
    """Exception raised when a Pinterest URL cannot be parsed."""


class InvalidPinterestUrlError(UrlParseError):
    def __init__(self, url: str):
        super().__init__(f"Invalid Pinterest URL: {url}")
        self.url = url


class InvalidSearchUrlError(UrlParseError):
    def __init__(self, url: str):
        super().__init__(f"Invalid Pinterest search URL: {url}")
        self.url = url


class InvalidBoardUrlError(UrlParseError):
    def __init__(self, url: str):
        super().__init__(f"Invalid Pinterest board URL: {url}")
        self.url = url


class PinResponseError(PinterestAPIError):
    """Base exception for Pinterest response errors."""

    def __init__(self, message: str, raw_response: Optional[dict] = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


class BoardIDException(PinResponseError):
    """Exception raised when a board ID is not found in the response data."""


class PinCountException(PinResponseError):
    """Exception raised when the pin count is not found in the response data."""


class BookmarkException(PinResponseError):
    """Exception raised when a bookmark operation fails."""


class EmptyResponseError(PinterestAPIError):
    """Exception raised when the API response is empty."""
