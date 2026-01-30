from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class SegmentInfo:
    index: int
    uri: str  # full resolved URL
    method: Optional[Literal["AES-128"]]  # e.g., "AES-128" or None
    key_uri: Optional[str]
    iv: Optional[bytes]  # explicit IV or None
    media_sequence: int
