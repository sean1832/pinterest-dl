
import pytest
from unittest.mock import MagicMock
from pathlib import Path
from pinterest_dl.download.downloader import MediaDownloader, _ConcurrentCoordinator
from pinterest_dl.domain.media import PinterestMedia, VideoStreamInfo
from pinterest_dl.exceptions import DownloadError

class TestMediaDownloader:
    @pytest.fixture
    def mock_http_client(self):
        return MagicMock()

    @pytest.fixture
    def downloader(self, mock_http_client):
        dl = MediaDownloader(user_agent="test-agent")
        dl.http_client = mock_http_client
        return dl

    @pytest.fixture
    def sample_media(self):
        return PinterestMedia(
            id=123,
            src="http://example.com/image.jpg",
            alt="desc",
            origin="http://pinterest.com/pin/123",
            resolution=(100, 100)
        )

    @pytest.fixture
    def sample_video_media(self, sample_media):
        sample_media.video_stream = VideoStreamInfo(
            url="http://example.com/video.m3u8",
            resolution=(720, 1280),
            duration=10
        )
        return sample_media

    def test_download_image_default(self, downloader, sample_media, tmp_path):
        """Test default behavior downloads image."""
        output_dir = tmp_path
        
        result_path = downloader.download(sample_media, output_dir)
        
        expected_path = output_dir / "123.jpg"
        assert result_path == expected_path
        downloader.http_client.download_blob.assert_called_once_with(
            sample_media.src, expected_path, chunk_size=2048
        )

    def test_download_image_fallback_when_streams_disabled(self, downloader, sample_video_media, tmp_path):
        """Test video media falls back to image if download_streams=False."""
        output_dir = tmp_path
        
        result_path = downloader.download(sample_video_media, output_dir, download_streams=False)
        
        expected_path = output_dir / "123.jpg"
        assert result_path == expected_path
        downloader.http_client.download_blob.assert_called_once()
        downloader.http_client.download_streams.assert_not_called()

    def test_download_video_direct_mp4(self, downloader, sample_media, tmp_path):
        """Test direct MP4 download."""
        sample_media.video_stream = VideoStreamInfo(
            url="http://example.com/video.mp4",
            resolution=(720, 1280),
            duration=10
        )
        output_dir = tmp_path
        
        result_path = downloader.download(sample_media, output_dir, download_streams=True)
        
        expected_path = output_dir / "123.mp4"
        assert result_path == expected_path
        # Should call download_blob for MP4, not download_streams
        downloader.http_client.download_blob.assert_called_once_with(
            "http://example.com/video.mp4", expected_path, chunk_size=2048
        )

    def test_download_video_hls(self, downloader, sample_video_media, tmp_path):
        """Test HLS video download delegation."""
        output_dir = tmp_path
        
        # Mock download_streams to return a path
        expected_path = output_dir / "123.mp4"
        downloader.http_client.download_streams.return_value = expected_path
        
        result_path = downloader.download(sample_video_media, output_dir, download_streams=True)
        
        assert result_path == expected_path
        downloader.http_client.download_streams.assert_called_once_with(
            sample_video_media.video_stream.url, expected_path, False
        )

    def test_download_video_hls_skip_remux(self, downloader, sample_video_media, tmp_path):
        """Test HLS video download with skip_remux=True."""
        output_dir = tmp_path
        
        # Mock download_streams to return a path (likely .ts)
        expected_path = output_dir / "123.mp4" # return val is just what the mock returns
        downloader.http_client.download_streams.return_value = expected_path
        
        downloader.download(sample_video_media, output_dir, download_streams=True, skip_remux=True)
        
        downloader.http_client.download_streams.assert_called_once_with(
            sample_video_media.video_stream.url, expected_path, True
        )


class TestConcurrentCoordinator:
    def test_concurrent_execution(self, tmp_path):
        """Test that items are processed and results returned."""
        coordinator = _ConcurrentCoordinator()
        
        items = [1, 2, 3]
        
        def worker(item, outdir):
            return outdir / f"{item}.txt"
        
        results = coordinator.run(items, tmp_path, worker, max_workers=2)
        
        assert len(results) == 3
        assert Path(tmp_path / "1.txt") in results
        assert Path(tmp_path / "2.txt") in results
        assert Path(tmp_path / "3.txt") in results

    def test_fail_fast(self, tmp_path):
        """Test fail_fast raises exception immediately."""
        coordinator = _ConcurrentCoordinator()
        
        items = [1, 2, 3]
        
        def worker(item, outdir):
            if item == 2:
                raise ValueError("Boom")
            return outdir / f"{item}.txt"
        
        with pytest.raises(ValueError, match="Boom"):
            coordinator.run(items, tmp_path, worker, max_workers=1, fail_fast=True)

    def test_collect_errors_no_fail_fast(self, tmp_path):
        """Test that without fail_fast, all errors are collected and raised as DownloadError."""
        coordinator = _ConcurrentCoordinator()
        
        items = ["ok1", "fail1", "ok2", "fail2"]
        
        def worker(item, outdir):
            if "fail" in str(item):
                raise ValueError(f"Error in {item}")
            return item
        
        with pytest.raises(DownloadError) as excinfo:
            coordinator.run(items, tmp_path, worker, max_workers=2, fail_fast=False)
        
        error_msg = str(excinfo.value)
        assert "Failed to download 2 out of 4 items" in error_msg
        assert "Error in fail1" in error_msg
        assert "Error in fail2" in error_msg
