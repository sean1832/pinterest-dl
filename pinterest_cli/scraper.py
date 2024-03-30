import copy
import os
import random
import socket
import time
from io import BytesIO
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pinterest_cli import downloader, driver_installer, utils


def randdelay(a, b):
    time.sleep(random.uniform(a, b))


class Browser(object):
    def __init__(self):
        self.browser = None

    def Chrome(self, image_enable=False, incognito=False, exe_path="chromedriver.exe"):
        if not os.path.exists(exe_path):
            driver_installer.install_chrome_driver(
                Path(exe_path).parent, version="123.0.6312.86", platform="win64"
            )

        service = webdriver.chrome.service.Service(exe_path)
        chrome_options = webdriver.ChromeOptions()
        # Disable images
        # https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-disable-image-loading/
        chrome_options.add_argument(
            "--blink-settings=imagesEnabled=true"
            if image_enable
            else "--blink-settings=imagesEnabled=false"
        )
        if incognito:
            chrome_options.add_argument("--incognito")
        browser = webdriver.Chrome(options=chrome_options, service=service)
        return browser

    def Firefox(self, image_enable=False, incognito=False):
        firefox_profile = webdriver.FirefoxProfile()
        # Disable images
        if image_enable:
            firefox_profile.set_preference("permissions.default.image", 1)
        else:
            firefox_profile.set_preference("permissions.default.image", 2)
        if incognito:
            firefox_profile.set_preference("browser.privatebrowsing.autostart", True)
        browser = webdriver.Firefox(firefox_profile=firefox_profile)
        return browser

    def _download_chrome_driver_not_exist(self, exe_path):
        if not utils.file_exists(exe_path):
            print("Chrome driver does not exist. Downloading...")

            downloader.download_curl()
        else:
            print("Chrome driver exists.")


class Pinterest(object):
    def __init__(self, browser=None):
        self.browser: WebDriver = browser

    def login(self, email, password):
        self.browser.get("https://www.pinterest.com.au/login/")
        email_field = self.browser.find_element(By.ID, "email")
        email_field.send_keys(email)
        password_field = self.browser.find_element(By.ID, "password")
        password_field.send_keys(password)
        randdelay(1, 2)  # delay between 1 and 2 seconds
        password_field.send_keys(Keys.RETURN)

    def scrape(
        self,
        url,
        threshold=20,
        presistence=120,
        verbose=False,
        min_resolution=None,
        max_try=5,
    ):
        final_results = []
        previous_divs = []
        tries = 0

        try:
            self.browser.get(url)
            while threshold > 0:
                try:
                    divs = self.browser.find_elements(
                        By.CSS_SELECTOR, "div[data-test-id='pin']"
                    )
                    if divs == previous_divs:
                        tries += 1
                    else:
                        tries = 0
                    if tries > presistence:
                        if verbose:
                            print("Exiting: persistence exceeded")
                        return final_results

                    for div in divs:
                        # if div is an ad, skip
                        if self._is_div_ad(div):
                            continue
                        images = div.find_elements(By.TAG_NAME, "img")
                        for image in images:
                            src = image.get_attribute("src")
                            if src and "/236x/" in src:
                                src = src.replace("/236x/", "/originals/")
                                if min_resolution:
                                    # parse resolution
                                    res_x, rex_y = min_resolution
                                    resolution = self._try_get_img_resultion(
                                        src, max_tries=max_try, verbose=verbose
                                    )
                                    if resolution and resolution > (res_x, rex_y):
                                        final_results.append(src)
                                else:
                                    final_results.append(src)
                    previous_divs = copy.copy(divs)  # copy to avoid reference
                    final_results = list(set(final_results))  # remove duplicates

                    # Scroll down
                    dummy = self.browser.find_element(By.TAG_NAME, "a")
                    dummy.send_keys(Keys.PAGE_DOWN)
                    randdelay(1, 2)  # delay between 1 and 2 seconds
                    threshold -= 1

                except StaleElementReferenceException:
                    print("StaleElementReferenceException")
                    threshold -= 1
        except (socket.error, socket.timeout):
            print("Socket Error")
        except KeyboardInterrupt:
            return final_results
        return final_results

    def _try_get_img_resultion(
        self, src, chunk_size=1024, max_tries=5, tries=0, verbose=False
    ):
        """Get image resolution from src.

        Args:
            src (str): image source.
            chunk_size (int, optional): Chunk size. Defaults to 1024.
            max_tries (int, optional): Maximum tries. Defaults to 10.
            tries (int, DO NOT MODIFY): Current try. Defaults to 0.

        Returns:
            tuple: image resolution.
        """
        if tries > max_tries:
            if verbose:
                print("Max tries exceeded.")
            return None
        sample_chunk = downloader.download_first_chunk(src, chunk_size=chunk_size)
        try:
            img = Image.open(BytesIO(sample_chunk))
            if verbose:
                print(f"Image resolution: {img.size}, tries: {tries}, src: {src}")
            return img.size
        except IOError:
            self._try_get_img_resultion(src, chunk_size + 1024, max_tries, tries + 1)

    def _is_div_ad(self, div: WebElement):
        """Check if div is an ad.

        Args:
            div (webElement): div element.
        """
        ads_svg_path = "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M3 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6m18 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6"
        svg_elements = div.find_elements(By.TAG_NAME, "svg")
        for svg in svg_elements:
            if ads_svg_path in svg.get_attribute("innerHTML"):
                return True
