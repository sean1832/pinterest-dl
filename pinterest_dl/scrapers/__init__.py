"""Pinterest scrapers module.

This module provides scraper implementations for Pinterest:
- ApiScraper: Fast API-based scraping (default)
- PlaywrightScraper: Playwright-based browser scraping (recommended for browser mode)
"""

from .api_scraper import ApiScraper
from .playwright_scraper import PlaywrightScraper

__all__ = ["ApiScraper", "PlaywrightScraper"]
