import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pinterest_dl import downloader, io


def get_chrome_version():
    try:
        # Determine the operating system
        os_type = platform.system()

        if os_type == "Windows":
            # Command for Windows to read from registry
            output = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                shell=True,
            )
            version = output.decode().split()[-1]

        elif os_type == "Darwin":  # macOS
            # Command for macOS to get version from Chrome app
            output = subprocess.check_output(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
            )
            version = output.decode("utf-8").strip().split()[-1]

        elif os_type == "Linux":
            # Command for Linux to get version from installed Chrome
            output = subprocess.check_output(["google-chrome", "--version"])
            version = output.decode("utf-8").strip().split()[-1]

        else:
            return "Unsupported operating system."

        return version

    except Exception as e:
        return f"Error retrieving Chrome version: {e}"


def get_platform():
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

    return None


def install_chrome_driver(
    install_dir: Path | str,
    version: str = "latest",
    platform: Literal["win32", "win64", "mac-x64", "mac-arm64", "linux64"] = "win64",
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
        response = downloader.get(
            "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json",
            response_format="json",
        )
        version = response["channels"]["Stable"]["version"]
    version.strip()
    platform.strip().lower()
    if platform not in ["win32", "win64", "mac-x64", "mac-arm64", "linux64"]:
        raise ValueError(
            "Platform must be one of 'win32', 'win64', 'mac-x64', 'mac-arm64', 'linux64'."
        )
    # create directory if not exist
    Path(install_dir).mkdir(parents=True, exist_ok=True)

    url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform}/chromedriver-{platform}.zip"
    if verbose:
        print(f"Downloading Chrome driver from {url}")
    zip_file = downloader.download(url, install_dir)
    io.unzip(zip_file, install_dir, "chromedriver.exe", verbose=verbose)
    io.write_text(version, install_dir / "CHROMEDRIVER_VERSION")
    print("Chrome driver installed.")

    os.unlink(zip_file)
    if verbose:
        print("Clean up zip file.")
