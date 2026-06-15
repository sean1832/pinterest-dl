"""Pinterest scrapers module.

This module provides scraper implementations for Pinterest:
- ApiScraper: Fast API-based scraping (default)
- PlaywrightScraper: Playwright-based browser scraping (recommended for browser mode)
"""

from pinterest_dl.common.ensure_playwright import ensure_playwright

from .api_scraper import ApiScraper

__all__ = ["ApiScraper", "PlaywrightScraper"]


def __getattr__(name: str) -> object:
    # Lazily expose PlaywrightScraper so importing this package (e.g. for
    # `operations`) does not require the optional playwright dependency.
    if name == "PlaywrightScraper":
        ensure_playwright()
        from .playwright_scraper import PlaywrightScraper

        return PlaywrightScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
