"""WebDriver module for Pinterest scraping.

This module provides Selenium WebDriver-based scraping functionality.
"""

import warnings

from .driver import Driver

__all__ = ["Driver"]


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
