import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, TypeVar

from pinterest_dl.exceptions import DownloadError
from pinterest_dl.low_level.hls import HlsProcessor
from pinterest_dl.low_level.http import HttpClient

ProgressCallback = Callable[[int, int], None]  # downloaded_segments, total_segments

T = TypeVar("T")  # result type


class _ConcurrentCoordinator:
    def __init__(
        self,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.progress_callback = progress_callback

    def report(self, done: int, total: int) -> None:
        if self.progress_callback:
            self.progress_callback(done, total)

    def run(
        self,
        items: List[str],
        output_dir: Path,
        worker: Callable[[str, Path], Optional[T]],
        max_workers: int,
        fail_fast: bool = False,
    ) -> List[T]:
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(items)
        done = 0
        results: List[Optional[T]] = [None] * total
        errors: Dict[str, Exception] = {}

        def submit_tasks(executor: ThreadPoolExecutor):
            futures = {}
            for idx, item in enumerate(items):
                fut = executor.submit(worker, item, output_dir)
                futures[fut] = (idx, item)
            return futures

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_meta = submit_tasks(executor)
            for future in as_completed(future_to_meta):
                idx, item = future_to_meta[future]
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as e:
                    errors[item] = e
                    if fail_fast:
                        # cancel others
                        for f in future_to_meta:
                            if not f.done():
                                f.cancel()
                        raise e from e
                finally:
                    done += 1
                    self.report(done, total)

        if errors:
            summary = "\n".join(f"{url}: {str(e)}" for url, e in errors.items())
            raise DownloadError(f"Errors occurred during concurrent run:\n{summary}")

        # type: ignore  # we've ensured no None if no exception
        return [r for r in results if r is not None]


class StreamDownloader:
    """Orchestrates downloading an HLS video stream"""

    def __init__(
        self,
        user_agent: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """Initialize the StreamDownloader with user agent and optional parameters."""
        self.http_client = HttpClient(user_agent, timeout, max_retries)
        self.hls_processor = HlsProcessor(self.http_client.session, user_agent)
        self.progress_callback = progress_callback

    def download(self, url: str, output_dir: Path) -> Path:
        """High-level method to download an HLS video stream and remux to MP4

        Args:
            url (str): The URL of the HLS video stream to download.
            output_dir (Path): The directory to save the downloaded video.

        Returns:
            Path: The path to the downloaded MP4 video file.
        """
        url_path = Path(url)
        video_path = output_dir / f"{url_path.stem}.mp4"
        output_dir.mkdir(parents=True, exist_ok=True)
        if url_path.suffix.lower() == ".mp4":
            # if the URL is already an MP4 file, just download it directly
            self.http_client.download_blob(url, video_path, chunk_size=2048)
            return video_path

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
                output_path = temp_dir / f"segment_{index:05d}.ts"
                self.hls_processor.write_segment_file(output_path, data)
                segment_paths.append(output_path)

            # build concat list and combine segments
            concat_list = temp_dir / "concat_list.txt"
            self.hls_processor.build_concat_list(segment_paths, concat_list)
            output_ts = output_dir / "output.ts"
            self.hls_processor.ffmpeg_concat(concat_list, output_ts)
            self.hls_processor.remux_to_mp4(output_ts, video_path)

        return video_path

    def download_concurrent(
        self,
        urls: List[str],
        output_dir: Path,
        max_workers: int = 8,
        fail_fast: bool = False,
    ) -> List[Path]:
        """Download images concurrently from a list of URLs.

        Args:
            urls (List[str]): List of image URLs to download.
            output_dir (Path): Directory to save downloaded images.
            max_workers (int, optional): Maximum number of worker threads. Defaults to 8.
        """

        def worker(url: str, outdir: Path) -> Path:
            return self.download(url, outdir)

        stream_coordinator = _ConcurrentCoordinator(progress_callback=self.progress_callback)

        return stream_coordinator.run(
            items=urls,
            output_dir=output_dir,
            worker=worker,
            max_workers=max_workers,
            fail_fast=fail_fast,
        )


class BlobDownloader:
    """Handles downloading blobs from URLs"""

    def __init__(
        self,
        user_agent: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """Initialize the BlobDownloader with user agent and optional parameters."""
        self.http_client = HttpClient(user_agent, timeout, max_retries)
        self.progress_callback = progress_callback

    def download(self, url: str, output_dir: Path, chunk_size: int = 2048) -> Path:
        """Download a blob from a URL and save it to the specified directory.

        Args:
            url (str): The URL of the blob to download.
            output_dir (Path): The directory to save the downloaded blob.
            chunk_size (int): Size of each chunk to read from the response.

        Returns:
            Path: The path to the downloaded blob file.
        """
        response = self.http_client.get(url, stream=True)
        response.raise_for_status()

        filename = Path(url).name
        outfile = output_dir / filename

        with open(outfile, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)

        return outfile

    def download_concurrent(
        self,
        urls: List[str],
        output_dir: Path,
        chunk_size: int = 2048,
        max_workers: int = 8,
        fail_fast: bool = False,
    ) -> List[Path]:
        """Download images concurrently from a list of URLs.

        Args:
            urls (List[str]): List of image URLs to download.
            output_dir (Path): Directory to save downloaded images.
            chunk_size (int, optional): Size of each chunk to read from the response. Defaults to 2048.
            max_workers (int, optional): Maximum number of worker threads. Defaults to 8.
            fail_fast (bool, optional): If True, stop on first download failure. Defaults to False.

        Returns:
            List[Path]: List of paths to the downloaded images.
        """

        def worker(url: str, outdir: Path) -> Path:
            return self.download(url, outdir, chunk_size=chunk_size)

        stream_coordinator = _ConcurrentCoordinator(progress_callback=self.progress_callback)
        return stream_coordinator.run(
            items=urls,
            output_dir=output_dir,
            worker=worker,
            max_workers=max_workers,
            fail_fast=fail_fast,
        )
