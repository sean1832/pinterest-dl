import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import m3u8
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pinterest_dl.download.video.key_cache import KeyCache
from pinterest_dl.download.video.segment_info import SegmentInfo
from pinterest_dl.exceptions import HlsDownloadError


class HlsProcessor:
    """Process HLS streams for downloading."""

    def __init__(
        self,
        session: requests.Session,
        user_agent: str,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """Initialize HLS processor.

        Args:
            session (requests.Session): The requests session to use.
            user_agent (str): The User-Agent string to use for requests.
            timeout (int, optional): The timeout for requests in seconds. Defaults to 10.
            max_retries (int, optional): The maximum number of retries for failed requests. Defaults to 3.
        """
        self.session = session
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout = timeout
        self.max_retries = max_retries
        self.key_cache = KeyCache(self.session, timeout=timeout, max_retries=max_retries)

    def fetch_playlist(self, url: str) -> m3u8.M3U8:
        """Fetch HLS playlist.

        Args:
            url (str): The URL of the HLS playlist.
        Returns:
            m3u8.M3U8: The parsed HLS playlist object.
        """
        if not url.startswith("http"):
            raise HlsDownloadError(f"HLS URL must start with http or https: '{url}'")
        if not url.endswith(".m3u8"):
            raise HlsDownloadError(f"HLS URL must end with .m3u8: '{url}'")

        return m3u8.load(url)

    def resolve_variant(self, playlist: m3u8.M3U8, base_uri: str) -> str:
        """Resolve the best variant playlist.

        Args:
            playlist (m3u8.M3U8): The master playlist.
            base_uri (str): The base URI for resolving relative URLs.

        Raises:
            HlsDownloadError: If no suitable variant playlist is found.

        Returns:
            str: The URL of the resolved variant playlist.
        """
        if not playlist.playlists:
            raise HlsDownloadError("No variant playlists available to resolve")
        best = max(
            (p for p in playlist.playlists if p.stream_info and p.stream_info.bandwidth),
            key=lambda p: p.stream_info.bandwidth or 0,
        )
        return urljoin(base_uri, best.uri)

    def get_init_section(self, playlist: m3u8.M3U8, base_uri: str) -> Optional[SegmentInfo]:
        """Get the initialization section data if present.

        Args:
            playlist (m3u8.M3U8): The HLS playlist.
            base_uri (str): The base URI for resolving segment URLs.
        Returns:
            Optional[SegmentInfo]: The initialization section information, or None if not present.
        """
        if not playlist.segment_map:
            return None
        init = playlist.segment_map[0]
        byte_offset = byte_length = None  # if byterange is not present, these will remain None
        if init.byterange:
            byte_offset, byte_length = self._parse_byterange(init.byterange, 0)
        return SegmentInfo(
            index=-1,
            uri=urljoin(base_uri, init.uri),
            method=None,
            key_uri=None,
            iv=None,
            media_sequence=playlist.media_sequence or 0,
            byte_offset=byte_offset,
            byte_length=byte_length,
        )

    def enumerate_segments(self, playlist: m3u8.M3U8, base_uri: str) -> List[SegmentInfo]:
        """Enumerate segments in the playlist.

        Args:
            playlist (m3u8.M3U8): The HLS playlist.
            base_uri (str): The base URI for resolving segment URLs.

        Raises:
            HlsDownloadError: If the playlist has no segments.
            HlsDownloadError: If a segment is encrypted but has no key URI.
            HlsDownloadError: If a segment uses an unsupported encryption method.

        Returns:
            List[SegmentInfo]: The list of segment information.
        """
        if not playlist.segments:
            raise HlsDownloadError("Playlist has no segments")
        media_sequence = playlist.media_sequence or 0
        prev_end = 0
        infos: List[SegmentInfo] = []
        for idx, segment in enumerate(playlist.segments):
            seg_url = urljoin(base_uri, segment.uri)
            method = None
            key_uri = None
            iv_bytes: Optional[bytes] = None
            byte_length: Optional[int] = None
            byte_offset: Optional[int] = None
            if segment.key:
                key_info = segment.key
                method = key_info.method
                if method != "AES-128":
                    raise HlsDownloadError(f"Unsupported encryption method: {method}")
                if not key_info.uri:
                    raise HlsDownloadError("Encrypted segment without key URI")
                key_uri = urljoin(base_uri, key_info.uri)
                if key_info.iv:
                    hexstr = key_info.iv.lower().replace("0x", "")
                    iv_bytes = bytes.fromhex(hexstr)
                else:
                    iv_bytes = self._compute_default_iv(media_sequence, idx)
            if segment.byterange:
                byte_offset, byte_length = self._parse_byterange(segment.byterange, prev_end)
                prev_end = byte_offset + byte_length
            infos.append(
                SegmentInfo(
                    index=idx,
                    uri=seg_url,
                    method=method,
                    key_uri=key_uri,
                    iv=iv_bytes,
                    media_sequence=media_sequence,
                    byte_offset=byte_offset,
                    byte_length=byte_length,
                )
            )
        return infos

    @staticmethod
    def _parse_byterange(spec: str, offset: int) -> Tuple[int, int]:
        """
        Parse an EXT-X-BYTERANGE 'length[@offset]' value into (offset, length).

        Args:
            spec (str): The byterange specification string (e.g., "5000@10000" or "5000").
            offset (int): The starting byte offset, used for absolute ranges.

        Returns:
            Tuple[int, int]: A tuple of (offset, length) where offset is the starting byte and length is the number of bytes.
        """
        spec = spec.strip()
        if "@" in spec:
            length_str, offset_str = spec.split("@", 1)
            return int(offset_str), int(length_str)

        return offset, int(spec)

    def download_segment(
        self, url: str, byte_offset: Optional[int] = None, byte_length: Optional[int] = None
    ) -> bytes:
        """Download a segment with optional byte range.

        Args:
            url (str): The URL of the segment.
            byte_offset (Optional[int]): The starting byte offset for the segment, if using byte range.
            byte_length (Optional[int]): The length in bytes to download, if using byte range.

        Returns:
            bytes: The downloaded segment data.
        """
        headers = None
        # If both byte_offset and byte_length are provided, set the Range header
        if byte_offset is not None and byte_length is not None:
            headers = {"Range": f"bytes={byte_offset}-{byte_offset + byte_length - 1}"}
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, headers=headers)
                if resp.status_code == 206:
                    # Partial Content: server honored the Range request
                    return resp.content
                if resp.status_code == 200:
                    # Server ignored Range and sent the whole file.
                    # Slice so we never concatenate full copies
                    if byte_offset is not None and byte_length is not None:
                        return resp.content[byte_offset : byte_offset + byte_length]
                    return resp.content
                last_exc = HlsDownloadError(f"HTTP {resp.status_code} for segment: {url}")
            except requests.RequestException as e:
                last_exc = e
        raise HlsDownloadError(
            f"Failed to download HLS segment after {self.max_retries} attempts: {url}\n"
            f"Last error: {last_exc}"
        )

    @staticmethod
    def _compute_default_iv(media_sequence: int, segment_index: int) -> bytes:
        seq = media_sequence + segment_index
        return seq.to_bytes(16, "big")

    def decrypt(self, segment: SegmentInfo, ciphertext: bytes) -> bytes:
        """Decrypt the segment if it is encrypted.

        Args:
            segment (SegmentInfo): The segment information.
            ciphertext (bytes): The encrypted segment data.

        Raises:
            HlsDownloadError: If decryption fails.
            HlsDownloadError: If the segment uses an unsupported encryption method.

        Returns:
            bytes: The decrypted segment data.
        """

        if segment.method is None:
            return ciphertext
        if segment.method != "AES-128":
            raise HlsDownloadError(f"Unsupported method {segment.method}")
        if not segment.key_uri:
            raise HlsDownloadError("Missing key URI for decryption")
        key = self.key_cache.get(segment.key_uri)
        iv = segment.iv or self._compute_default_iv(segment.media_sequence, segment.index)
        return self._aes128_decrypt(ciphertext, key, iv)

    @staticmethod
    def _aes128_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def write_segment_file(path: Path, data: bytes) -> None:
        """Write the decrypted segment to a file.

        Args:
            path (Path): The path to the output file.
            data (bytes): The decrypted segment data.
        """
        path.write_bytes(data)

    @staticmethod
    def concat_to_ts(segment_paths: List[Path], output_ts: Path) -> None:
        """Binary concatenate .ts segments into a single .ts file without ffmpeg.

        Args:
            segment_paths (List[Path]): List of segment file paths.
            output_ts (Path): Path to output .ts file.
        """
        with output_ts.open("wb") as out:
            for seg_path in segment_paths:
                out.write(seg_path.read_bytes())

    def remux_to_mp4(self, input_file: Path, output_mp4: Path) -> None:
        """Concatenate segments and remux to MP4 using ffmpeg (stream copy, no re-encode).

        Args:
            input_file (Path): Path to the concatenated input .ts file.
            output_mp4 (Path): Path to the output MP4 file.

        Raises:
            HlsDownloadError: If ffmpeg remux fails.
        """
        self._run_cmd(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "info",
                "-i",
                input_file.absolute().as_posix(),
                "-c",
                "copy",
                output_mp4.absolute().as_posix(),
            ],
            "remux to mp4",
        )

    # TODO: Expose reencode_to_mp4 via CLI flag (e.g. --reencode) for guaranteed mp4 output
    def reencode_to_mp4(self, input_file: Path, output_mp4: Path, crf: int = 23) -> None:
        """Concatenate segments and re-encode to MP4 using ffmpeg (slower but more compatible).

        Args:
            input_file (Path): Path to the concatenated input .ts file.
            output_mp4 (Path): Path to the output MP4 file.
            crf (int): The CRF value for x264 encoding (lower is better quality, default 23).

        Raises:
            HlsDownloadError: If ffmpeg re-encode fails.
        """
        self._run_cmd(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "info",
                "-i",
                input_file.absolute().as_posix(),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                str(crf),
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                output_mp4.absolute().as_posix(),
            ],
            "re-encode to mp4",
        )

    def _run_cmd(self, cmd: List[str], phase: str) -> None:
        """Run ffmpeg command and raise detailed error on failure."""
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            stderr_tail = "\n".join(proc.stderr.strip().splitlines()[-60:])
            raise HlsDownloadError(
                f"ffmpeg {phase} failed with exit code {proc.returncode}.\n"
                f"Command: {' '.join(cmd[:5])}...\n"
                f"Error output:\n{stderr_tail}"
            )
