from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyexiv2
from PIL import Image


class PinterestImage:
    def __init__(
        self,
        src: str,
        alt: Optional[str],
        origin: Optional[str],
        is_stream: bool,
    ) -> None:
        """Pinterest Image data.

        Args:
            src (str): Image source url.
            alt (Optional[str]): Image alt text.
            origin (Optional[str]): Pinterest pin url.
        """
        self.src = src
        self.alt = alt
        self.origin = origin
        self.is_stream = is_stream
        self.local_path: Optional[Path] = None
        self.local_resolution: Optional[Tuple[int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "alt": self.alt,
            "is_stream": self.is_stream,
            "origin": self.origin,
            "resolution": {
                "x": self.local_resolution[0] if self.local_resolution else None,
                "y": self.local_resolution[1] if self.local_resolution else None,
            },
        }

    def set_local(self, path: str | Path) -> None:
        self.local_path = Path(path)
        with Image.open(self.local_path) as img:
            self.local_resolution = img.size

    def prune_local(self, resolution: Tuple[int, int], verbose: bool = False) -> bool:
        if not self.local_path or not self.local_resolution:
            if verbose:
                print(f"Local path or size not set for {self.src}")
            return False
        if (
            self.local_resolution is not None
            and resolution is not None
            and self.local_resolution < resolution
        ):
            self.local_path.unlink()
            if verbose:
                print(
                    f"Removed {self.local_path}, resolution: {self.local_resolution} < {resolution}"
                )
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
    def from_dict(data: Dict[str, Any]) -> "PinterestImage":
        return PinterestImage(
            data["src"], data["alt"], data["origin"], data.get("is_stream", False)
        )

    @classmethod
    def from_responses(
        cls, response_data: List[Dict[str, Any]], min_resolution: Tuple[int, int]
    ) -> List["PinterestImage"]:
        if not response_data:
            raise ValueError("No data found in response.")
        min_width, min_height = min_resolution

        images: List["PinterestImage"] = []
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

            alt = item.get("auto_alt_text", "")
            origin = f"https://www.pinterest.com/pin/{item.get('id', '')}/"
            is_stream = bool(item.get("should_open_in_stream", False))

            # if the item is a stream, try to resolve the best video URL
            if is_stream:
                video_url = cls._get_best_video_url(item)
                if not video_url:
                    # if stream is expected but cannot resolve a video variant, skip
                    continue
                src = video_url

            images.append(cls(src, alt, origin, is_stream=is_stream))

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
    def _get_best_video_url(cls, data_raw: Dict[str, Any]) -> Optional[str]:
        video_variant = cls._choose_highest_resolution(cls._extract_video_list(data_raw))
        if not video_variant:
            return None
        return video_variant.get("url")

    def __str__(self) -> str:
        return f"PinterestImage(src: {self.src}, alt: {self.alt}, origin: {self.origin}, is_stream: {self.is_stream})"
