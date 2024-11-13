__version__ = "0.2.0"
__description__ = "An unofficial Pinterest image downloader"

from typing import Literal

from pinterest_dl._pinterest_dl_api import _PinterestDLAPI
from pinterest_dl._pinterest_dl_webdriver import _PinterestDLWebdriver


class PinterestDL:
    """PinterestDL is a class for scraping, downloading, and managing images from Pinterest.
    Users can scrape pins, download images, add captions, and prune by resolution.
    """

    @staticmethod
    def with_api(timeout: float = 3, verbose: bool = False) -> "_PinterestDLAPI":
        """Scrape pinterest using unofficial API. This is faster than using a browser but may be less reliable.

        Args:
            timeout (float): Timeout in seconds for requests.
            verbose (bool): Enable verbose logging.

        Returns:
            PinterestDL: Instance of PinterestDL with the requests library.
        """
        return _PinterestDLAPI(verbose=verbose, timeout=timeout)

    @staticmethod
    def with_browser(
        browser_type: Literal["chrome", "firefox"],
        timeout: float = 3,
        headless: bool = True,
        incognito: bool = True,
        verbose: bool = False,
    ) -> "_PinterestDLWebdriver":
        """Scrape Pinterest using a webdriver (Selenium). This is slower but more reliable.

        Args:
            browser_type (Literal["chrome", "firefox"]): Browser type to use ('chrome' or 'firefox').
            timeout (float): Timeout in seconds for browser operations.
            headless (bool): Run browser in headless mode.
            incognito (bool): Use incognito mode in the browser.
            verbose (bool): Enable verbose logging.

        Returns:
            PinterestDL: Instance of PinterestDL with an initialized browser.
        """
        webdriver = _PinterestDLWebdriver._initialize_webdriver(browser_type, headless, incognito)
        return _PinterestDLWebdriver(webdriver, timeout, verbose)
