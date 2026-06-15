"""Tests for Playwright integration.

This test suite verifies the Playwright-based scraping functionality,
including browser initialization, cookie handling, and scraper operations.
"""

import warnings

import pytest

from pinterest_dl import PinterestDL
from pinterest_dl.scrapers import PlaywrightScraper


class TestPlaywrightImports:
    """Test that Playwright modules can be imported correctly."""

    def test_playwright_scraper_import(self):
        """Test that PlaywrightScraper can be imported from scrapers."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            from pinterest_dl.scrapers import PlaywrightScraper

            assert PlaywrightScraper is not None

    def test_playwright_driver_import(self):
        """Test that PlaywrightDriver can be imported from webdriver."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.webdriver import PlaywrightDriver

            assert PlaywrightDriver is not None

    def test_playwright_browser_import(self):
        """Test that PlaywrightBrowser can be imported from webdriver."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.webdriver import PlaywrightBrowser

            assert PlaywrightBrowser is not None

    def test_playwright_in_all_exports(self):
        """Test that Playwright classes are in __all__ exports."""
        from pinterest_dl import scrapers, webdriver

        assert "PlaywrightScraper" in scrapers.__all__
        assert "PlaywrightDriver" in webdriver.__all__
        assert "PlaywrightBrowser" in webdriver.__all__


class TestPinterestDLFactory:
    """Test that PinterestDL factory methods work correctly."""

    def test_with_browser_returns_playwright_scraper(self):
        """Test that with_browser() returns a PlaywrightScraper instance."""
        # Note: This test requires Playwright browsers to be installed
        # Skip if Playwright is not properly set up
        try:
            scraper = PinterestDL.with_browser(
                browser_type="chromium",
                headless=True,
            )
            assert isinstance(scraper, PlaywrightScraper)
            scraper.close()
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "executable doesn't exist" in error_msg
                or "playwright install" in error_msg
                or "asyncio" in error_msg
            ):
                pytest.skip(
                    "Playwright browsers not installed or asyncio conflict. Run: playwright install chromium"
                )
            raise


class TestCookieConversion:
    """Test cookie format conversion for the stored cookie format."""

    def test_to_playwright_conversion(self):
        """Test converting stored cookies to Playwright format."""
        from pinterest_dl.domain.cookies import CookieJar

        stored_cookies = [
            {
                "name": "test_cookie",
                "value": "test_value",
                "domain": ".pinterest.com",
                "path": "/",
                "expiry": 1735689600,
                "secure": True,
            }
        ]

        pw_cookies = CookieJar.to_playwright(stored_cookies)

        assert len(pw_cookies) == 1
        assert pw_cookies[0]["name"] == "test_cookie"
        assert pw_cookies[0]["value"] == "test_value"
        assert pw_cookies[0]["domain"] == ".pinterest.com"
        # Playwright uses 'expires' instead of 'expiry'
        assert "expires" in pw_cookies[0]
        assert pw_cookies[0]["expires"] == 1735689600.0
        # Playwright includes additional fields
        assert "httpOnly" in pw_cookies[0]
        assert "sameSite" in pw_cookies[0]

    def test_from_cookies(self):
        """Test building a CookieJar from stored cookie dicts."""
        from pinterest_dl.domain.cookies import CookieJar

        stored_cookies = [
            {
                "name": "session",
                "value": "xyz789",
                "domain": ".pinterest.com",
                "path": "/",
                "expiry": 1735689600,
                "secure": True,
            }
        ]

        jar = CookieJar.from_cookies(stored_cookies)

        # Verify cookie was added
        cookie = jar.get("session", domain=".pinterest.com")
        assert cookie == "xyz789"


class TestPlaywrightScraperMethods:
    """Test PlaywrightScraper instance methods (without launching browser)."""

    def test_sanitize_cookies(self):
        """Test that _sanitize_cookies() enforces Pinterest domain."""
        cookies = [
            {"name": "test", "value": "123", "domain": "example.com"},
            {"name": "test2", "value": "456", "domain": ".pinterest.com"},
        ]

        sanitized = PlaywrightScraper._sanitize_cookies(cookies)

        assert sanitized[0]["domain"] == ".pinterest.com"
        assert sanitized[1]["domain"] == ".pinterest.com"

    def test_create_factory_method_exists(self):
        """Test that PlaywrightScraper.create() factory method exists."""
        assert hasattr(PlaywrightScraper, "create")
        assert callable(PlaywrightScraper.create)
