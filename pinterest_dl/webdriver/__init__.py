"""WebDriver module for Pinterest scraping.

This module provides browser-based scraping functionality using Playwright:
- PlaywrightDriver: Pinterest page interactions (login, scrape, cookies)
- PlaywrightBrowser: Browser lifecycle management for Playwright
"""

from pinterest_dl.common.ensure_playwright import ensure_playwright

__all__ = ["PlaywrightDriver", "PlaywrightBrowser"]


def __getattr__(name: str) -> object:
    # Lazily import the playwright-backed drivers so this package can be imported
    # without the optional playwright dependency installed.
    if name == "PlaywrightBrowser":
        ensure_playwright()
        from .playwright_browser import PlaywrightBrowser

        return PlaywrightBrowser
    if name == "PlaywrightDriver":
        ensure_playwright()
        from .playwright_driver import PlaywrightDriver

        return PlaywrightDriver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
