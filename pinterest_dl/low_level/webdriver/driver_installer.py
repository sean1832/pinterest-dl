import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pinterest_dl.low_level.ops import downloader, io


class ChromeDriverInstaller:
    def __init__(self, install_dir: Path | str) -> None:
        self.install_dir = Path(install_dir)
        self.chrome_version = self._get_chrome_version()
        self.platform: Literal["win32", "win64", "mac-x64", "mac-arm64", "linux64"] = (
            self._get_platform()
        )

    def _get_chrome_version(self) -> str:
        # Determine the operating system
        os_type = platform.system()

        if os_type == "Windows":
            try:
                # Command for Windows to read from registry
                output = subprocess.check_output(
                    r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                    shell=True,
                    stderr=subprocess.STDOUT,  # Capture standard error as well
                )
                version = output.decode().split()[-1]
            except subprocess.CalledProcessError:
                raise FileNotFoundError("Chrome not found in Windows registry.")

        elif os_type == "Darwin":  # macOS
            try:
                # Command for macOS to get version from Chrome app
                output = subprocess.check_output(
                    [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "--version",
                    ],
                    stderr=subprocess.STDOUT,
                )
                version = output.decode("utf-8").strip().split()[-1]
            except FileNotFoundError:
                raise FileNotFoundError("Chrome not found in /Applications.")

        elif os_type == "Linux":
            try:
                # Command for Linux to get version from installed Chrome
                output = subprocess.check_output(
                    ["google-chrome", "--version"], stderr=subprocess.STDOUT
                )
                version = output.decode("utf-8").strip().split()[-1]
            except FileNotFoundError:
                raise FileNotFoundError("Chrome not found in PATH.")

        else:
            return "Unsupported operating system."

        return version

    def _get_platform(
        self,
    ) -> Literal["win32", "win64", "mac-x64", "mac-arm64", "linux64"]:
        os_name = platform.system()
        arch = platform.machine()

        if os_name == "Windows":
            if sys.maxsize > 2**32:
                return "win64"  # 64-bit Windows
            else:
                return "win32"  # 32-bit Windows
        elif os_name == "Darwin":
            if arch == "x86_64":
                return "mac-x64"  # Intel Mac
            elif arch == "arm64":
                return "mac-arm64"  # Apple Silicon Mac
        elif os_name == "Linux":
            if arch in ("x86_64", "amd64"):
                return "linux64"  # 64-bit Linux
        raise ValueError("Unsupported platform.")

    def install(
        self,
        version: str = "latest",
        platform: Literal["win32", "win64", "mac-x64", "mac-arm64", "linux64", "auto"] = "auto",
        verbose: bool = False,
    ):
        """Install Chrome driver to the specified directory.

        Args:
            install_dir (Path | str): Directory to install Chrome driver.
            version (str): Version of Chrome driver to install. Defaults to 'latest'.
            platform (Literal[&quot;win64&quot;, &quot;win32&quot;], optional): Platform of Chrome driver to install. Defaults to &quot;win64&quot;.
            verbose (bool, optional): Print debug logs. Defaults to False.

        Raises:
            ValueError: _description_
        """
        if version == "latest":
            response = downloader.fetch(
                "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json",
                response_format="json",
            )
            if isinstance(response, dict):
                version = response["channels"]["Stable"]["version"]
            else:
                raise ValueError("Failed to fetch latest Chrome driver version.")
        version.strip()

        if platform == "auto":
            platform = self.platform
            if verbose:
                print(f"Auto detected platform: {platform}")

        platform.strip().lower()
        if platform not in ["win32", "win64", "mac-x64", "mac-arm64", "linux64"]:
            raise ValueError(
                "Platform must be one of 'win32', 'win64', 'mac-x64', 'mac-arm64', 'linux64'."
            )
        # create directory if not exist
        Path(self.install_dir).mkdir(parents=True, exist_ok=True)

        url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform}/chromedriver-{platform}.zip"
        if verbose:
            print(f"Downloading Chrome driver from {url}")
        zip_file = downloader.download(url, self.install_dir)
        io.unzip(zip_file, self.install_dir, "chromedriver.exe", verbose=verbose)
        io.write_text(version, f"{str(self.install_dir)}/CHROMEDRIVER_VERSION")
        print("Chrome driver installed.")

        os.unlink(zip_file)
        if verbose:
            print("Clean up zip file.")
