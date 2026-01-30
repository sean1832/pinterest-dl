"""WebDriver module for Pinterest scraping.

This module provides browser-based scraping functionality:
- PlaywrightDriver: Recommended, uses Playwright (stable, cross-platform)
- PlaywrightBrowser: Browser management for Playwright
- Driver: Legacy Selenium-based driver (for backward compatibility)
"""

import warnings

from .driver import Driver
from .playwright_browser import PlaywrightBrowser
from .playwright_driver import PlaywrightDriver

__all__ = ["Driver", "PlaywrightDriver", "PlaywrightBrowser"]


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for renamed classes."""
    if name == "PinterestDriver":
        warnings.warn(
            "PinterestDriver has been renamed to Driver and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.webdriver import Driver",
            DeprecationWarning,
            stacklevel=2,
        )
        return Driver

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
