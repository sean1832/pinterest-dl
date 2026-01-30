import os
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

from pinterest_dl.common import io
from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.browser import BrowserVersion
from pinterest_dl.webdriver.driver_installer import BrowserDetector, ChromeDriverInstaller

logger = get_logger(__name__)


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
        logger.debug(f"Current Chrome driver version: {current_version}")
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
            logger.info(f"Installing latest Chrome driver for version {self.version}")
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
            logger.debug("Running in incognito mode")
            chrome_options.add_argument("--incognito")
        if not headful:
            logger.debug("Running in headless mode")
            chrome_options.add_argument("--headless=new")
        try:
            browser = webdriver.Chrome(options=chrome_options, service=service)
        except Exception as e:
            if "cannot find Chrome binary" in str(e):
                raise RuntimeError(
                    "Chrome browser not found. Selenium requires Chrome to be installed.\n"
                    "Options:\n"
                    "  1. Install Chrome browser: https://www.google.com/chrome/\n"
                    "  2. Use Playwright instead (recommended, no browser install needed):\n"
                    "     pinterest-dl scrape <url> --client chromium\n"
                    "     (remove --backend selenium)"
                ) from e
            raise
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
            logger.debug("Running in headless mode")
            firefox_options.add_argument("--headless")
        try:
            browser = webdriver.Firefox(options=firefox_options)
        except Exception as e:
            if "Cannot find firefox binary" in str(e) or "geckodriver" in str(e).lower():
                raise RuntimeError(
                    "Firefox browser not found. Selenium requires Firefox to be installed.\n"
                    "Options:\n"
                    "  1. Install Firefox browser: https://www.mozilla.org/firefox/\n"
                    "  2. Use Playwright instead (recommended, no browser install needed):\n"
                    "     pinterest-dl scrape <url> --client firefox\n"
                    "     (remove --backend selenium)"
                ) from e
            raise
        return browser
