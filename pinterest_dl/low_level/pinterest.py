import copy
import json
import random
import socket
import time
from pathlib import Path
from typing import List

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from pinterest_dl.data_model.pinterest_image import PinterestImage


class Pinterest:
    def __init__(self, browser: WebDriver) -> None:
        self.browser: WebDriver = browser

    @staticmethod
    def randdelay(a, b) -> None:
        time.sleep(random.uniform(a, b))

    def login(
        self, email: str, password: str, url: str = "https://www.pinterest.com/login/"
    ) -> "Pinterest":
        """Login to Pinterest.

        Args:
            email (str): Pinterest email.
            password (str): Pinterest password.
            url (str): Pinterest login page url. Defaults to "https://www.pinterest.com/login/".

        Returns:
            Pinterest: Pinterest object.
        """
        self.browser.get(url)
        email_field = self.browser.find_element(By.ID, "email")
        email_field.send_keys(email)
        password_field = self.browser.find_element(By.ID, "password")
        password_field.send_keys(password)
        self.randdelay(1, 2)  # delay between 1 and 2 seconds
        password_field.send_keys(Keys.RETURN)
        print("Login Successful")
        return self

    def capture_cookies(self, out_path: str | Path = "cookies.json", after_sec: float = 5) -> None:
        """Capture cookies to a file.

        Args:
            out_path (str | Path, optional): output file path. Defaults to "cookies.json".
            after_sec (float, optional): time in second to wait before capturing cookies. Defaults to 5.
        """
        time.sleep(after_sec)
        cookies = self.browser.get_cookies()
        with open(out_path, "w") as f:
            json.dump(cookies, f)
        print("Cookies Captured")

    def scrape(
        self,
        url: str,
        limit: int = 20,
        timeout: float = 3,
        verbose: bool = False,
    ) -> List[PinterestImage]:
        unique_results = set()  # Use a set to store unique results
        imgs_data: List[PinterestImage] = []  # Store image data
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
                        time.sleep(1)  # delay 1 second
                    else:
                        tries = 0
                    if tries > timeout:
                        print(f"\nTimeout: no new images in ({timeout}) seconds.")
                        break

                    for div in divs:
                        if self._is_div_ad(div) or len(unique_results) >= limit:
                            continue
                        images = div.find_elements(By.TAG_NAME, "img")
                        href = div.find_element(By.TAG_NAME, "a").get_attribute("href")
                        for image in images:
                            alt = image.get_attribute("alt")
                            src = image.get_attribute("src")
                            if src and "/236x/" in src:
                                src = src.replace("/236x/", "/originals/")
                                src_736 = src.replace("/originals/", "/736x/")
                                if src not in unique_results:
                                    unique_results.add(src)
                                    img_data = PinterestImage(src, alt, href, [src_736])
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
                    self.randdelay(1, 2)  # delay between 1 and 2 seconds

                except StaleElementReferenceException:
                    if verbose:
                        print("\nStaleElementReferenceException")

        except (socket.error, socket.timeout):
            print("Socket Error")
        finally:
            pbar.close()
            if verbose:
                print(f"Scraped {len(imgs_data)} images")
            return imgs_data

    def _is_div_ad(self, div: WebElement) -> bool:
        """Check if div is an ad.

        Args:
            div (webElement): div element.
        """
        ads_svg_path = "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M3 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6m18 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6"
        svg_elements = div.find_elements(By.TAG_NAME, "svg")
        for svg in svg_elements:
            inner_html = svg.get_attribute("innerHTML")
            if inner_html and ads_svg_path in inner_html:
                return True
        return False
