from typing import Dict

import requests

from pinterest_dl.exceptions import HlsDownloadError


class KeyCache:
    """Cache for HLS encryption keys."""

    def __init__(self, session: requests.Session, timeout: int = 10, max_retries: int = 3):
        """Initialize the key cache.

        Args:
            session (requests.Session): The requests session to use.
            timeout (int, optional): The timeout for requests in seconds. Defaults to 10.
            max_retries (int, optional): The maximum number of retries for failed requests. Defaults to 3.
        """
        self._cache: Dict[str, bytes] = {}
        self._session = session
        self._timeout = timeout
        self._max_retries = max_retries

    def get(self, url: str) -> bytes:
        """Fetch an HLS encryption key from the cache or download it.

        Args:
            url (str): The URL of the encryption key.

        Raises:
            HlsDownloadError: If the key cannot be fetched.

        Returns:
            bytes: The encryption key.
        """
        if url in self._cache:
            return self._cache[url]
        last_exc = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._session.get(url, timeout=self._timeout)
                if resp.status_code == 200:
                    self._cache[url] = resp.content
                    return resp.content
                last_exc = HlsDownloadError(f"HTTP {resp.status_code}")
            except requests.RequestException as e:
                last_exc = e
        raise HlsDownloadError(f"Failed to fetch key {url}: {last_exc}")
