"""Tests for backward compatibility of deprecated APIs.

This test suite ensures that all deprecated APIs continue to work with proper
deprecation warnings, maintaining backward compatibility for users upgrading to 1.0.0.
"""

import warnings

import pytest

from pinterest_dl import PinterestDL
from pinterest_dl.scrapers import ApiScraper, WebDriverScraper


class TestPublicAPIStability:
    """Test that the main public API remains stable and functional."""

    def test_pinterest_dl_factory_api(self):
        """Test PinterestDL.with_api() factory method."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            scraper = PinterestDL.with_api(timeout=5, verbose=False)
            assert scraper is not None
            assert isinstance(scraper, ApiScraper)

    def test_pinterest_dl_factory_browser(self):
        """Test PinterestDL.with_browser() factory method (skip if Chromium unavailable)."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")  # Turn warnings into errors
                scraper = PinterestDL.with_browser(browser_type="chromium", headless=True)
                assert scraper is not None
                from pinterest_dl.scrapers import PlaywrightScraper

                assert isinstance(scraper, PlaywrightScraper)
                scraper.close()  # Clean up
        except Exception:
            # Skip test if Chromium is not available - not a backward compatibility issue
            pytest.skip("Chromium not available for testing")

    def test_pinterest_dl_factory_methods_exist(self):
        """Test that PinterestDL factory methods exist and are accessible."""
        # These should be accessible without warnings
        assert hasattr(PinterestDL, "with_api")
        assert hasattr(PinterestDL, "with_browser")
        assert callable(PinterestDL.with_api)
        assert callable(PinterestDL.with_browser)

    def test_pinterest_media_import_from_main(self):
        """Test that PinterestMedia can be imported from main package."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl import PinterestMedia

            assert PinterestMedia is not None


class TestDeprecatedScraperNames:
    """Test that deprecated scraper class names still work with warnings."""

    def test_deprecated_scraper_api_import_triggers_warning(self):
        """Test that importing _ScraperAPI triggers DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match=r"_ScraperAPI is deprecated.*1\.1\.0"):
            from pinterest_dl.scrapers import _ScraperAPI

            # Verify it returns the correct class
            assert _ScraperAPI is ApiScraper

    def test_deprecated_scraper_webdriver_import_triggers_warning(self):
        """Test that importing _ScraperWebdriver triggers DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match=r"_ScraperWebdriver is deprecated.*1\.1\.0"):
            from pinterest_dl.scrapers import _ScraperWebdriver

            # Verify it returns the correct class
            assert _ScraperWebdriver is WebDriverScraper

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
        assert "1.1.0" in warning_message


class TestDeprecatedDataModelModule:
    """Test backward compatibility for the deprecated data_model module."""

    def test_pinterest_media_from_data_model(self):
        """Test importing PinterestMedia from old data_model path."""
        with pytest.warns(DeprecationWarning, match=r"data_model.*1\.1\.0"):
            from pinterest_dl.data_model import PinterestMedia

            # Should work but trigger warning
            assert PinterestMedia is not None

            # Verify it's the same class as the new import
            from pinterest_dl.domain.media import PinterestMedia as NewPinterestMedia

            assert PinterestMedia is NewPinterestMedia

    def test_video_stream_info_from_data_model(self):
        """Test importing VideoStreamInfo from old data_model path."""
        with pytest.warns(DeprecationWarning, match=r"data_model.*1\.1\.0"):
            from pinterest_dl.data_model import VideoStreamInfo

            assert VideoStreamInfo is not None

            from pinterest_dl.domain.media import VideoStreamInfo as NewVideoStreamInfo

            assert VideoStreamInfo is NewVideoStreamInfo


class TestDeprecatedClassNames:
    """Test backward compatibility for renamed internal classes."""

    def test_deprecated_pinterest_api(self):
        """Test that PinterestAPI is still accessible with deprecation warning."""
        with pytest.warns(DeprecationWarning, match=r"PinterestAPI.*Api.*1\.1\.0"):
            from pinterest_dl.api import Api, PinterestAPI

            assert PinterestAPI is Api

    def test_deprecated_pinterest_driver(self):
        """Test that PinterestDriver is still accessible with deprecation warning."""
        with pytest.warns(DeprecationWarning, match=r"PinterestDriver.*Driver.*1\.1\.0"):
            from pinterest_dl.webdriver import Driver, PinterestDriver

            assert PinterestDriver is Driver

    def test_deprecated_pinterest_media_downloader(self):
        """Test that PinterestMediaDownloader is still accessible with deprecation warning."""
        with pytest.warns(
            DeprecationWarning, match=r"PinterestMediaDownloader.*MediaDownloader.*1\.1\.0"
        ):
            from pinterest_dl.download import MediaDownloader, PinterestMediaDownloader

            assert PinterestMediaDownloader is MediaDownloader

    def test_deprecated_pinterest_cookie_jar(self):
        """Test that PinterestCookieJar is still accessible with deprecation warning."""
        with pytest.warns(DeprecationWarning, match=r"PinterestCookieJar.*CookieJar.*1\.1\.0"):
            from pinterest_dl.domain import CookieJar, PinterestCookieJar

            assert PinterestCookieJar is CookieJar


class TestNewAPIsWorkWithoutWarnings:
    """Test that new API names work without triggering deprecation warnings."""

    def test_new_api_import(self):
        """Test that Api import doesn't trigger warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.api import Api

            assert Api is not None

    def test_new_driver_import(self):
        """Test that Driver import doesn't trigger warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.webdriver import Driver

            assert Driver is not None

    def test_new_media_downloader_import(self):
        """Test that MediaDownloader import doesn't trigger warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.download import MediaDownloader

            assert MediaDownloader is not None

    def test_new_cookie_jar_import(self):
        """Test that CookieJar import doesn't trigger warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.domain import CookieJar

            assert CookieJar is not None

    def test_new_domain_imports(self):
        """Test that new domain module imports work without warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            from pinterest_dl.domain import PinterestMedia, VideoStreamInfo

            assert PinterestMedia is not None
            assert VideoStreamInfo is not None


class TestDeprecationMessageQuality:
    """Test that all deprecation messages are clear and actionable."""

    def test_all_deprecations_mention_version(self):
        """Test that all deprecation warnings mention version 1.1.0."""
        deprecated_imports = [
            ("pinterest_dl.scrapers", "_ScraperAPI"),
            ("pinterest_dl.scrapers", "_ScraperWebdriver"),
            ("pinterest_dl.data_model", "PinterestMedia"),
            ("pinterest_dl.data_model", "VideoStreamInfo"),
            ("pinterest_dl.api", "PinterestAPI"),
            ("pinterest_dl.webdriver", "PinterestDriver"),
            ("pinterest_dl.download", "PinterestMediaDownloader"),
            ("pinterest_dl.domain", "PinterestCookieJar"),
        ]

        for module_name, class_name in deprecated_imports:
            with pytest.warns(DeprecationWarning) as record:
                __import__(module_name, fromlist=[class_name])
                getattr(__import__(module_name, fromlist=[class_name]), class_name)

            assert len(record) >= 1
            warning_message = str(record[0].message)
            assert "1.1.0" in warning_message, f"{class_name} warning should mention version 1.1.0"

    def test_deprecation_messages_provide_alternatives(self):
        """Test that deprecation warnings tell users what to use instead."""
        test_cases = [
            ("pinterest_dl.scrapers", "_ScraperAPI", "ApiScraper"),
            ("pinterest_dl.api", "PinterestAPI", "Api"),
            ("pinterest_dl.webdriver", "PinterestDriver", "Driver"),
            ("pinterest_dl.download", "PinterestMediaDownloader", "MediaDownloader"),
            ("pinterest_dl.domain", "PinterestCookieJar", "CookieJar"),
        ]

        for module_name, old_name, new_name in test_cases:
            with pytest.warns(DeprecationWarning) as record:
                __import__(module_name, fromlist=[old_name])
                getattr(__import__(module_name, fromlist=[old_name]), old_name)

            warning_message = str(record[0].message)
            assert new_name in warning_message, (
                f"{old_name} warning should mention the new name: {new_name}"
            )
