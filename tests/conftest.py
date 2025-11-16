"""Pytest configuration and shared fixtures."""
import pytest

from pinterest_dl.data_model.pinterest_media import PinterestMedia, VideoStreamInfo


@pytest.fixture
def sample_media():
    """Create a sample PinterestMedia object for testing."""
    return PinterestMedia(
        id=123456789,
        src="https://i.pinimg.com/originals/ab/cd/ef/abcdef123456.jpg",
        alt="A beautiful landscape photo",
        origin="https://www.pinterest.com/pin/123456789/",
        resolution=(1920, 1080),
    )


@pytest.fixture
def sample_media_with_video():
    """Create a sample PinterestMedia with video stream."""
    video_stream = VideoStreamInfo(
        url="https://v.pinimg.com/videos/mc/720p/ab/cd/ef/abcdef.m3u8",
        resolution=(1280, 720),
        duration=30,
    )
    return PinterestMedia(
        id=987654321,
        src="https://i.pinimg.com/originals/12/34/56/123456.jpg",
        alt="Video pin",
        origin="https://www.pinterest.com/pin/987654321/",
        resolution=(1280, 720),
        video_stream=video_stream,
    )


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for file tests."""
    test_dir = tmp_path / "test_output"
    test_dir.mkdir()
    return test_dir
