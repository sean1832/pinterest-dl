import platform as _platform_module
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from pinterest_dl.exceptions import InvalidBrowser
from pinterest_dl.low_level.http import USER_AGENT, fetch, http_client
from pinterest_dl.utils import io

# Supported driver target platforms
DriverPlatform = Literal["win32", "win64", "mac-x64", "mac-arm64", "linux64"]


@dataclass(frozen=True)
class BrowserSpec:
    name: str
    # Windows: registry path to BLBeacon version key; macOS: binary path; Linux: executable name
    win_registry_key: Optional[str]
    mac_path: Optional[Path]
    linux_executable: Optional[str]

    def is_installed(self) -> bool:
        system = _platform_module.system()
        if system == "Windows":
            if not self.win_registry_key:
                return False
            try:
                subprocess.check_output(
                    rf'reg query "{self.win_registry_key}" /v version',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except subprocess.CalledProcessError:
                return False
        elif system == "Darwin":
            if self.mac_path and self.mac_path.exists():
                return True
            return False
        elif system == "Linux":
            if self.linux_executable and shutil.which(self.linux_executable):
                return True
            return False
        return False

    def probe_version(self) -> Optional[str]:
        system = _platform_module.system()
        if system == "Windows":
            if not self.win_registry_key:
                return None
            try:
                output = subprocess.check_output(
                    rf'reg query "{self.win_registry_key}" /v version',
                    shell=True,
                    stderr=subprocess.STDOUT,
                )
                # Last token is expected to be version
                version = output.decode(errors="ignore").strip().split()[-1]
                return version
            except subprocess.CalledProcessError:
                return None
        elif system == "Darwin":
            if not self.mac_path or not self.mac_path.exists():
                return None
            try:
                output = subprocess.check_output(
                    [str(self.mac_path), "--version"], stderr=subprocess.STDOUT
                )
                # Example: "Google Chrome 115.0.5790.170"
                parts = output.decode("utf-8", errors="ignore").strip().split()
                if parts:
                    return parts[-1]
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None
        elif system == "Linux":
            if not self.linux_executable:
                return None
            exe = shutil.which(self.linux_executable)
            if not exe:
                return None
            try:
                output = subprocess.check_output([exe, "--version"], stderr=subprocess.STDOUT)
                parts = output.decode("utf-8", errors="ignore").strip().split()
                if parts:
                    return parts[-1]
            except subprocess.CalledProcessError:
                return None
        return None


class BrowserDetector:
    # Ordered preference
    BROWSERS: List[BrowserSpec] = [
        BrowserSpec(
            name="chrome",
            win_registry_key=r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
            mac_path=Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            linux_executable="google-chrome",
        ),
        BrowserSpec(
            name="brave",
            win_registry_key=r"HKEY_CURRENT_USER\Software\BraveSoftware\Brave-Browser\BLBeacon",
            mac_path=Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            linux_executable="brave",
        ),
        BrowserSpec(
            name="edge",
            win_registry_key=r"HKEY_CURRENT_USER\Software\Microsoft\Edge\BLBeacon",
            mac_path=Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            linux_executable="microsoft-edge",
        ),
        BrowserSpec(
            name="vivaldi",
            win_registry_key=r"HKEY_CURRENT_USER\Software\Vivaldi\BLBeacon",
            mac_path=Path("/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"),
            linux_executable="vivaldi",
        ),
        BrowserSpec(
            name="opera",
            win_registry_key=r"HKEY_CURRENT_USER\Software\Opera Software\Opera Stable\BLBeacon",
            mac_path=Path("/Applications/Opera.app/Contents/MacOS/Opera"),
            linux_executable="opera",
        ),
    ]

    @classmethod
    def probe_all(cls) -> List[Tuple[BrowserSpec, str]]:
        """Return all installed browsers with their detected version."""
        found: List[Tuple[BrowserSpec, str]] = []
        for spec in cls.BROWSERS:
            if not spec.is_installed():
                continue
            version = spec.probe_version()
            if version:
                found.append((spec, version.strip()))
        return found

    @classmethod
    def first_available(cls) -> Tuple[BrowserSpec, str]:
        """Return first browser that is installed with a version. Raises if none found.

        Raises:
            InvalidBrowser: If no supported browser is found with a retrievable version.

        Returns:
            Tuple[BrowserSpec, str]: The first available browser spec and its version. (spec, version)
        """
        for spec in cls.BROWSERS:
            if not spec.is_installed():
                continue
            version = spec.probe_version()
            if version:
                return spec, version.strip()
        raise InvalidBrowser(
            "No supported Chromium-based browser detected with a retrievable version."
        )


class ChromeDriverInstaller:
    CHROMEDRIVER_PLATFORMS: Tuple[DriverPlatform, ...] = (
        "win32",
        "win64",
        "mac-x64",
        "mac-arm64",
        "linux64",
    )

    def __init__(self, install_dir: Union[Path, str]) -> None:
        self.install_dir = Path(install_dir)
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self._auto_platform: DriverPlatform = self._detect_driver_platform()

    def _detect_driver_platform(self) -> DriverPlatform:
        os_name = _platform_module.system()
        arch = _platform_module.machine().lower()

        if os_name == "Windows":
            if sys.maxsize > 2**32:
                return "win64"
            else:
                return "win32"
        elif os_name == "Darwin":
            if arch == "x86_64":
                return "mac-x64"
            elif arch == "arm64":
                return "mac-arm64"
        elif os_name == "Linux":
            if arch in ("x86_64", "amd64"):
                return "linux64"
        raise ValueError(f"Unsupported platform combination: os={os_name} arch={arch}")

    def install(
        self,
        version: str = "latest",
        platform: Union[DriverPlatform, Literal["auto"]] = "auto",
        verbose: bool = False,
        force: bool = False,
    ) -> Path:
        """
        Install ChromeDriver to install_dir. Returns path to extracted driver binary.
        """
        target_platform: DriverPlatform
        if platform == "auto":
            target_platform = self._auto_platform
            if verbose:
                print(f"Auto-detected driver platform: {target_platform}")
        else:
            if platform not in self.CHROMEDRIVER_PLATFORMS:
                raise ValueError(
                    f"Platform must be one of {self.CHROMEDRIVER_PLATFORMS}, got '{platform}'."
                )
            target_platform = platform

        if version == "latest":
            if verbose:
                print("Fetching latest stable Chrome for Testing version...")
            response = fetch(
                "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json",
                response_format="json",
            )
            if not isinstance(response, dict):
                raise InvalidBrowser("Failed to fetch latest Chrome driver version metadata.")
            try:
                version = response["channels"]["Stable"]["version"]
            except KeyError:
                raise InvalidBrowser(
                    "Unexpected structure in version metadata; missing Stable.version."
                )
        version = version.strip()

        marker_file = self.install_dir / "CHROMEDRIVER_VERSION"
        driver_name = "chromedriver.exe" if target_platform.startswith("win") else "chromedriver"
        extracted_path = self.install_dir / driver_name

        # Skip if already installed and version matches, unless force
        if not force and marker_file.exists():
            existing_version = marker_file.read_text().strip()
            if existing_version == version and extracted_path.exists():
                if verbose:
                    print(
                        f"ChromeDriver {version} already installed at {extracted_path}. Skipping download."
                    )
                return extracted_path

        zip_filename = f"chromedriver-{target_platform}.zip"
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{target_platform}/{zip_filename}"
        zip_path = self.install_dir / zip_filename

        if verbose:
            print(f"Downloading ChromeDriver from {url} into {zip_path}...")

        downloader = http_client.HttpClient(user_agent=USER_AGENT, timeout=10, max_retries=3)
        downloader.download_blob(url, zip_path)

        if verbose:
            print(f"Unpacking {zip_path}...")

        # On non-Windows the binary inside may already be executable; unzip expects the name inside.
        expected_member = (
            "chromedriver.exe" if target_platform.startswith("win") else "chromedriver"
        )
        io.unzip(zip_path, self.install_dir, expected_member, verbose=verbose)

        # Ensure executable bit on unix
        if not target_platform.startswith("win"):
            try:
                extracted_path.chmod(extracted_path.stat().st_mode | 0o111)
            except OSError as e:
                if verbose:
                    print(f"Warning: failed to set executable bit on {extracted_path}: {e}")

        io.write_text(version, str(marker_file))

        # Cleanup
        try:
            zip_path.unlink()
            if verbose:
                print("Removed zip archive.")
        except OSError as e:
            if verbose:
                print(f"Warning: failed to delete archive {zip_path}: {e}")

        if verbose:
            print(f"ChromeDriver {version} installed at {extracted_path}.")
        return extracted_path
