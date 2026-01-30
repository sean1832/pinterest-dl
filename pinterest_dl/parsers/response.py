"""Pinterest API response parser.

This module handles parsing Pinterest API responses into PinterestMedia objects.
Separated from the data model to maintain clear separation of concerns.
"""

from typing import Any, Dict, List, Optional, Tuple

from pinterest_dl.domain.media import PinterestMedia, VideoStreamInfo
from pinterest_dl.exceptions import EmptyResponseError


class ResponseParser:
    """Parses Pinterest API responses into PinterestMedia objects."""

    @classmethod
    def from_responses(
        cls,
        response_data: List[Dict[str, Any]],
        min_resolution: Tuple[int, int],
        caption_from_title: bool = False,
    ) -> List[PinterestMedia]:
        """Extract PinterestMedia objects from response data.

        Args:
            response_data: List of dictionaries containing image data from Pinterest API.
            min_resolution: Minimum resolution as (width, height) to filter images.
            caption_from_title: Whether to use the image title as the caption.

        Raises:
            EmptyResponseError: If no valid data is found.

        Returns:
            List of PinterestMedia objects parsed from the response.
        """
        if not response_data:
            raise EmptyResponseError("No data found in response.")

        min_width, min_height = min_resolution
        media_items: List[PinterestMedia] = []

        for item in response_data:
            if not isinstance(item, dict):
                continue

            # Parse base image data
            orig = item.get("images", {}).get("orig")
            if not orig:
                continue

            # Extract and validate dimensions
            try:
                width = int(orig.get("width", 0))
                height = int(orig.get("height", 0))
            except (TypeError, ValueError):
                continue

            # Skip images below minimum resolution
            if width < min_width or height < min_height:
                continue

            # Extract source URL
            src = orig.get("url")
            if not src:
                continue

            # Extract metadata
            id = item.get("id", 0)

            # Determine caption based on preference
            if caption_from_title:
                alt = item.get(
                    "title",
                    item.get("auto_alt_text", ""),  # Fallback to auto_alt_text
                )
            else:
                alt = item.get("auto_alt_text", "")

            origin = f"https://www.pinterest.com/pin/{id}/"

            # Parse video stream if available
            video_stream = cls._parse_video_stream(item)

            media_items.append(
                PinterestMedia(
                    id=id,
                    src=src,
                    alt=alt,
                    origin=origin,
                    resolution=(width, height),
                    video_stream=video_stream,
                )
            )

        return media_items

    @classmethod
    def _parse_video_stream(cls, item: Dict[str, Any]) -> Optional[VideoStreamInfo]:
        """Parse video stream information from Pinterest item.

        Args:
            item: Pinterest API item dictionary.

        Returns:
            VideoStreamInfo if video data is valid, None otherwise.
        """
        stream_variant = cls._get_best_video_variant(item)
        if not stream_variant:
            return None

        url = stream_variant.get("url")
        if not url:
            return None

        return VideoStreamInfo(
            url=url,
            resolution=(
                stream_variant.get("width", 0),
                stream_variant.get("height", 0),
            ),
            duration=stream_variant.get("duration", 0),
        )

    @staticmethod
    def _extract_video_list(data_raw: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract video list from Pinterest item.

        Checks multiple locations where video data can appear:
        1. Regular pins: videos.video_list
        2. Story pins: story_pin_data.pages[0].blocks[0].video.video_list

        Args:
            data_raw: Raw Pinterest API item data.

        Returns:
            Dictionary mapping video variant keys to metadata.
        """
        # Try regular pin structure first: videos.video_list
        try:
            video_list = data_raw["videos"]["video_list"]
            if isinstance(video_list, dict) and video_list:
                return video_list
        except (KeyError, TypeError):
            pass

        # Try story pin structure: story_pin_data.pages[0].blocks[0].video.video_list
        try:
            video_list = data_raw["story_pin_data"]["pages"][0]["blocks"][0]["video"]["video_list"]
            if isinstance(video_list, dict):
                return video_list
        except (KeyError, IndexError, TypeError):
            pass

        return {}

    @staticmethod
    def _choose_highest_resolution(video_list: Dict[str, Dict]) -> Optional[Dict[str, Any]]:
        """Select highest resolution video variant.

        Args:
            video_list: Dictionary of video variants.

        Returns:
            Video variant dictionary with highest resolution, or None if empty.
        """
        if not video_list:
            return None

        def resolution(entry: Dict[str, Any]) -> int:
            """Calculate pixel count for sorting."""
            return (entry.get("width") or 0) * (entry.get("height") or 0)

        return max(video_list.values(), key=resolution)

    @classmethod
    def _get_best_video_variant(cls, data_raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get best video variant from Pinterest item.

        Args:
            data_raw: Raw Pinterest API item data.

        Returns:
            Best video variant dictionary, or None if unavailable.
        """
        video_list = cls._extract_video_list(data_raw)
        return cls._choose_highest_resolution(video_list)
