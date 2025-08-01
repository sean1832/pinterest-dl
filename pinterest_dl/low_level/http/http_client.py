from typing import Iterable

import requests
import requests.adapters


class HttpClient:
    def __init__(
        self,
        user_agent: str,
        timeout: float = 10,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ):
        """Initializes the HttpClient with the given parameters.

        Args:
            user_agent (str): User-Agent string to be used in HTTP requests.
            timeout (float, optional): Timeout duration for HTTP requests in seconds. Defaults to 10.
            max_retries (int, optional): Maximum number of retry attempts for failed requests. Defaults to 3.
            backoff_factor (float, optional): Backoff factor for retrying requests. Defaults to 0.3.
        """
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        retries = requests.adapters.Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> requests.Response:
        """Sends a GET request to the specified URL.

        Args:
            url (str): The URL to send the GET request to.
            **kwargs: Additional keyword arguments to be passed to the request.

        Returns:
            requests.Response: The response object from the GET request.
        """
        resp = self.session.get(url, timeout=self.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def iter_content(
        self, url: str, chunk_size: int = 2048, decode_unicode=False
    ) -> Iterable[bytes]:
        """Sends a GET request and returns an iterator over the response content.

        Args:
            url (str): The URL to send the GET request to.
            chunk_size (int, optional): Size of each chunk in bytes. Defaults to 2048.
            decode_unicode (bool, optional): Whether to decode the content to unicode. Defaults to False.

        Yields:
            bytes: The response content in chunks.
        """
        resp = self.get(url, stream=True)
        for chunk in resp.iter_content(chunk_size, decode_unicode):
            if chunk:
                yield chunk
