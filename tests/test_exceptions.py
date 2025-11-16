"""Tests for exception handling."""

import pytest

from pinterest_dl.exceptions import (
    DownloadError,
    ExecutableNotFoundError,
    HlsDownloadError,
    InvalidBoardUrlError,
    InvalidPinterestUrlError,
    UnsupportedMediaTypeError,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_hls_download_error(self):
        """Test HlsDownloadError has correct message."""
        error = HlsDownloadError("Failed to download segment")
        assert str(error) == "Failed to download segment"

    def test_invalid_pinterest_url_error(self):
        """Test InvalidPinterestUrlError stores URL."""
        url = "https://invalid.com/pin/123"
        error = InvalidPinterestUrlError(url)
        assert error.url == url
        assert "Invalid Pinterest URL" in str(error)
        assert url in str(error)

    def test_invalid_board_url_error(self):
        """Test InvalidBoardUrlError stores URL."""
        url = "https://pinterest.com/invalid"
        error = InvalidBoardUrlError(url)
        assert error.url == url
        assert "Invalid Pinterest board URL" in str(error)

    def test_download_error(self):
        """Test DownloadError can be raised."""
        with pytest.raises(DownloadError, match="Download failed"):
            raise DownloadError("Download failed")

    def test_unsupported_media_type_error(self):
        """Test UnsupportedMediaTypeError."""
        with pytest.raises(UnsupportedMediaTypeError, match="Unsupported format"):
            raise UnsupportedMediaTypeError("Unsupported format")

    def test_executable_not_found_error(self):
        """Test ExecutableNotFoundError."""
        error = ExecutableNotFoundError("ffmpeg not found in PATH")
        assert "ffmpeg not found in PATH" in str(error)


class TestExceptionRaising:
    """Test that exceptions are raised correctly in critical paths."""

    def test_hls_processor_validates_url_scheme(self):
        """Test HlsProcessor validates URL starts with http/https."""
        import requests

        from pinterest_dl.low_level.hls.hls_processor import HlsProcessor

        processor = HlsProcessor(requests.Session(), "test-agent")

        with pytest.raises(HlsDownloadError, match="must start with http or https"):
            processor.fetch_playlist("invalid-url")

    def test_hls_processor_validates_m3u8_extension(self):
        """Test HlsProcessor validates .m3u8 extension."""
        import requests

        from pinterest_dl.low_level.hls.hls_processor import HlsProcessor

        processor = HlsProcessor(requests.Session(), "test-agent")

        with pytest.raises(HlsDownloadError, match="must end with .m3u8"):
            processor.fetch_playlist("https://example.com/video.mp4")
