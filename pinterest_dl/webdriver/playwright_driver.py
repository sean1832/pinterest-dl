"""Playwright-based Pinterest scraping driver.

This module provides the core scraping logic using Playwright,
mirroring the functionality of the Selenium-based driver.py.
"""

import random
import time
from typing import List

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from tqdm import tqdm

from pinterest_dl.common.logging import get_logger
from pinterest_dl.domain.media import PinterestMedia

logger = get_logger(__name__)


class PlaywrightDriver:
    """Pinterest scraping driver using Playwright.

    This class handles the actual Pinterest page interactions:
    - Login flow
    - Pin scraping with scroll pagination
    - Cookie extraction
    - Ad detection
    """

    def __init__(self, page: Page) -> None:
        """Initialize driver with a Playwright page.

        Args:
            page: Playwright Page object from a browser context.
        """
        self.page = page

    @staticmethod
    def randdelay(a: float, b: float) -> None:
        """Random delay between a and b seconds."""
        time.sleep(random.uniform(a, b))

    def login(
        self, email: str, password: str, url: str = "https://www.pinterest.com/login/"
    ) -> "PlaywrightDriver":
        """Login to Pinterest with human-like behavior.

        Args:
            email: Pinterest email.
            password: Pinterest password.
            url: Pinterest login page URL.

        Returns:
            PlaywrightDriver: Self for method chaining.
        """
        print("Navigating to login page...")
        self.page.goto(url)
        self.randdelay(2, 3)  # Wait for page to fully load

        print("Filling in email...")

        # Click email field and fill (like pasting)
        email_field = self.page.locator("#email")
        email_field.click()
        self.randdelay(0.1, 0.5)  # Pause after clicking
        email_field.fill(email)

        self.randdelay(0.1, 0.5)  # Important: delay between email and password fields

        print("Filling in password...")

        # Click password field and fill (like pasting)
        password_field = self.page.locator("#password")
        password_field.click()
        self.randdelay(0.1, 0.5)  # Pause after clicking
        password_field.fill(password)

        self.randdelay(0.3, 1.0)  # Pause before submitting (humans review before clicking)

        print("Submitting login...")

        # Try to find and click the login button
        try:
            login_button = self.page.locator('button[type="submit"]').first
            login_button.click()
        except Exception:
            # Fallback to Enter key if button not found
            password_field.press("Enter")

        # Wait for navigation - use 'load' instead of 'networkidle' since Pinterest
        # keeps making background requests that prevent networkidle from resolving
        print("Waiting for login to process...")
        self.page.wait_for_load_state("load")

        # Give a moment for redirect to happen after login
        self.randdelay(1, 2)

        # Check if we're no longer on the login page (indicates success)
        if "/login" not in self.page.url:
            print("Login Successful")
        print("(If prompted, please complete any CAPTCHA or 2FA in the browser window)")
        return self

    def get_cookies(self, after_sec: float = 5) -> List[dict]:
        """Capture cookies from the current browser context.

        Args:
            after_sec: Time in seconds to wait before capturing cookies.

        Returns:
            List of cookie dictionaries in Selenium-compatible format.
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

        # Get cookies from Playwright context
        cookies = self.page.context.cookies()

        # Convert to Selenium-compatible format (expiry vs expires)
        selenium_cookies = []
        for cookie in cookies:
            sel_cookie = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
            }
            # Playwright uses 'expires', Selenium uses 'expiry'
            if "expires" in cookie and cookie["expires"] > 0:
                sel_cookie["expiry"] = int(cookie["expires"])
            selenium_cookies.append(sel_cookie)

        print("Cookies Captured")
        return selenium_cookies

    def scrape(
        self,
        url: str,
        num: int = 20,
        timeout: float = 3,
        verbose: bool = False,
        ensure_alt: bool = False,
    ) -> List[PinterestMedia]:
        """Scrape pins from a Pinterest board/search page.

        Args:
            url: Pinterest URL to scrape.
            num: Maximum number of images to scrape.
            timeout: Seconds to wait before giving up when no new images appear.
            verbose: Print detailed progress information.
            ensure_alt: Only include images that have alt text.

        Returns:
            List of PinterestMedia objects with scraped data.
        """
        unique_results = set()
        imgs_data: List[PinterestMedia] = []
        previous_ids = set()
        tries = 0
        pbar = tqdm(total=num, desc="Scraping")

        try:
            self.page.goto(url, wait_until="domcontentloaded")

            # Wait for pin elements to appear instead of networkidle
            # Pinterest never reaches networkidle due to constant background requests
            try:
                self.page.locator("div[data-test-id='pin']").first.wait_for(timeout=15000)
            except PlaywrightTimeoutError:
                if verbose:
                    logger.debug("No pins found on initial load, continuing anyway...")

            while len(unique_results) < num:
                try:
                    # Find all pin divs
                    divs = self.page.locator("div[data-test-id='pin']").all()
                    current_ids = set()

                    for div in divs:
                        pin_id = div.get_attribute("data-test-pin-id")
                        if pin_id:
                            current_ids.add(pin_id)

                    # Check if we got new pins
                    if current_ids == previous_ids:
                        tries += 1
                        time.sleep(1)
                    else:
                        tries = 0

                    if tries > timeout:
                        logger.warning(
                            f"Scraping timeout: no new pins found after {timeout} seconds on {url}. Collected {len(unique_results)} images so far."
                        )
                        break

                    # Process each pin div
                    for div in divs:
                        if len(unique_results) >= num:
                            break

                        # Check for ads
                        if self._is_div_ad(div):
                            continue

                        pin_id = div.get_attribute("data-test-pin-id")
                        if not pin_id:
                            continue

                        # Get link and aria-label (cleaner alt text source)
                        link_elem = div.locator("a").first
                        href = link_elem.get_attribute("href") if link_elem else None
                        aria_label = link_elem.get_attribute("aria-label") if link_elem else ""

                        # Clean up aria-label: remove " Pin page" suffix
                        if aria_label and aria_label.endswith(" Pin page"):
                            aria_label = aria_label[: -len(" Pin page")]

                        # Get images
                        images = div.locator("img").all()
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
                                        int(pin_id),
                                        src,
                                        alt,
                                        href,
                                        resolution=(
                                            0,
                                            0,
                                        ),  # Resolution not available in this context
                                    )
                                    imgs_data.append(img_data)
                                    pbar.update(1)

                                    if verbose:
                                        logger.debug(f"{src} {alt}")

                                    if len(unique_results) >= num:
                                        break

                    previous_ids = current_ids.copy()

                    # Scroll down
                    self.page.keyboard.press("PageDown")
                    self.randdelay(1, 2)

                except PlaywrightTimeoutError:
                    if verbose:
                        logger.debug("Timeout waiting for elements")

        except Exception as e:
            logger.error(
                f"Unexpected error during scraping of {url}: {type(e).__name__}: {e}",
                exc_info=verbose,
            )
        finally:
            pbar.close()
            if verbose:
                logger.debug(f"Scraped {len(imgs_data)} images")

        return imgs_data

    def _is_div_ad(self, div) -> bool:
        """Check if a pin div is an advertisement.

        Args:
            div: Playwright Locator for the div element.

        Returns:
            True if the div is an ad, False otherwise.
        """
        ads_svg_path = "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M3 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6m18 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6"

        try:
            svg_elements = div.locator("svg").all()
            for svg in svg_elements:
                inner_html = svg.inner_html()
                if inner_html and ads_svg_path in inner_html:
                    return True
        except Exception:
            pass

        return False
