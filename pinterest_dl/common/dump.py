"""Utilities for dumping API request and response data to JSON files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests


class RequestDumper:
    """Utility class for dumping HTTP request and response data to JSON files."""

    def __init__(self, dump_dir: Union[str, Path] = ".dump"):
        """Initialize the dumper with a directory for dump files.

        Args:
            dump_dir (Union[str, Path], optional): Directory to save dump files. Defaults to ".dump".
        """
        self.dump_dir = Path(dump_dir)
        self.dump_dir.mkdir(parents=True, exist_ok=True)

    def dump_request_response(
        self,
        request_url: str,
        response: requests.Response,
        filename: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Dump request and response data to a JSON file.

        Args:
            request_url (str): The URL that was requested.
            response (requests.Response): The response object.
            filename (Optional[str], optional): Custom filename. If None, uses timestamp. Defaults to None.
            request_data (Optional[Dict[str, Any]], optional): Additional request data to include. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata to include. Defaults to None.

        Returns:
            Path: Path to the created dump file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if filename is None:
            filename = f"request_{timestamp}.json"
        elif not filename.endswith(".json"):
            filename = f"{filename}.json"

        dump_path = self.dump_dir / filename

        # Build dump data structure
        dump_data = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "url": request_url,
                "method": response.request.method if response.request else "UNKNOWN",
                "headers": dict(response.request.headers) if response.request else {},
            },
            "response": {
                "status_code": response.status_code,
                "reason": response.reason,
                "headers": dict(response.headers),
                "url": response.url,
                "elapsed_ms": response.elapsed.total_seconds() * 1000,
            },
        }

        # Add request data if provided
        if request_data:
            dump_data["request"]["data"] = request_data

        # Add request body if it exists
        if response.request and response.request.body:
            try:
                dump_data["request"]["body"] = (
                    response.request.body.decode("utf-8")
                    if isinstance(response.request.body, bytes)
                    else response.request.body
                )
            except (UnicodeDecodeError, AttributeError):
                dump_data["request"]["body"] = "<binary data>"

        # Add response content
        try:
            dump_data["response"]["json"] = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            dump_data["response"]["text"] = response.text[:5000]  # Limit text size

        # Add metadata if provided
        if metadata:
            dump_data["metadata"] = metadata

        # Write to file
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=4, ensure_ascii=False)

        return dump_path

    def dump_api_call(
        self,
        endpoint: str,
        options: Dict[str, Any],
        response: requests.Response,
        filename: Optional[str] = None,
    ) -> Path:
        """Dump Pinterest API call data to a JSON file.

        Args:
            endpoint (str): The API endpoint used.
            options (Dict[str, Any]): The options/parameters passed to the API.
            response (requests.Response): The response object.
            filename (Optional[str], optional): Custom filename. Defaults to None.

        Returns:
            Path: Path to the created dump file.
        """
        metadata = {
            "api_endpoint": endpoint,
            "api_options": options,
        }

        return self.dump_request_response(
            request_url=response.url,
            response=response,
            filename=filename,
            metadata=metadata,
        )

    def dump_error(
        self,
        error: Exception,
        request_url: Optional[str] = None,
        response: Optional[requests.Response] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """Dump error information along with request/response data.

        Args:
            error (Exception): The exception that occurred.
            request_url (Optional[str], optional): The URL that was requested. Defaults to None.
            response (Optional[requests.Response], optional): The response object if available. Defaults to None.
            filename (Optional[str], optional): Custom filename. Defaults to None.

        Returns:
            Path: Path to the created dump file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if filename is None:
            filename = f"error_{timestamp}.json"
        elif not filename.endswith(".json"):
            filename = f"{filename}.json"

        dump_path = self.dump_dir / filename

        dump_data = {
            "timestamp": datetime.now().isoformat(),
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }

        if request_url:
            dump_data["request"] = {"url": request_url}

        if response:
            dump_data["response"] = {
                "status_code": response.status_code,
                "reason": response.reason,
                "headers": dict(response.headers),
                "url": response.url,
            }

            try:
                dump_data["response"]["json"] = response.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                dump_data["response"]["text"] = response.text[:5000]

        # Write to file
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=4, ensure_ascii=False)

        return dump_path


# Singleton instance for convenient access
_default_dumper: Optional[RequestDumper] = None


def get_dumper(dump_dir: Union[str, Path] = ".dump") -> RequestDumper:
    """Get or create the default dumper instance.

    Args:
        dump_dir (Union[str, Path], optional): Directory for dump files. Defaults to ".dump".

    Returns:
        RequestDumper: The dumper instance.
    """
    global _default_dumper
    if _default_dumper is None:
        _default_dumper = RequestDumper(dump_dir)
    return _default_dumper


def dump_request_response(
    request_url: str,
    response: requests.Response,
    filename: Optional[str] = None,
    **kwargs,
) -> Path:
    """Convenience function to dump request/response using the default dumper.

    Args:
        request_url (str): The URL that was requested.
        response (requests.Response): The response object.
        filename (Optional[str], optional): Custom filename. Defaults to None.
        **kwargs: Additional arguments passed to RequestDumper.dump_request_response().

    Returns:
        Path: Path to the created dump file.
    """
    dumper = get_dumper()
    return dumper.dump_request_response(request_url, response, filename, **kwargs)
