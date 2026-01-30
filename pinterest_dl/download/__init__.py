# ruff: noqa: F401
"""Download module for media downloading.

This module provides HTTP client and concurrent download functionality.
"""

import warnings
from typing import Any, Dict, Literal, Union

import requests

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


def __getattr__(name: str):
    """Provide backward compatibility and lazy imports to avoid circular dependencies."""
    if name == "HttpClient":
        from pinterest_dl.download.http_client import HttpClient

        return HttpClient

    if name == "MediaDownloader":
        from pinterest_dl.download.downloader import MediaDownloader

        return MediaDownloader

    if name == "PinterestMediaDownloader":
        warnings.warn(
            "PinterestMediaDownloader has been renamed to MediaDownloader and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.download import MediaDownloader",
            DeprecationWarning,
            stacklevel=2,
        )
        from pinterest_dl.download.downloader import MediaDownloader

        return MediaDownloader

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
