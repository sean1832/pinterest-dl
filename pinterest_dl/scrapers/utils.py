"""Shared utility functions for Pinterest scrapers.

This module contains common functionality used by both API and WebDriver scrapers.
Functions are module-level to avoid unnecessary inheritance hierarchies.
"""

import json
import logging
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import tqdm

from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.download import USER_AGENT, downloader
from pinterest_dl.exceptions import ExecutableNotFoundError, UnsupportedMediaTypeError
from pinterest_dl.storage.media import MediaFileHandler
from pinterest_dl.utils import ensure_executable
from pinterest_dl.utils.progress_bar import TqdmProgressBarCallback

logger = logging.getLogger(__name__)


def download_media(
    media: List[PinterestMedia],
    output_dir: Union[str, Path],
    download_streams: bool,
) -> List[PinterestMedia]:
    """Download media from Pinterest using given URLs and fallbacks.

    Args:
        media: List of PinterestMedia objects to download.
        output_dir: Directory to store downloaded media.
        download_streams: Whether to download video streams.

    Returns:
        List of PinterestMedia objects with local paths set.
    """
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dl = downloader.PinterestMediaDownloader(
        user_agent=USER_AGENT,
        timeout=10,
        max_retries=3,
        progress_callback=TqdmProgressBarCallback(description="Downloading Media"),
    )

    if download_streams:
        try:
            ensure_executable.ensure_executable("ffmpeg")
        except ExecutableNotFoundError as e:
            logger.warning(f"ffmpeg not found: {e}. Falling back to images.")
            print(f"Warning: {e}. Video streams will not be downloaded, falling back to images.")
            download_streams = False

    try:
        local_paths = dl.download_concurrent(media, output_dir, download_streams)
    except Exception as e:
        # Log the error and re-raise for CLI to handle
        logger.error(f"Download failed: {e}")
        raise

    for item, path in zip(media, local_paths):
        item.set_local_path(path)
        if item.resolution is None or item.resolution == (0, 0):
            try:
                MediaFileHandler.set_local_resolution(item, path)
            except FileNotFoundError:
                print(f"Warning: Local path '{path}' does not exist. Skipping resolution set.")
            except UnsupportedMediaTypeError as ve:
                print(f"Warning: {ve}. Skipping resolution set for '{path}'.")

    return media


def add_captions_to_file(
    images: List[PinterestMedia],
    output_dir: Union[str, Path],
    extension: Literal["txt", "json"] = "txt",
    verbose: bool = False,
) -> None:
    """Add captions to downloaded images and save them to a file.

    Args:
        images: List of PinterestMedia objects to add captions to.
        output_dir: Directory to save image captions.
        extension: File extension for the captions.
            'txt' for alt text in separate files,
            'json' for full image data.
        verbose: Enable verbose logging.
    """
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Saving captions to {output_dir}...")

    for img in tqdm.tqdm(images, desc="Captioning to file", disable=verbose):
        if not img.local_path:
            continue

        if extension == "json":
            with open(output_dir / f"{img.local_path.stem}.json", "w") as f:
                f.write(json.dumps(img.to_dict(), indent=4))
        elif extension == "txt":
            if img.alt:
                with open(output_dir / f"{img.local_path.stem}.txt", "w") as f:
                    f.write(img.alt)
            else:
                if verbose:
                    print(f"No alt text for {img.local_path}")
        else:
            raise ValueError("Invalid file extension. Use 'txt' or 'json'.")

        if verbose:
            print(f"Caption saved for {img.local_path}: '{img.alt}'")


def add_captions_to_meta(
    images: List[PinterestMedia],
    verbose: bool = False,
) -> None:
    """Add captions and origin information to image metadata.

    Args:
        images: List of PinterestMedia objects to add captions to.
        verbose: Enable verbose logging.
    """
    for index in tqdm.tqdm(
        range(len(images)),
        desc="Captioning to metadata",
        disable=verbose,
    ):
        img: Optional[PinterestMedia] = None
        try:
            img = images[index]

            if img.video_stream:
                continue  # Skip streams for metadata captioning

            if not img.local_path:
                continue

            if img.local_path.suffix == ".gif":
                if verbose:
                    print(f"Skipping captioning for {img.local_path} (GIF)")
                continue

            if img.origin:
                MediaFileHandler.write_exif_comment(img, img.origin)
                if verbose:
                    print(f"Origin added to {img.local_path}: '{img.origin}'")

            if img.alt:
                MediaFileHandler.write_exif_subject(img, img.alt)
                if verbose:
                    print(f"Caption added to {img.local_path}: '{img.alt}'")

        except Exception as e:
            # Log metadata errors but continue processing other images
            if img and img.local_path:
                logger.warning(
                    f"Failed to add metadata to {img.local_path}: {e}",
                    exc_info=verbose,
                )
                if verbose:
                    print(f"Error captioning {img.local_path}: {e}")
            else:
                logger.warning(
                    f"Failed to add metadata to image at index {index}: {e}",
                    exc_info=verbose,
                )


def prune_images(
    images: List[PinterestMedia],
    min_resolution: Tuple[int, int],
    verbose: bool = False,
) -> List[PinterestMedia]:
    """Return images that meet the resolution requirement.

    Args:
        images: Original list of PinterestMedia.
        min_resolution: Minimum (width, height).
        verbose: If True, logs how many were pruned.

    Returns:
        List of PinterestMedia that passed the resolution check.
    """
    kept: List[PinterestMedia] = []
    for img in images:
        if not MediaFileHandler.prune_local(img, min_resolution, verbose):
            kept.append(img)

    pruned_count = len(images) - len(kept)
    if verbose:
        print(f"Pruned ({pruned_count}) images")

    return kept
