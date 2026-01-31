# ruff: noqa: F401
"""Download module for media downloading.

This module provides HTTP client and concurrent download functionality.
"""

from typing import Any, Dict, Literal, Union

import requests

from .downloader import MediaDownloader
from .http_client import HttpClient

__all__ = ["HttpClient", "MediaDownloader", "fetch"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
)


def fetch(
    url: str, response_format: Literal["json", "text"] = "text"
) -> Union[Dict[str, Any], str]:
    if isinstance(url, str):
        req = requests.get(url)
        req.raise_for_status()
        if response_format == "json":
            return req.json()  # JSON response may contain more complex structures
        elif response_format == "text":
            return req.text
    else:
        raise ValueError("URL must be a string.")
