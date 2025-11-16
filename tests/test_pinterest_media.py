"""Tests for PinterestMedia data model."""

from pathlib import Path

from pinterest_dl.data_model.pinterest_media import PinterestMedia, VideoStreamInfo


class TestVideoStreamInfo:
    """Test VideoStreamInfo dataclass."""

    def test_create_video_stream_info(self):
        """Test creating a VideoStreamInfo object."""
        stream = VideoStreamInfo(
            url="https://example.com/video.m3u8",
            resolution=(1920, 1080),
            duration=60,
        )
        assert stream.url == "https://example.com/video.m3u8"
        assert stream.resolution == (1920, 1080)
        assert stream.duration == 60


class TestPinterestMedia:
    """Test PinterestMedia class."""

    def test_create_media(self, sample_media):
        """Test creating a PinterestMedia object."""
        assert sample_media.id == 123456789
        assert sample_media.src == "https://i.pinimg.com/originals/ab/cd/ef/abcdef123456.jpg"
        assert sample_media.alt == "A beautiful landscape photo"
        assert sample_media.origin == "https://www.pinterest.com/pin/123456789/"
        assert sample_media.resolution == (1920, 1080)
        assert sample_media.video_stream is None
        assert sample_media.local_path is None

    def test_create_media_with_video(self, sample_media_with_video):
        """Test creating media with video stream."""
        assert sample_media_with_video.video_stream is not None
        assert (
            sample_media_with_video.video_stream.url
            == "https://v.pinimg.com/videos/mc/720p/ab/cd/ef/abcdef.m3u8"
        )
        assert sample_media_with_video.video_stream.resolution == (1280, 720)
        assert sample_media_with_video.video_stream.duration == 30

    def test_to_dict_without_video(self, sample_media):
        """Test converting media to dict without video stream."""
        result = sample_media.to_dict()

        assert result["id"] == 123456789
        assert result["src"] == "https://i.pinimg.com/originals/ab/cd/ef/abcdef123456.jpg"
        assert result["alt"] == "A beautiful landscape photo"
        assert result["origin"] == "https://www.pinterest.com/pin/123456789/"
        assert result["resolution"]["x"] == 1920
        assert result["resolution"]["y"] == 1080
        assert "media_stream" not in result

    def test_to_dict_with_video(self, sample_media_with_video):
        """Test converting media with video to dict."""
        result = sample_media_with_video.to_dict()

        assert "media_stream" in result
        assert (
            result["media_stream"]["video"]["url"]
            == "https://v.pinimg.com/videos/mc/720p/ab/cd/ef/abcdef.m3u8"
        )
        assert result["media_stream"]["video"]["resolution"] == (1280, 720)
        assert result["media_stream"]["video"]["duration"] == 30

    def test_set_local_path_string(self, sample_media):
        """Test setting local path with string."""
        sample_media.set_local_path("path/to/image.jpg")
        assert sample_media.local_path == Path("path/to/image.jpg")

    def test_set_local_path_path_object(self, sample_media):
        """Test setting local path with Path object."""
        path = Path("another/path/image.png")
        sample_media.set_local_path(path)
        assert sample_media.local_path == path

    def test_to_dict_with_none_resolution(self):
        """Test to_dict with None resolution."""
        media = PinterestMedia(
            id=999,
            src="https://example.com/image.jpg",
            alt=None,
            origin=None,
            resolution=(0, 0),
        )
        result = media.to_dict()

        assert result["resolution"]["x"] is None
        assert result["resolution"]["y"] is None
