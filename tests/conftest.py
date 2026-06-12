"""Pytest configuration and shared fixtures."""

import socket

import pytest

from pinterest_dl.api.api import Api
from pinterest_dl.domain.media import PinterestMedia, VideoStreamInfo


@pytest.fixture(autouse=True)
def _offline_guard(request, monkeypatch):
    """Keep the default suite fully offline.

    Constructing Api() fetches default cookies over the network, which would
    hit Pinterest on every test run. Stub that out and block any other socket
    connection so no unit test can accidentally reach the network. Tests marked
    with @pytest.mark.integration are exempt and run against the real API.
    """
    if request.node.get_closest_marker("integration"):
        return

    monkeypatch.setattr(Api, "_get_default_cookies", staticmethod(lambda url: {}))

    # Block real outbound connections, but allow loopback: asyncio/Playwright
    # build their event-loop self-pipe from a 127.0.0.1 socketpair on Windows.
    real_connect = socket.socket.connect

    def guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(host, str) and (
            host == "localhost" or host == "::1" or host.startswith("127.")
        ):
            return real_connect(self, address, *args, **kwargs)
        raise RuntimeError(
            "Network access is not allowed in unit tests. "
            "Mark the test with @pytest.mark.integration to hit the real API."
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)


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
