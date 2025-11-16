from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyexiv2
from PIL import Image

from pinterest_dl.exceptions import EmptyResponseError, UnsupportedMediaTypeError


@dataclass
class VideoStreamInfo:
    """Data class to hold video stream information."""

    url: str
    resolution: Tuple[int, int]
    duration: int


class PinterestMedia:
    def __init__(
        self,
        id: int,
        src: str,
        alt: Optional[str],
        origin: Optional[str],
        resolution: Tuple[int, int],
        video_stream: Optional[VideoStreamInfo] = None,
    ) -> None:
        """Pinterest Image data.

        Args:
            id (int): Unique identifier for the media.
            src (str): Image source url.
            alt (Optional[str]): Image alt text.
            origin (Optional[str]): Pinterest pin url.
            resolution (Tuple[int, int]): Image resolution as (width, height).
            video_stream (Optional[VideoStreamInfo]): Optional video stream information, if available.
        """
        self.id = id
        self.src = src
        self.alt = alt
        self.origin = origin
        self.resolution = resolution
        self.video_stream = video_stream
        self.local_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "src": self.src,
            "alt": self.alt,
            "origin": self.origin,
            "resolution": {
                "x": self.resolution[0] if self.resolution else None,
                "y": self.resolution[1] if self.resolution else None,
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

    def set_local_path(self, path: str | Path) -> None:
        self.local_path = Path(path)

    def set_local_resolution(self, path: str | Path) -> None:
        """Set the local resolution of the media.

        Args:
            path (str | Path): Local file path to the media.
        """
        if Path(path).suffix.lower() not in {".mp4", ".mkv", ".avi", ".mov"}:
            return None  # If not a video, skip resolution setting
        if Path(path).suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            raise UnsupportedMediaTypeError(
                f"Unsupported image format for {path}. Supported formats: jpg, jpeg, png, gif, webp."
            )
        if not self.local_path:
            self.local_path = Path(path)
        if not self.local_path.exists():
            raise FileNotFoundError(f"Local path {self.local_path} does not exist.")
        with Image.open(self.local_path) as img:
            self.resolution = (img.width, img.height)

    def prune_local(self, resolution: Tuple[int, int], verbose: bool = False) -> bool:
        if not self.local_path or not self.resolution:
            if verbose:
                print(f"Local path or size not set for {self.src}")
            return False
        if self.resolution is not None and resolution is not None and self.resolution < resolution:
            self.local_path.unlink()
            if verbose:
                print(f"Removed {self.local_path}, resolution: {self.resolution} < {resolution}")
            return True
        return False

    def meta_write_comment(self, comment: str) -> None:
        if not self.local_path:
            raise ValueError("Local path not set.")
        with pyexiv2.Image(str(self.local_path)) as img:
            img.modify_exif({"Exif.Image.XPComment": comment})

    def meta_write_subject(self, subject: str) -> None:
        if not self.local_path:
            raise ValueError("Local path not set.")
        with pyexiv2.Image(str(self.local_path)) as img:
            img.modify_exif({"Exif.Image.XPSubject": subject})

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PinterestMedia":
        return PinterestMedia(
            data["id"],
            data["src"],
            data["alt"],
            data["origin"],
            (data["resolution"]["x"], data["resolution"]["y"]) if "resolution" in data else (0, 0),
            data.get("is_stream", False),
        )

    @classmethod
    def from_responses(
        cls,
        response_data: List[Dict[str, Any]],
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> List["PinterestMedia"]:
        """Extract PinterestMedia objects from response data.

        Args:
            response_data (List[Dict[str, Any]]): List of dictionaries containing image data.
            min_resolution (Tuple[int, int]): Minimum resolution as (width, height) to filter images.
            caption_from_title (bool): Whether to use the image title as the caption.

        Raises:
            EmptyResponseError: If no valid data is found.

        Returns:
            List[PinterestMedia]: A list of PinterestMedia objects.
        """
        if not response_data:
            raise EmptyResponseError("No data found in response.")
        min_width, min_height = min_resolution

        images: List["PinterestMedia"] = []
        for item in response_data:
            if not isinstance(item, dict):
                continue

            # base image
            orig = item.get("images", {}).get("orig")
            if not orig:
                continue

            # extract width and height from the original image metadata
            try:
                width = int(orig.get("width", 0))
                height = int(orig.get("height", 0))
            except (TypeError, ValueError):
                continue

            # skip images that are smaller than the minimum resolution
            if width < min_width or height < min_height:
                continue

            # set the source URL and other attributes
            src = orig.get("url")
            if not src:
                continue
            id = item.get("id", 0)  # Use 'id' from the item, default to 0 if not present
            if caption_from_title:
                # use title as alt
                alt = item.get(
                    "title",
                    item.get("auto_alt_text", ""),  # <- fallback to auto_alt_text
                )
            else:
                # use auto_alt_text as alt
                alt = item.get("auto_alt_text", "")
            origin = f"https://www.pinterest.com/pin/{id}/"

            is_stream = bool(item.get("should_open_in_stream", False))
            # if the item is a stream, try to resolve the best video URL
            video_stream = None
            if is_stream:
                stream_variant = cls._get_best_video_variant(item)
                if not stream_variant:
                    continue
                if not stream_variant.get("url", None):
                    continue
                video_stream = VideoStreamInfo(
                    url=stream_variant["url"],
                    resolution=(stream_variant.get("width", 0), stream_variant.get("height", 0)),
                    duration=stream_variant.get("duration", 0),
                )

            images.append(
                cls(
                    id,
                    src,
                    alt,
                    origin,
                    resolution=(width, height),
                    video_stream=video_stream,
                )
            )

        return images

    @staticmethod
    def _extract_video_list(data_raw: Dict[str, Any]) -> Dict[str, Dict]:
        try:
            video_list = data_raw["story_pin_data"]["pages"][0]["blocks"][0]["video"]["video_list"]
        except (KeyError, IndexError, TypeError):
            return {}
        if not isinstance(video_list, dict):
            return {}
        return video_list  # mapping of arbitrary keys to video metadata

    @staticmethod
    def _choose_highest_resolution(video_list: Dict[str, Dict]) -> Optional[Dict[str, Any]]:
        if not video_list:
            return None

        def resolution(entry: Dict[str, Any]) -> int:
            return (entry.get("width") or 0) * (entry.get("height") or 0)

        return max(video_list.values(), key=resolution)

    @classmethod
    def _get_best_video_variant(cls, data_raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        video_variant = cls._choose_highest_resolution(cls._extract_video_list(data_raw))
        if not video_variant:
            return None
        return video_variant

    def __str__(self) -> str:
        return f"PinterestMedia(src: {self.src}, alt: {self.alt}, origin: {self.origin}, resolution: {self.resolution}, video_stream: {self.video_stream})"
