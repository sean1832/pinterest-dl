import tempfile
from pathlib import Path
from typing import Iterable, List, Union

import requests
import requests.adapters

from pinterest_dl.common.logging import get_logger
from pinterest_dl.download.video.hls_processor import HlsProcessor

logger = get_logger(__name__)


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
        self.hls_processor = HlsProcessor(self.session, user_agent)

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

    def download_blob(
        self, url: str, output_path: Union[str, Path], chunk_size: int = 8192, **kwargs
    ) -> None:
        """Downloads the blob content from the specified URL and saves it to the output path.

        Args:
            url (str): The URL to download content from.
            output_path (Union[str, Path]): The file path where the content will be saved.
            chunk_size (int): Size of each chunk to read from the response. Defaults to 8192.
            **kwargs: Additional keyword arguments to be passed to the request.
        """
        with self.get(url, stream=True, **kwargs) as response:
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)

    def download_streams(
        self, url: str, output_path: Union[str, Path], skip_remux: bool = False
    ) -> Path:
        """Downloads a stream from the specified URL and saves it to the output path.

        Args:
            url (str): The URL to download the stream from.
            output_path (Union[str, Path]): The file path where the stream will be saved.
            skip_remux (bool): If True, output raw .ts file without ffmpeg remux.

        Returns:
            Path: The actual output path (may differ from input if skip_remux changes extension).
        """
        output_path = Path(output_path)

        # fetch and resolve playlist
        playlist = self.hls_processor.fetch_playlist(url)
        base_uri = playlist.base_uri or url.rsplit("/", 1)[0] + "/"
        if playlist.is_variant:
            media_url = self.hls_processor.resolve_variant(playlist, base_uri)
            playlist = self.hls_processor.fetch_playlist(media_url)
            base_uri = playlist.base_uri or media_url.rsplit("/", 1)[0] + "/"

        # enumerate segments
        segments = self.hls_processor.enumerate_segments(playlist, base_uri)
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            segment_paths: List[Path] = []
            iterator: Iterable = enumerate(segments)
            for index, segment in iterator:
                raw = self.hls_processor.download_segment(segment.uri)
                data = self.hls_processor.decrypt(segment, raw)
                segment_path = temp_dir / f"segment_{index:05d}.ts"
                self.hls_processor.write_segment_file(segment_path, data)
                segment_paths.append(segment_path)

            if skip_remux:
                # Binary concat to .ts file (no ffmpeg)
                output_ts = output_path.with_suffix(".ts")
                self.hls_processor.concat_to_ts(segment_paths, output_ts)
                return output_ts
            else:
                # Remux to .mp4 using ffmpeg, fallback to re-encode if remux fails
                output_mp4 = output_path.with_suffix(".mp4")
                concat_list = temp_dir / "concat_list.txt"
                self.hls_processor.build_concat_list(segment_paths, concat_list)
                try:
                    self.hls_processor.remux_to_mp4(concat_list, output_mp4)
                except Exception:
                    logger.warning("Remux failed, re-encoding video (this may take longer)...")
                    self.hls_processor.reencode_to_mp4(concat_list, output_mp4)
                return output_mp4
