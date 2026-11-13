"""Tests for local media storage helpers."""

import pytest

from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.storage.media import prune_local


def _local_media(tmp_path, resolution):
    path = tmp_path / "pin.jpg"
    path.write_bytes(b"jpg")
    media = PinterestMedia(
        id=1,
        src="https://i.pinimg.com/originals/pin.jpg",
        alt=None,
        origin=None,
        resolution=resolution,
    )
    media.local_path = path
    return media


class TestPruneLocal:
    """prune_local removes files below the minimum width or height."""

    @pytest.mark.parametrize(
        "resolution",
        [
            (2000, 100),  # wide enough, too short
            (500, 5000),  # tall enough, too narrow
            (300, 300),  # too small both ways
        ],
    )
    def test_prunes_when_either_dimension_is_below_minimum(self, tmp_path, resolution):
        media = _local_media(tmp_path, resolution)

        assert prune_local(media, (512, 512)) is True
        assert not media.local_path.exists()

    @pytest.mark.parametrize("resolution", [(512, 512), (800, 1200)])
    def test_keeps_media_that_meets_both_dimensions(self, tmp_path, resolution):
        media = _local_media(tmp_path, resolution)

        assert prune_local(media, (512, 512)) is False
        assert media.local_path.exists()

    def test_keeps_media_without_resolution(self, tmp_path):
        media = _local_media(tmp_path, None)

        assert prune_local(media, (512, 512)) is False
        assert media.local_path.exists()
