"""Request URL building utilities for Pinterest API.

This module provides functions for building Pinterest API request URLs
with proper encoding and query parameters.
"""

import json
import time
from urllib.parse import quote_plus, unquote_plus, urlencode


def build_post(options: dict, source_url: str = "/", context: dict = None) -> str:
    """Build a POST request query string.

    Args:
        options: Request options dict.
        source_url: Source URL for the request. Defaults to "/".
        context: Optional context dict.

    Returns:
        URL-encoded query string.
    """
    return url_encode(
        {
            "source_url": source_url,
            "data": json.dumps({"options": options, "context": context}),
            "_": "%s" % int(time.time() * 1000),
        }
    )


def build_get(endpoint: str, options: dict, source_url: str = "/", context: dict = None) -> str:
    """Build a GET request URL with query parameters.

    Args:
        endpoint: API endpoint path.
        options: Request options dict.
        source_url: Source URL for the request. Defaults to "/".
        context: Optional context dict. Defaults to empty dict.

    Returns:
        Complete URL with encoded query parameters.
    """
    if context is None:
        context = {}

    query = url_encode(
        {
            "source_url": source_url,
            "data": json.dumps({"options": options, "context": context}),
            "_": "%s" % int(time.time() * 1000),
        }
    )

    url = f"{endpoint}?{query}"
    return url


def url_encode(query: str | dict) -> str:
    """URL-encode a query string or dict.

    Args:
        query: String or dict to encode.

    Returns:
        URL-encoded string with spaces as %20.
    """
    if isinstance(query, str):
        query = quote_plus(query)
    else:
        query = urlencode(query)
    query = query.replace("+", "%20")
    return query


def url_decode(query: str) -> str:
    """Decode a URL-encoded string.

    Args:
        query: URL-encoded string.

    Returns:
        Decoded string.
    """
    return unquote_plus(query)
