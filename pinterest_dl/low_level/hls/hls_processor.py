import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import m3u8
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pinterest_dl.exceptions import HlsDownloadError
from pinterest_dl.low_level.hls.key_cache import KeyCache
from pinterest_dl.low_level.hls.segment_info import SegmentInfo


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
        infos: List[SegmentInfo] = []
        for idx, segment in enumerate(playlist.segments):
            seg_url = urljoin(base_uri, segment.uri)
            method = None
            key_uri = None
            iv_bytes: Optional[bytes] = None
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
            infos.append(
                SegmentInfo(
                    index=idx,
                    uri=seg_url,
                    method=method,
                    key_uri=key_uri,
                    iv=iv_bytes,
                    media_sequence=media_sequence,
                )
            )
        return infos

    def download_segment(self, url: str) -> bytes:
        """Download a segment.

        Args:
            url (str): The URL of the segment.

        Raises:
            HlsDownloadError: If the segment cannot be downloaded.

        Returns:
            bytes: The content of the downloaded segment.
        """
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
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
    def build_concat_list(segment_paths: List[Path], output_list: Path) -> None:
        """Build a concat list file for ffmpeg.

        Args:
            segment_paths (List[Path]): The paths to the segment files.
            output_list (Path): The path to the output concat list file.
        """
        with output_list.open("w", encoding="utf-8") as f:
            for p in segment_paths:
                f.write(f"file '{p.as_posix()}'\n")

    def concat_and_remux(
        self, concat_list: Path, output_mp4: Path, reencode_fallback: bool = True
    ) -> None:
        """Concatenate segments and remux to MP4 using ffmpeg in a single step. (use this for better performance)

        Args:
            concat_list (Path): Path to the file containing the list of segments.
            output_mp4 (Path): Path to the output MP4 file.
            reencode_fallback (bool, optional): Whether to re-encode if remuxing fails. Defaults to True.
        """
        # Try direct remux (concat into mp4)
        try:
            self._run_cmd(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "info",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-c",
                    "copy",
                    str(output_mp4),
                ],
                "concat and remux",
            )
        except HlsDownloadError:
            if not reencode_fallback:
                raise
            # Fallback: re-encode video/audio while concatenating
            self._run_cmd(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "info",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    str(output_mp4),
                ],
                "concat and re-encode",
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
