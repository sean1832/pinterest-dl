"""Pinterest scrapers module.

This module provides scraper implementations for Pinterest:
- ApiScraper: Fast API-based scraping
- WebDriverScraper: Selenium-based scraping
"""

import warnings

from .api_scraper import ApiScraper
from .webdriver_scraper import WebDriverScraper

__all__ = ["ApiScraper", "WebDriverScraper"]


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for old class names.
    
    This function is called when an attribute is not found in the module.
    It provides deprecated aliases for the old underscore-prefixed class names.
    
    Deprecated in 2.0.0, will be removed in 2.1.0:
    - _ScraperAPI -> use ApiScraper instead
    - _ScraperWebdriver -> use WebDriverScraper instead
    """
    if name == "_ScraperAPI":
        warnings.warn(
            "_ScraperAPI is deprecated and will be removed in version 2.1.0. "
            "Use ApiScraper instead: from pinterest_dl.scrapers import ApiScraper",
            DeprecationWarning,
            stacklevel=2,
        )
        return ApiScraper
    elif name == "_ScraperWebdriver":
        warnings.warn(
            "_ScraperWebdriver is deprecated and will be removed in version 2.1.0. "
            "Use WebDriverScraper instead: from pinterest_dl.scrapers import WebDriverScraper",
            DeprecationWarning,
            stacklevel=2,
        )
        return WebDriverScraper
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
