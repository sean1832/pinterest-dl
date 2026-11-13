"""Pinterest media file operations.

This module provides functions for Pinterest media file I/O operations, including
saving images, embedding metadata, and managing local files.
Separated from the data model to maintain clear separation of concerns.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple

from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.exceptions import UnsupportedMediaTypeError

if TYPE_CHECKING:
    import pyexiv2  # type: ignore
    from PIL import Image as PILImage  # type: ignore

logger = get_logger(__name__)

# Module-level lazy imports (checked only once)
_pyexiv2: Optional[Any] = None
_pyexiv2_available: Optional[bool] = None

_PIL: Optional[Any] = None
_PIL_available: Optional[bool] = None


def _get_pyexiv2() -> Any:
    """Lazy import pyexiv2, caching the result.

    Returns:
        pyexiv2 module if available.

    Raises:
        ImportError: If pyexiv2 is not installed.
    """
    global _pyexiv2, _pyexiv2_available

    if _pyexiv2_available is None:
        try:
            import pyexiv2  # type: ignore

            _pyexiv2 = pyexiv2
            _pyexiv2_available = True
        except ImportError:
            _pyexiv2_available = False

    if not _pyexiv2_available:
        raise ImportError(
            "pyexiv2 is required for EXIF operations. "
            "Install it with: pip install pyexiv2"
        )

    return _pyexiv2


def _get_PIL() -> Any:
    """Lazy import PIL, caching the result.

    Returns:
        PIL module if available.

    Raises:
        ImportError: If Pillow is not installed.
    """
    global _PIL, _PIL_available

    if _PIL_available is None:
        try:
            from PIL import Image

            _PIL = Image
            _PIL_available = True
        except ImportError:
            _PIL_available = False

    if not _PIL_available:
        raise ImportError(
            "Pillow is required for image operations. "
            "Install it with: pip install pillow"
        )

    return _PIL


def set_local_resolution(media: PinterestMedia, path: Path) -> None:
    """Set the local resolution of the media from file.

    Args:
        media: PinterestMedia object to update.
        path: Local file path to the media.

    Raises:
        UnsupportedMediaTypeError: If file format is not supported.
        FileNotFoundError: If file does not exist.
        ImportError: If Pillow is not installed.
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
    Image = _get_PIL()
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

    width, height = media.resolution
    min_width, min_height = resolution
    if width < min_width or height < min_height:
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
        ImportError: If pyexiv2 is not installed.
    """
    pyexiv2 = _get_pyexiv2()

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
        ImportError: If pyexiv2 is not installed.
    """
    pyexiv2 = _get_pyexiv2()

    if not media.local_path:
        raise ValueError("Local path not set.")

    with pyexiv2.Image(str(media.local_path)) as img:
        img.modify_exif({"Exif.Image.XPSubject": subject})
