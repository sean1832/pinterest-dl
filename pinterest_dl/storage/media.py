"""Pinterest media file operations.

This module provides functions for Pinterest media file I/O operations, including
saving images, embedding metadata, and managing local files.
Separated from the data model to maintain clear separation of concerns.
"""

from pathlib import Path
from typing import Tuple

import pyexiv2
from PIL import Image

from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.exceptions import UnsupportedMediaTypeError

logger = get_logger(__name__)


def set_local_resolution(media: PinterestMedia, path: Path) -> None:
    """Set the local resolution of the media from file.

    Args:
        media: PinterestMedia object to update.
        path: Local file path to the media.

    Raises:
        UnsupportedMediaTypeError: If file format is not supported.
        FileNotFoundError: If file does not exist.
    """
    # Skip resolution setting for video files
    if path.suffix.lower() in {".mp4", ".mkv", ".avi", ".mov"}:
        return

    # Validate image format
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        raise UnsupportedMediaTypeError(
            f"Unsupported image format for {path}. Supported formats: jpg, jpeg, png, gif, webp."
        )

    # Set local path if not already set
    if not media.local_path:
        media.local_path = path

    # Verify file exists
    if not media.local_path.exists():
        raise FileNotFoundError(f"Local path {media.local_path} does not exist.")

    # Read and set resolution from image
    with Image.open(media.local_path) as img:
        media.resolution = (img.width, img.height)


def prune_local(
    media: PinterestMedia,
    resolution: Tuple[int, int],
    verbose: bool = False,
) -> bool:
    """Remove local file if resolution is below threshold.

    Args:
        media: PinterestMedia object with local file.
        resolution: Minimum resolution threshold as (width, height).
        verbose: Whether to log removal message.

    Returns:
        True if file was removed, False otherwise.
    """
    if not media.local_path or not media.resolution:
        if verbose:
            logger.debug(f"Local path or size not set for {media.src}")
        return False

    if media.resolution < resolution:
        media.local_path.unlink()
        if verbose:
            logger.debug(
                f"Removed {media.local_path}, resolution: {media.resolution} < {resolution}"
            )
        return True

    return False


def write_exif_comment(media: PinterestMedia, comment: str) -> None:
    """Write comment to EXIF metadata.

    Args:
        media: PinterestMedia object with local file.
        comment: Comment text to embed.

    Raises:
        ValueError: If local path is not set.
    """
    if not media.local_path:
        raise ValueError("Local path not set.")

    with pyexiv2.Image(str(media.local_path)) as img:
        img.modify_exif({"Exif.Image.XPComment": comment})


def write_exif_subject(media: PinterestMedia, subject: str) -> None:
    """Write subject to EXIF metadata.

    Args:
        media: PinterestMedia object with local file.
        subject: Subject text to embed.

    Raises:
        ValueError: If local path is not set.
    """
    if not media.local_path:
        raise ValueError("Local path not set.")

    with pyexiv2.Image(str(media.local_path)) as img:
        img.modify_exif({"Exif.Image.XPSubject": subject})
