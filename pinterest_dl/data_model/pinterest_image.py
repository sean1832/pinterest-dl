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
        fallback_urls: Optional[str | List[str]] = None,
    ) -> None:
        """Pinterest Image data.

        Args:
            src (str): Image source url.
            alt (Optional[str]): Image alt text.
            origin (Optional[str]): Pinterest pin url.
            fallback_urls (Optional[str  |  List[str]], optional): Fallback image urls. Defaults to None.
        """
        self.src = src
        self.alt = alt
        self.origin = origin
        self.fallback_urls: List[str] = self._set_fallback(fallback_urls) if fallback_urls else []
        self.local_path: Optional[Path] = None
        self.local_size: Optional[Tuple[int, int]] = None

    def _set_fallback(self, urls: str | List[str]) -> List[str]:
        if isinstance(urls, str):
            return [urls]
        elif isinstance(urls, list):
            return urls
        else:
            raise ValueError("Invalid fallback urls")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "alt": self.alt,
            "origin": self.origin,
            "fallback_urls": self.fallback_urls,
        }

    def set_local(self, path: str | Path) -> None:
        self.local_path = Path(path)
        with Image.open(self.local_path) as img:
            self.local_size = img.size

    def prune_local(self, resolution: Tuple[int, int], verbose: bool = False) -> bool:
        if not self.local_path or not self.local_size:
            if verbose:
                print(f"Local path or size not set for {self.src}")
            return False
        if self.local_size and self.local_size < resolution:
            self.local_path.unlink()
            if verbose:
                print(f"Removed {self.local_path}, resolution: {self.local_size} < {resolution}")
            return True
        return False

    def write_comment(self, comment: str) -> None:
        if not self.local_path:
            raise ValueError("Local path not set.")
        with pyexiv2.Image(str(self.local_path)) as img:
            img.modify_exif({"Exif.Image.XPComment": comment})

    def write_subject(self, subject: str) -> None:
        if not self.local_path:
            raise ValueError("Local path not set.")
        with pyexiv2.Image(str(self.local_path)) as img:
            img.modify_exif({"Exif.Image.XPSubject": subject})

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PinterestImage":
        return PinterestImage(data["src"], data["alt"], data["origin"], data["fallback_urls"])

    def __str__(self) -> str:
        return f"PinterestImage(src: {self.src}, alt: {self.alt}, origin: {self.origin}, fallback_urls: {self.fallback_urls})"