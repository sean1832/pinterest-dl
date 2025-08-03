import os
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

from pinterest_dl.data_model.browser_version import BrowserVersion
from pinterest_dl.low_level.webdriver.driver_installer import BrowserDetector, ChromeDriverInstaller
from pinterest_dl.utils import io


class Browser:
    def __init__(self) -> None:
        self.app_root = io.get_appdata_dir()
        self.version: BrowserVersion = BrowserVersion()  # Default version 0.0.0.0

    @staticmethod
    def _get_appdata_dir(path_under: Optional[str] = None) -> Path:
        if path_under:
            return Path.home().joinpath("AppData", "Local", "pinterest-dl", path_under)
        return Path.home().joinpath("AppData", "Local", "pinterest-dl")

    def _validate_chrome_driver_version(self) -> bool:
        version_file = Path(self.app_root, "CHROMEDRIVER_VERSION")
        if not version_file.exists():
            return False

        with open(version_file, "r") as f:
            version_str = f.read().strip()
            current_version = BrowserVersion.from_str(version_str)
        print(f"Current Chrome driver version: {current_version}")
        if self.version.Major != current_version.Major:
            return False
        if self.version.Minor != current_version.Minor:
            return False
        if self.version.Build != current_version.Build:
            return False
        # patch version can be different

        return True

    def Chrome(
        self,
        image_enable: bool = False,
        incognito: bool = False,
        exe_path: Path | str = "chromedriver.exe",
        headful: bool = False,
    ) -> WebDriver:
        driver_installer = ChromeDriverInstaller(self.app_root)
        spec, version = BrowserDetector.first_available()
        self.version = BrowserVersion.from_str(version)

        if not os.path.exists(exe_path) or not self._validate_chrome_driver_version():
            print(f"Installing latest Chrome driver for version {self.version}")
            driver_installer.install(version="latest", platform="auto")

        service = Service(str(exe_path))
        chrome_options = webdriver.ChromeOptions()

        # Disable images
        # https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-disable-image-loading/
        chrome_options.add_argument(
            "--blink-settings=imagesEnabled=true"
            if image_enable
            else "--blink-settings=imagesEnabled=false"
        )
        chrome_options.add_argument("--log-level=3")  # Suppress most logs
        if incognito:
            print("Running in incognito mode")
            chrome_options.add_argument("--incognito")
        if not headful:
            print("Running in headless mode")
            chrome_options.add_argument("--headless=new")
        browser = webdriver.Chrome(options=chrome_options, service=service)
        return browser

    def Firefox(self, image_enable=False, incognito=False, headful=False) -> WebDriver:
        firefox_options = webdriver.FirefoxOptions()
        # Disable images
        if image_enable:
            firefox_options.set_preference("permissions.default.image", 1)
        else:
            firefox_options.set_preference("permissions.default.image", 2)
        if incognito:
            firefox_options.set_preference("browser.privatebrowsing.autostart", True)
        if not headful:
            print("Running in headless mode")
            firefox_options.add_argument("--headless")
        browser = webdriver.Firefox(options=firefox_options)
        return browser
