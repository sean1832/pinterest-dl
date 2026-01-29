"""Tests for backward compatibility of deprecated APIs."""

import warnings

import pytest

from pinterest_dl import PinterestDL
from pinterest_dl.scrapers import ApiScraper, WebDriverScraper


class TestDeprecatedScraperNames:
    """Test that deprecated scraper class names still work with warnings."""

    def test_deprecated_scraper_api_import_triggers_warning(self):
        """Test that importing _ScraperAPI triggers DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match=r"_ScraperAPI is deprecated.*2\.1\.0"):
            from pinterest_dl.scrapers import _ScraperAPI

            # Verify it returns the correct class
            assert _ScraperAPI is ApiScraper

    def test_deprecated_scraper_webdriver_import_triggers_warning(self):
        """Test that importing _ScraperWebdriver triggers DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match=r"_ScraperWebdriver is deprecated.*2\.1\.0"):
            from pinterest_dl.scrapers import _ScraperWebdriver

            # Verify it returns the correct class
            assert _ScraperWebdriver is WebDriverScraper

    def test_deprecated_scraper_api_instantiation_works(self):
        """Test that old name can still instantiate scrapers."""
        with pytest.warns(DeprecationWarning):
            from pinterest_dl.scrapers import _ScraperAPI

            scraper = _ScraperAPI(timeout=5, verbose=False)  # noqa: F841
            # Should be an instance of ApiScraper
            assert isinstance(scraper, ApiScraper)

    def test_factory_returns_new_class_names(self):
        """Test that PinterestDL factory returns new class instances."""
        scraper = PinterestDL.with_api(timeout=5, verbose=False)
        # Should return ApiScraper, not _ScraperAPI
        assert type(scraper).__name__ == "ApiScraper"
        assert isinstance(scraper, ApiScraper)

    def test_new_class_names_work_without_warnings(self):
        """Test that new class names don't trigger warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            # These should NOT raise DeprecationWarning
            scraper = ApiScraper(timeout=5, verbose=False)
            assert isinstance(scraper, ApiScraper)

    def test_deprecation_message_content(self):
        """Test that deprecation messages are clear and helpful."""
        with pytest.warns(DeprecationWarning) as record:
            from pinterest_dl.scrapers import _ScraperAPI  # noqa: F401

        # Should have at least one warning
        assert len(record) >= 1
        warning_message = str(record[0].message)

        # Message should mention:
        # 1. The deprecated name
        assert "_ScraperAPI" in warning_message
        # 2. The new name to use
        assert "ApiScraper" in warning_message
        # 3. The removal version
        assert "2.1.0" in warning_message
