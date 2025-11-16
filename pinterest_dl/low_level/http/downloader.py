from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List, Optional, TypeVar

from pinterest_dl.data_model.pinterest_media import PinterestMedia
from pinterest_dl.exceptions import DownloadError
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
        items: List[PinterestMedia],
        output_dir: Path,
        worker: Callable[[PinterestMedia, Path], Optional[T]],
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
                    # Store error with item identifier for better error reporting
                    item_id = getattr(item, "id", None) or getattr(item, "url", str(item)[:50])
                    errors[item] = (item_id, e)
                    if fail_fast:
                        # cancel others
                        for f in future_to_meta:
                            if not f.done():
                                f.cancel()
                        raise
                finally:
                    done += 1
                    self.report(done, total)

        if errors:
            error_lines = [f"  - {item_id}: {str(e)}" for item_id, e in errors.values()]
            summary = "\n".join(error_lines)
            raise DownloadError(
                f"Failed to download {len(errors)} out of {total} items:\n{summary}"
            )

        # type: ignore  # we've ensured no None if no exception
        return [r for r in results if r is not None]


class PinterestMediaDownloader:
    """Handles downloading media files from Pinterest"""

    def __init__(
        self,
        user_agent: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """Initialize the PinterestMediaDownloader with user agent and optional parameters."""
        self.http_client = HttpClient(user_agent, timeout, max_retries)
        self.progress_callback = progress_callback

    def download(
        self, pin_media: PinterestMedia, output_dir: Path, download_streams: bool = False
    ) -> Path:
        """Download a media file (video stream or image) to the given directory.

        Args:
            pin_media (PinterestMedia): Media descriptor.
            output_dir (Path): Destination directory.
            download_streams (bool): If True and a video stream exists, prefer that over the image.

        Returns:
            Path: Path to the downloaded file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        media_base = output_dir / f"{pin_media.id}"

        if download_streams and pin_media.video_stream:
            stream_url = pin_media.video_stream.url
            target_path = media_base.with_suffix(".mp4")

            if Path(stream_url).suffix.lower() == ".mp4":
                # Direct MP4 download
                self.http_client.download_blob(stream_url, target_path, chunk_size=2048)
            else:
                # HLS stream: download and remux to MP4
                self.http_client.download_streams(stream_url, target_path)
            return target_path

        # Fallback to image
        image_url = pin_media.src
        ext = Path(image_url).suffix.lower()
        if not ext:
            ext = ".jpg"  # reasonable default if extension is missing
        image_path = media_base.with_suffix(ext)
        self.http_client.download_blob(image_url, image_path, chunk_size=2048)
        return image_path

    def download_concurrent(
        self,
        media_list: List[PinterestMedia],
        output_dir: Path,
        download_streams: bool = False,
        max_workers: int = 8,
        fail_fast: bool = False,
    ) -> List[Path]:
        """Download a list of PinterestMedia objects concurrently.

        Args:
            media_list (List[PinterestMedia]): List of PinterestMedia objects to download.
            output_dir (Path): Directory to save downloaded media.
            download_streams (bool): If True, prefer video streams over images.
            max_workers (int): Maximum number of worker threads.
            fail_fast (bool): If True, stop on first download failure.

        Returns:
            List[Path]: List of paths to the downloaded media files.
        """

        def worker(media: PinterestMedia, outdir: Path) -> Path:
            return self.download(media, outdir, download_streams)

        stream_coordinator = _ConcurrentCoordinator(progress_callback=self.progress_callback)
        return stream_coordinator.run(
            items=media_list,
            output_dir=output_dir,
            worker=worker,
            max_workers=max_workers,
            fail_fast=fail_fast,
        )
