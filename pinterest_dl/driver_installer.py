import os
import subprocess
from pathlib import Path

from pinterest_dl import downloader, io


def print_chrome_version():
    command = (
        'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
    )

    # Execute the command to get Chrome version
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )
    if result.stderr:
        raise RuntimeError(result.stderr)
    print(result.stdout.strip())


def install_chrome_driver(install_dir, version=None, platform="win64", verbose=False):
    if version is None:
        print_chrome_version()
        print("Enter the version of Chrome installed on your system.")
        version = input("Version: ")
    version.strip()
    platform.strip().lower()
    if platform not in ["win32", "win64"]:
        raise ValueError("Platform must be either win32 or win64.")
    # create directory if not exist
    Path(install_dir).mkdir(parents=True, exist_ok=True)

    url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform}/chromedriver-{platform}.zip"
    if verbose:
        print(f"Downloading Chrome driver from {url}")
    zip_file = downloader.download(url, install_dir, verbose=verbose)
    io.unzip(zip_file, install_dir, "chromedriver.exe", verbose=verbose)
    print("Chrome driver installed.")

    os.unlink(zip_file)
    if verbose:
        print("Clean up zip file.")
