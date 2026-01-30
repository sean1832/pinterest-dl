"""Playwright browser initialization module.

This module provides browser initialization using Playwright, supporting
Chromium and Firefox browsers with various options (headless, incognito, etc.).
"""

from typing import Literal, Tuple

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from pinterest_dl.common.logging import get_logger

logger = get_logger(__name__)


class PlaywrightBrowser:
    """Browser initialization using Playwright.

    Playwright handles browser binary management automatically via `playwright install`.
    No driver management required unlike Selenium.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def launch(
        self,
        browser_type: Literal["chromium", "firefox"] = "chromium",
        headless: bool = True,
        incognito: bool = True,
        image_enable: bool = False,
    ) -> "PlaywrightBrowser":
        """Launch browser with specified options.

        Args:
            browser_type: Browser to use ('chromium' or 'firefox').
            headless: Run in headless mode (no visible window).
            incognito: Use incognito/private browsing mode.
            image_enable: Enable image loading (disabled by default for performance).

        Returns:
            PlaywrightBrowser: Self for method chaining.
        """
        self._playwright = sync_playwright().start()

        # Select browser type
        if browser_type == "firefox":
            browser_launcher = self._playwright.firefox
        else:
            browser_launcher = self._playwright.chromium

        # Browser launch arguments to appear more like a real browser
        launch_args = []
        if browser_type == "chromium":
            launch_args = [
                "--disable-blink-features=AutomationControlled",  # Hide automation
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]

        # Launch browser
        self._browser = browser_launcher.launch(
            headless=headless,
            args=launch_args if launch_args else None,
        )

        # Create context with stealth settings to avoid detection
        # Each context is isolated like an incognito window
        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation", "notifications"],
            "color_scheme": "light",
        }

        self._context = self._browser.new_context(**context_options)

        # Disable images if requested (via route interception)
        if not image_enable:
            # Block by resource type - more efficient than pattern matching
            self._context.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type == "image"
                else route.continue_(),
            )

        # Create page
        self._page = self._context.new_page()

        if not headless:
            logger.debug("Running in headful mode (browser window will open)")
        if incognito:
            logger.debug("Running in incognito mode (isolated context)")

        return self

    @property
    def page(self) -> Page:
        """Get the current page object."""
        if self._page is None:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._page

    @property
    def context(self) -> BrowserContext:
        """Get the current browser context."""
        if self._context is None:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._context

    @property
    def browser(self) -> Browser:
        """Get the browser instance."""
        if self._browser is None:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._browser

    def close(self) -> None:
        """Close browser and cleanup resources."""
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        self._page = None

    def __enter__(self) -> "PlaywrightBrowser":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def create_browser(
    browser_type: Literal["chromium", "firefox"] = "chromium",
    headless: bool = True,
    incognito: bool = True,
    image_enable: bool = False,
) -> Tuple[PlaywrightBrowser, Page]:
    """Convenience function to create and launch a browser.

    Args:
        browser_type: Browser to use ('chromium' or 'firefox').
        headless: Run in headless mode.
        incognito: Use incognito mode.
        image_enable: Enable image loading.

    Returns:
        Tuple of (PlaywrightBrowser instance, Page object).
    """
    pw_browser = PlaywrightBrowser()
    pw_browser.launch(
        browser_type=browser_type,
        headless=headless,
        incognito=incognito,
        image_enable=image_enable,
    )
    return pw_browser, pw_browser.page
