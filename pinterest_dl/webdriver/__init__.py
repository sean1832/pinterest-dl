"""WebDriver module for Pinterest scraping.

This module provides browser-based scraping functionality:
- PlaywrightDriver: Recommended, uses Playwright (stable, cross-platform)
- PlaywrightBrowser: Browser management for Playwright
- Driver: Legacy Selenium-based driver (for backward compatibility)
"""

from .driver import Driver
from .playwright_browser import PlaywrightBrowser
from .playwright_driver import PlaywrightDriver

__all__ = ["Driver", "PlaywrightDriver", "PlaywrightBrowser"]
