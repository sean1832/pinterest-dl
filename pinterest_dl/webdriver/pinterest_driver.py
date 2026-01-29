import copy
import random
import socket
import time
from typing import List

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from pinterest_dl.data_model.pinterest_media import PinterestMedia


class PinterestDriver:
    def __init__(self, webdriver: WebDriver) -> None:
        self.webdriver: WebDriver = webdriver

    @staticmethod
    def randdelay(a, b) -> None:
        time.sleep(random.uniform(a, b))

    def login(
        self, email: str, password: str, url: str = "https://www.pinterest.com/login/"
    ) -> "PinterestDriver":
        """Login to Pinterest.

        Args:
            email (str): Pinterest email.
            password (str): Pinterest password.
            url (str): Pinterest login page url. Defaults to "https://www.pinterest.com/login/".

        Returns:
            Pinterest: Pinterest object.
        """
        self.webdriver.get(url)
        email_field = self.webdriver.find_element(By.ID, "email")
        email_field.send_keys(email)
        password_field = self.webdriver.find_element(By.ID, "password")
        password_field.send_keys(password)
        self.randdelay(1, 2)  # delay between 1 and 2 seconds
        password_field.send_keys(Keys.RETURN)
        print("Login Successful")
        return self

    def get_cookies(self, after_sec: float = 5) -> List[dict]:
        """Capture cookies to a file.

        Args:
            out_path (str | Path, optional): output file path. Defaults to "cookies.json".
            after_sec (float, optional): time in second to wait before capturing cookies. Defaults to 5.
        """
        print(f"Waiting for {after_sec} seconds before capturing cookies...")
        time.sleep(after_sec)
        cookies = self.webdriver.get_cookies()
        print("Cookies Captured")
        return cookies

    def scrape(
        self,
        url: str,
        num: int = 20,
        timeout: float = 3,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> List[PinterestMedia]:
        unique_results = set()  # Use a set to store unique results
        imgs_data: List[PinterestMedia] = []  # Store image data
        previous_divs = []
        tries = 0
        pbar = tqdm(total=num, desc="Scraping")
        try:
            self.webdriver.get(url)
            while len(unique_results) < num:
                try:
                    divs = self.webdriver.find_elements(By.CSS_SELECTOR, "div[data-test-id='pin']")
                    if divs == previous_divs:
                        tries += 1
                        time.sleep(1)  # delay 1 second
                    else:
                        tries = 0
                    if tries > timeout:
                        print(f"\nTimeout: no new images in ({timeout}) seconds.")
                        break

                    for div in divs:
                        if self._is_div_ad(div) or len(unique_results) >= num:
                            continue
                        images = div.find_elements(By.TAG_NAME, "img")
                        href = div.find_element(By.TAG_NAME, "a").get_attribute("href")
                        id = div.get_attribute("data-test-pin-id")
                        if not id:
                            continue
                        for image in images:
                            alt = image.get_attribute("alt")
                            if ensure_alt and (not alt or not alt.strip()):
                                continue
                            src = image.get_attribute("src")
                            if src and "/236x/" in src:
                                src = src.replace("/236x/", "/originals/")
                                if src not in unique_results:
                                    unique_results.add(src)
                                    img_data = PinterestMedia(
                                        int(id),
                                        src,
                                        alt,
                                        href,
                                        resolution=(
                                            0,
                                            0,
                                        ),  # resolution is not available in this context
                                    )  # TODO: support streams for webdriver
                                    imgs_data.append(img_data)
                                    pbar.update(1)
                                    if verbose:
                                        print(src, alt)
                                    if len(unique_results) >= num:
                                        break

                    previous_divs = copy.copy(divs)  # copy to avoid reference

                    # Scroll down
                    dummy = self.webdriver.find_element(By.TAG_NAME, "a")
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
