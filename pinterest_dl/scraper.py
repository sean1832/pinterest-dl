import copy
import os
import random
import socket
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from pinterest_dl import driver_installer, utils


def randdelay(a, b):
    time.sleep(random.uniform(a, b))


class Browser(object):
    def __init__(self):
        self.browser = None

    def Chrome(
        self, image_enable=False, incognito=False, exe_path="chromedriver.exe", headful=False
    ):
        if not os.path.exists(exe_path):
            driver_installer.install_chrome_driver(
                utils.get_appdata_dir(), version="123.0.6312.86", platform="win64"
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
        chrome_options.add_argument("--log-level=3")  # Suppress most logs
        if incognito:
            print("Running in incognito mode")
            chrome_options.add_argument("--incognito")
        if not headful:
            print("Running in headless mode")
            chrome_options.add_argument("--headless=new")
        browser = webdriver.Chrome(options=chrome_options, service=service)
        return browser

    def Firefox(self, image_enable=False, incognito=False, headful=False):
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


class Pinterest(object):
    def __init__(self, browser=None):
        self.browser: WebDriver = browser

    # currently not used
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
        limit=20,
        presistence=120,
        verbose=False,
    ):
        unique_results = set()  # Use a set to store unique results
        imgs_data = []  # Store image data
        previous_divs = []
        tries = 0
        pbar = tqdm(total=limit, desc="Scraping")
        try:
            self.browser.get(url)
            while len(unique_results) < limit:
                try:
                    divs = self.browser.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
                    if divs == previous_divs:
                        tries += 1
                    else:
                        tries = 0
                    if tries > presistence:
                        if verbose:
                            print("Exiting: persistence exceeded")
                        break

                    for div in divs:
                        if self._is_div_ad(div) or len(unique_results) >= limit:
                            continue
                        images = div.find_elements(By.TAG_NAME, "img")
                        for image in images:
                            alt = image.get_attribute("alt")
                            src = image.get_attribute("src")
                            if src and "/236x/" in src:
                                src = src.replace("/236x/", "/originals/")
                                src_763 = src.replace("/originals/", "/736x/")
                                if src not in unique_results:
                                    unique_results.add(src)
                                    img_data = {"src": src, "alt": alt, "fallback": src_763}
                                    imgs_data.append(img_data)
                                    pbar.update(1)
                                    if verbose:
                                        print(src, alt)
                                    if len(unique_results) >= limit:
                                        break

                    previous_divs = copy.copy(divs)  # copy to avoid reference

                    # Scroll down
                    dummy = self.browser.find_element(By.TAG_NAME, "a")
                    dummy.send_keys(Keys.PAGE_DOWN)
                    randdelay(1, 2)  # delay between 1 and 2 seconds

                except StaleElementReferenceException:
                    print("StaleElementReferenceException")

        except (socket.error, socket.timeout):
            print("Socket Error")
        finally:
            pbar.close()
            if verbose:
                print(f"Scraped {len(imgs_data)} images")
            return imgs_data

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
