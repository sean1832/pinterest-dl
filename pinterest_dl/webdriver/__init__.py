"""WebDriver module for Pinterest scraping.

This module provides browser-based scraping functionality using Playwright:
- PlaywrightDriver: Pinterest page interactions (login, scrape, cookies)
- PlaywrightBrowser: Browser lifecycle management for Playwright
"""

from .playwright_browser import PlaywrightBrowser
from .playwright_driver import PlaywrightDriver

__all__ = ["PlaywrightDriver", "PlaywrightBrowser"]
