import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from pinterest_dl.download.video.hls_processor import HlsProcessor
from pinterest_dl.exceptions import HlsDownloadError
from pinterest_dl.download.video.segment_info import SegmentInfo

class TestHlsProcessor:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def processor(self, mock_session):
        return HlsProcessor(mock_session, user_agent="test-agent")

    def test_fetch_playlist_validation(self, processor):
        """Test URL validation in fetch_playlist."""
        with pytest.raises(HlsDownloadError, match="must start with http"):
            processor.fetch_playlist("ftp://example.com/video.m3u8")
        
        with pytest.raises(HlsDownloadError, match="must end with .m3u8"):
            processor.fetch_playlist("http://example.com/video.mp4")

    @patch("m3u8.load")
    def test_fetch_playlist_success(self, mock_load, processor):
        """Test successful playlist fetching."""
        url = "http://example.com/video.m3u8"
        processor.fetch_playlist(url)
        mock_load.assert_called_once_with(url)

    def test_resolve_variant_best_bandwidth(self, processor):
        """Test resolving the variant with the highest bandwidth."""
        # Mock m3u8 playlist object
        mock_playlist = MagicMock()
        
        # Create mock variants with different bandwidths
        v1 = MagicMock()
        v1.stream_info.bandwidth = 1000
        v1.uri = "low.m3u8"
        
        v2 = MagicMock()
        v2.stream_info.bandwidth = 5000
        v2.uri = "high.m3u8"
        
        v3 = MagicMock()
        v3.stream_info.bandwidth = 2000
        v3.uri = "mid.m3u8"
        
        mock_playlist.playlists = [v1, v2, v3]
        
        base_uri = "http://example.com/"
        resolved_url = processor.resolve_variant(mock_playlist, base_uri)
        
        assert resolved_url == "http://example.com/high.m3u8"

    def test_resolve_variant_no_playlists(self, processor):
        """Test error when no variants are available."""
        mock_playlist = MagicMock()
        mock_playlist.playlists = []
        
        with pytest.raises(HlsDownloadError, match="No variant playlists"):
            processor.resolve_variant(mock_playlist, "http://example.com/")

    def test_enumerate_segments_encryption(self, processor):
        """Test parsing segments with encryption info."""
        mock_playlist = MagicMock()
        mock_playlist.media_sequence = 0
        
        # Segment 1: Encrypted
        seg1 = MagicMock()
        seg1.uri = "seg1.ts"
        seg1.key.method = "AES-128"
        seg1.key.uri = "key.php"
        seg1.key.iv = "0x1234567890abcdef1234567890abcdef"
        
        # Segment 2: Unencrypted
        seg2 = MagicMock()
        seg2.uri = "seg2.ts"
        seg2.key = None
        
        mock_playlist.segments = [seg1, seg2]
        base_uri = "http://example.com/"
        
        segments = processor.enumerate_segments(mock_playlist, base_uri)
        
        assert len(segments) == 2
        
        # Verify encrypted segment
        assert segments[0].uri == "http://example.com/seg1.ts"
        assert segments[0].method == "AES-128"
        assert segments[0].key_uri == "http://example.com/key.php"
        assert segments[0].iv == bytes.fromhex("1234567890abcdef1234567890abcdef")
        
        # Verify unencrypted segment
        assert segments[1].uri == "http://example.com/seg2.ts"
        assert segments[1].method is None

    def test_enumerate_segments_unsupported_encryption(self, processor):
        """Test error for unsupported encryption method."""
        mock_playlist = MagicMock()
        seg = MagicMock()
        seg.uri = "seg.ts"
        seg.key.method = "SAMPLE-AES"
        mock_playlist.segments = [seg]
        
        with pytest.raises(HlsDownloadError, match="Unsupported encryption method"):
            processor.enumerate_segments(mock_playlist, "http://example.com/")

    def test_parse_byterange(self, processor):
        """Parse 'length@offset' and bare 'length' (implicit offset) forms."""
        assert processor._parse_byterange("500@1000", 0) == (1000, 500)
        # When '@offset' is omitted, the range continues from the previous end.
        assert processor._parse_byterange("500", 1500) == (1500, 500)

    def test_enumerate_segments_byterange(self, processor):
        """Byte-range segments sharing one file keep distinct (offset, length).

        Regression: the ranges used to be dropped, so every segment resolved to
        the same URL and the whole file was downloaded once per segment, yielding
        a video repeated N times.
        """
        mock_playlist = MagicMock()
        mock_playlist.media_sequence = 0

        seg1 = MagicMock()
        seg1.uri = "video.cmfv"
        seg1.key = None
        seg1.byterange = "100@0"

        seg2 = MagicMock()
        seg2.uri = "video.cmfv"
        seg2.key = None
        seg2.byterange = "200@100"

        mock_playlist.segments = [seg1, seg2]
        segments = processor.enumerate_segments(mock_playlist, "http://example.com/")

        assert segments[0].uri == segments[1].uri == "http://example.com/video.cmfv"
        assert (segments[0].byte_offset, segments[0].byte_length) == (0, 100)
        assert (segments[1].byte_offset, segments[1].byte_length) == (100, 200)

    def test_get_init_section(self, processor):
        """EXT-X-MAP init section is resolved with its byte range."""
        mock_playlist = MagicMock()
        mock_playlist.media_sequence = 0
        init = MagicMock()
        init.uri = "video.cmfv"
        init.byterange = "899@0"
        mock_playlist.segment_map = [init]

        result = processor.get_init_section(mock_playlist, "http://example.com/")

        assert result is not None
        assert result.uri == "http://example.com/video.cmfv"
        assert (result.byte_offset, result.byte_length) == (0, 899)

    def test_get_init_section_absent(self, processor):
        """No EXT-X-MAP -> no init section (plain .ts streams)."""
        mock_playlist = MagicMock()
        mock_playlist.segment_map = []
        assert processor.get_init_section(mock_playlist, "http://example.com/") is None

    def test_download_segment_byterange_uses_range_header(self, processor, mock_session):
        """Range request sends a Range header and accepts HTTP 206."""
        resp = MagicMock()
        resp.status_code = 206
        resp.content = b"partial-bytes"
        mock_session.get.return_value = resp

        data = processor.download_segment(
            "http://example.com/v.cmfv", byte_offset=100, byte_length=50
        )

        assert data == b"partial-bytes"
        _, kwargs = mock_session.get.call_args
        assert kwargs["headers"] == {"Range": "bytes=100-149"}

    def test_download_segment_200_slices_when_range_ignored(self, processor, mock_session):
        """If the server ignores Range and returns 200, slice locally."""
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"0123456789"
        mock_session.get.return_value = resp

        data = processor.download_segment(
            "http://example.com/v.cmfv", byte_offset=2, byte_length=4
        )

        assert data == b"2345"

    def test_decrypt_aes128(self, processor):
        """Test AES-128 decryption logic."""
        # Setup mock key cache
        processor.key_cache.get = MagicMock(return_value=b"1234567890123456") # 16 bytes key
        
        segment = SegmentInfo(
            index=0,
            uri="http://example.com/seg.ts",
            method="AES-128",
            key_uri="http://example.com/key",
            iv=b"0000000000000000", # 16 bytes IV
            media_sequence=0
        )
        
        encrypted_data = b"encrypteddata123" # Dummy data
        
        with patch("pinterest_dl.download.video.hls_processor.Cipher") as MockCipher:
            mock_decryptor = MagicMock()
            mock_decryptor.update.return_value = b"decrypted"
            mock_decryptor.finalize.return_value = b""
            
            mock_cipher_instance = MockCipher.return_value
            mock_cipher_instance.decryptor.return_value = mock_decryptor
            
            result = processor.decrypt(segment, encrypted_data)
            
            assert result == b"decrypted"
            processor.key_cache.get.assert_called_with("http://example.com/key")

    @patch("subprocess.run")
    def test_remux_to_mp4_success(self, mock_run, processor):
        """Test successful remux command (single input file, stream copy)."""
        mock_run.return_value.returncode = 0

        input_file = Path("combined.ts")
        output_mp4 = Path("output.mp4")

        processor.remux_to_mp4(input_file, output_mp4)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert "-c" in args
        assert "copy" in args  # verify stream copy is used
        assert input_file.absolute().as_posix() in args
        assert output_mp4.absolute().as_posix() in args

    @patch("subprocess.run")
    def test_reencode_to_mp4_failure_handling(self, mock_run, processor):
        """Test error handling when ffmpeg fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error details"
        
        with pytest.raises(HlsDownloadError, match="ffmpeg re-encode to mp4 failed"):
            processor.reencode_to_mp4(Path("list.txt"), Path("out.mp4"))
