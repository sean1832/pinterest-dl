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

from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.media import PinterestMedia

logger = get_logger(__name__)


class Driver:
    def __init__(self, webdriver: WebDriver) -> None:
        self.webdriver: WebDriver = webdriver

    @staticmethod
    def randdelay(a, b) -> None:
        time.sleep(random.uniform(a, b))

    def login(
        self, email: str, password: str, url: str = "https://www.pinterest.com/login/"
    ) -> "Driver":
        """Login to Pinterest.

        Args:
            email (str): Pinterest email.
            password (str): Pinterest password.
            url (str): Pinterest login page url. Defaults to "https://www.pinterest.com/login/".

        Returns:
            Driver: Driver object.
        """
        self.webdriver.get(url)
        email_field = self.webdriver.find_element(By.ID, "email")
        email_field.send_keys(email)
        password_field = self.webdriver.find_element(By.ID, "password")
        password_field.send_keys(password)
        self.randdelay(1, 2)  # delay between 1 and 2 seconds
        password_field.send_keys(Keys.RETURN)
        print("Login Successful")
        print("(If prompted, please complete any CAPTCHA or 2FA in the browser window)")
        return self

    def get_cookies(self, after_sec: float = 5) -> List[dict]:
        """Capture cookies to a file.

        Args:
            out_path (str | Path, optional): output file path. Defaults to "cookies.json".
            after_sec (float, optional): time in second to wait before capturing cookies. Defaults to 5.
        """
        print(f"Waiting {after_sec} seconds before capturing cookies...")
        print("(Complete any verification steps in the browser if needed)")
        for remaining in range(int(after_sec), 0, -1):
            print(f"  Capturing in {remaining}...", end="\r")
            time.sleep(1)
        # Handle fractional seconds
        if after_sec % 1 > 0:
            time.sleep(after_sec % 1)
        print(" " * 30, end="\r")  # Clear the countdown line
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
                        logger.warning(
                            f"Scraping timeout: no new pins found after {timeout} seconds on {url}. Collected {len(unique_results)} images so far."
                        )
                        break

                    for div in divs:
                        if self._is_div_ad(div) or len(unique_results) >= num:
                            continue
                        images = div.find_elements(By.TAG_NAME, "img")
                        link_elem = div.find_element(By.TAG_NAME, "a")
                        href = link_elem.get_attribute("href")
                        aria_label = link_elem.get_attribute("aria-label") or ""

                        # Clean up aria-label: remove " Pin page" suffix
                        if aria_label.endswith(" Pin page"):
                            aria_label = aria_label[: -len(" Pin page")]

                        id = div.get_attribute("data-test-pin-id")
                        if not id:
                            continue
                        for image in images:
                            # Try aria-label first (cleaner), then fall back to img alt
                            alt = aria_label or image.get_attribute("alt") or ""

                            # Strip "This may contain: " prefix from alt text
                            if alt.startswith("This may contain: "):
                                alt = alt[len("This may contain: ") :]

                            if ensure_alt and not alt.strip():
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
                                        logger.debug(f"{src} {alt}")
                                    if len(unique_results) >= num:
                                        break

                    previous_divs = copy.copy(divs)  # copy to avoid reference

                    # Scroll down
                    dummy = self.webdriver.find_element(By.TAG_NAME, "a")
                    dummy.send_keys(Keys.PAGE_DOWN)
                    self.randdelay(1, 2)  # delay between 1 and 2 seconds

                except StaleElementReferenceException:
                    if verbose:
                        logger.debug("StaleElementReferenceException")

        except (socket.error, socket.timeout) as e:
            logger.error(f"Network error during scraping of {url}: {type(e).__name__}")
        finally:
            pbar.close()
            if verbose:
                logger.debug(f"Scraped {len(imgs_data)} images")
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
