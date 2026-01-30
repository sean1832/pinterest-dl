"""Pinterest media data model.

This module contains pure data classes for Pinterest media objects.
Parsing and file operations are handled by separate modules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class VideoStreamInfo:
    """Data class to hold video stream information.

    Attributes:
        url: Direct URL to video stream.
        resolution: Video resolution as (width, height) tuple.
        duration: Video duration in seconds.
    """

    url: str
    resolution: Tuple[int, int]
    duration: int


class PinterestMedia:
    """Pinterest media data container.

    Pure data class representing a Pinterest image or video pin.
    For parsing API responses, use ResponseParser.from_responses().
    For file operations, use MediaFileHandler methods.
    """

    def __init__(
        self,
        id: int,
        src: str,
        alt: Optional[str],
        origin: Optional[str],
        resolution: Tuple[int, int],
        video_stream: Optional[VideoStreamInfo] = None,
    ) -> None:
        """Initialize Pinterest media object.

        Args:
            id: Unique identifier for the media.
            src: Image source URL.
            alt: Image alt text or caption.
            origin: Pinterest pin URL.
            resolution: Image resolution as (width, height).
            video_stream: Optional video stream information if available.
        """
        self.id = id
        self.src = src
        self.alt = alt
        self.origin = origin
        self.resolution = resolution
        self.video_stream = video_stream
        self.local_path: Optional[Path] = None

    def set_local_path(self, path: str | Path) -> None:
        """Set the local file path for downloaded media.

        Args:
            path: Local filesystem path to the media file.
        """
        self.local_path = Path(path)

    def to_dict(self) -> Dict[str, Any]:
        """Convert media object to dictionary representation.

        Returns:
            Dictionary containing all media attributes.
        """
        # Treat (0, 0) resolution as None (invalid resolution)
        has_valid_resolution = self.resolution and self.resolution != (0, 0)

        data = {
            "id": self.id,
            "src": self.src,
            "alt": self.alt,
            "origin": self.origin,
            "resolution": {
                "x": self.resolution[0] if has_valid_resolution else None,
                "y": self.resolution[1] if has_valid_resolution else None,
            },
        }
        if self.video_stream:
            data["media_stream"] = {
                "video": {
                    "url": self.video_stream.url,
                    "resolution": self.video_stream.resolution,
                    "duration": self.video_stream.duration,
                }
            }
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PinterestMedia":
        """Create PinterestMedia object from dictionary.

        Args:
            data: Dictionary containing media attributes.

        Returns:
            Reconstructed PinterestMedia object.
        """
        video_stream = None
        if "media_stream" in data and "video" in data["media_stream"]:
            video_data = data["media_stream"]["video"]
            video_stream = VideoStreamInfo(
                url=video_data["url"],
                resolution=tuple(video_data["resolution"]),
                duration=video_data["duration"],
            )

        return PinterestMedia(
            id=data["id"],
            src=data["src"],
            alt=data["alt"],
            origin=data["origin"],
            resolution=(
                data["resolution"]["x"],
                data["resolution"]["y"],
            )
            if "resolution" in data
            else (0, 0),
            video_stream=video_stream,
        )

    def __str__(self) -> str:
        """String representation of media object."""
        return (
            f"PinterestMedia("
            f"src: {self.src}, "
            f"alt: {self.alt}, "
            f"origin: {self.origin}, "
            f"resolution: {self.resolution}, "
            f"video_stream: {self.video_stream}"
            f")"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return self.__str__()
