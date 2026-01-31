import pytest
from unittest.mock import MagicMock, patch
from pinterest_dl.download.http_client import HttpClient
from pinterest_dl.download.video.segment_info import SegmentInfo

class TestHttpClientVideo:
    @pytest.fixture
    def mock_processor(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_processor):
        with patch("pinterest_dl.download.http_client.HlsProcessor", return_value=mock_processor):
            client = HttpClient(user_agent="test-agent")
            return client

    def test_download_streams_flow(self, client, mock_processor, tmp_path):
        """Test the full flow of HLS stream download."""
        output_mp4 = tmp_path / "video.mp4"
        url = "http://example.com/master.m3u8"
        
        # 1. Playlist Setup
        mock_playlist = MagicMock()
        mock_playlist.is_variant = False # Simulate leaf playlist
        mock_playlist.base_uri = "http://example.com/"
        mock_processor.fetch_playlist.return_value = mock_playlist
        
        # 2. Segments Setup
        seg1 = SegmentInfo(0, "seg1.ts", None, None, None, 0)
        seg2 = SegmentInfo(1, "seg2.ts", None, None, None, 1)
        mock_processor.enumerate_segments.return_value = [seg1, seg2]
        
        # 3. Download/Decrypt Setup
        mock_processor.download_segment.return_value = b"encrypted"
        mock_processor.decrypt.return_value = b"decrypted"
        
        client.download_streams(url, output_mp4, skip_remux=False)
        
        # Verifications
        mock_processor.fetch_playlist.assert_called_with(url)
        mock_processor.enumerate_segments.assert_called()
        
        # Should download and decrypt every segment
        assert mock_processor.download_segment.call_count == 2
        assert mock_processor.decrypt.call_count == 2
        assert mock_processor.write_segment_file.call_count == 2
        
        # Should build concat list
        mock_processor.build_concat_list.assert_called_once()
        
        # Should call remux
        mock_processor.remux_to_mp4.assert_called_once()
        mock_processor.reencode_to_mp4.assert_not_called()

    def test_remux_fallback_to_reencode(self, client, mock_processor, tmp_path):
        """Test fallback to re-encode if remux fails."""
        output_mp4 = tmp_path / "video.mp4"
        
        # Setup minimal flow
        mock_playlist = MagicMock()
        mock_playlist.is_variant = False
        mock_processor.fetch_playlist.return_value = mock_playlist
        mock_processor.enumerate_segments.return_value = [] # Empty just to skip loop
        
        # Simulate remux failure
        mock_processor.remux_to_mp4.side_effect = Exception("Remux failed")
        
        client.download_streams("url", output_mp4, skip_remux=False)
        
        mock_processor.remux_to_mp4.assert_called_once()
        mock_processor.reencode_to_mp4.assert_called_once()

    def test_skip_remux_flow(self, client, mock_processor, tmp_path):
        """Test flow when skip_remux is True."""
        output_path = tmp_path / "video.mp4"
        
        mock_playlist = MagicMock()
        mock_playlist.is_variant = False
        mock_processor.fetch_playlist.return_value = mock_playlist
        mock_processor.enumerate_segments.return_value = []
        
        result = client.download_streams("url", output_path, skip_remux=True)
        
        # Expectation: output path extension changed to .ts
        expected_output = output_path.with_suffix(".ts")
        assert result == expected_output
        
        # Should call concat_to_ts, NOT remux/reencode
        mock_processor.concat_to_ts.assert_called_once()
        mock_processor.remux_to_mp4.assert_not_called()
