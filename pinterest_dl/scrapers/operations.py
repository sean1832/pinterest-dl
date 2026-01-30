"""Shared utility functions for Pinterest scrapers.

This module contains common functionality used by both API and WebDriver scrapers.
Functions are module-level to avoid unnecessary inheritance hierarchies.
"""

import json
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import tqdm

from pinterest_dl.common import ensure_executable
from pinterest_dl.common.logging import get_logger
from pinterest_dl.common.progress_bar import TqdmProgressBarCallback
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.download import USER_AGENT
from pinterest_dl.download.downloader import MediaDownloader
from pinterest_dl.exceptions import ExecutableNotFoundError, UnsupportedMediaTypeError
from pinterest_dl.storage import media as media_storage

logger = get_logger(__name__)


def download_media(
    media: List[PinterestMedia],
    output_dir: Union[str, Path],
    download_streams: bool,
    skip_remux: bool = False,
) -> List[PinterestMedia]:
    """Download media from Pinterest using given URLs and fallbacks.

    Args:
        media: List of PinterestMedia objects to download.
        output_dir: Directory to store downloaded media.
        download_streams: Whether to download video streams.
        skip_remux: If True, output raw .ts file without ffmpeg remux.

    Returns:
        List of PinterestMedia objects with local paths set.
    """
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dl = MediaDownloader(
        user_agent=USER_AGENT,
        timeout=10,
        max_retries=3,
        progress_callback=TqdmProgressBarCallback(description="Downloading Media"),
    )

    if download_streams and not skip_remux:
        try:
            ensure_executable.ensure_executable("ffmpeg")
        except ExecutableNotFoundError as e:
            logger.warning(f"ffmpeg not found: {e}. Falling back to images.")
            logger.info(
                "Hint: Use --skip-remux to download videos as raw .ts files without ffmpeg."
            )
            download_streams = False

    try:
        local_paths = dl.download_concurrent(media, output_dir, download_streams, skip_remux)
        logger.info(f"Successfully downloaded {len(local_paths)}/{len(media)} media items")
    except Exception as e:
        # Log the error and re-raise for CLI to handle
        logger.error(f"Download operation failed: {type(e).__name__}: {e}")
        raise

    for item, path in zip(media, local_paths):
        item.set_local_path(path)
        if item.resolution is None or item.resolution == (0, 0):
            try:
                media_storage.set_local_resolution(item, path)
            except FileNotFoundError:
                logger.warning(f"Local path '{path}' does not exist. Skipping resolution set.")
            except UnsupportedMediaTypeError as ve:
                logger.warning(f"{ve}. Skipping resolution set for '{path}'.")

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
        logger.debug(f"Saving captions to {output_dir}...")

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
                    logger.debug(f"No alt text for {img.local_path}")
        else:
            raise ValueError("Invalid file extension. Use 'txt' or 'json'.")

        if verbose:
            logger.debug(f"Caption saved for {img.local_path}: '{img.alt}'")


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
                    logger.debug(f"Skipping captioning for {img.local_path} (GIF)")
                continue

            if img.origin:
                media_storage.write_exif_comment(img, img.origin)
                if verbose:
                    logger.debug(f"Origin added to {img.local_path}: '{img.origin}'")

            if img.alt:
                media_storage.write_exif_subject(img, img.alt)
                if verbose:
                    logger.debug(f"Caption added to {img.local_path}: '{img.alt}'")

        except Exception as e:
            # Log metadata errors but continue processing other images
            if img and img.local_path:
                logger.warning(
                    f"Failed to add metadata to {img.local_path}: {e}",
                    exc_info=verbose,
                )
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
        if not media_storage.prune_local(img, min_resolution, verbose):
            kept.append(img)

    pruned_count = len(images) - len(kept)
    if verbose:
        logger.debug(f"Pruned ({pruned_count}) images")

    return kept
