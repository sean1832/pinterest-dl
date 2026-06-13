"""Tests for Pinterest API URL parsing."""

from types import SimpleNamespace
from unittest.mock import patch

from pinterest_dl.api.api import Api
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.exceptions import (
    EmptyResponseError,
    InvalidBoardUrlError,
    InvalidPinterestUrlError,
    InvalidSearchUrlError,
)
from pinterest_dl.scrapers.api_scraper import ApiScraper


class TestPinterestAPIUrlParsing:
    """Test URL parsing methods in Api."""

    def test_parse_pin_id_valid_url(self):
        """Test parsing pin ID from valid Pinterest URL."""
        api = Api("https://www.pinterest.com/pin/123456789012345/")
        assert api.pin_id == "123456789012345"

    def test_parse_pin_id_without_trailing_slash(self):
        """Test parsing pin ID when URL omits trailing slash."""
        api = Api("https://www.pinterest.com/pin/987654321098765")
        assert api.pin_id == "987654321098765"

    def test_parse_pin_id_without_scheme(self):
        """Test parsing pin ID when URL omits scheme."""
        api = Api("ru.pinterest.com/pin/47358233572860931/")
        assert api.url == "https://ru.pinterest.com/pin/47358233572860931/"
        assert api.pin_id == "47358233572860931"

    def test_parse_board_url_valid(self):
        """Test parsing board URL."""
        api = Api("https://www.pinterest.com/username/board-name/")
        assert api.username == "username"
        assert api.boardname == "board-name"

    def test_parse_board_url_without_trailing_slash(self):
        """Test parsing board URL without trailing slash."""
        api = Api("https://www.pinterest.com/testuser/my-board")
        assert api.username == "testuser"
        assert api.boardname == "my-board"

    def test_parse_board_url_with_query_parameters(self):
        """Test parsing board URL when short-link redirect preserves query params."""
        api = Api(
            "https://ru.pinterest.com/DRAMrefresh/what-the-dog-doin/"
            "?invite_code=106b1079a76c49e7b995245a1ec4697c&sender=923308498513593481"
        )
        assert api.username == "DRAMrefresh"
        assert api.boardname == "what-the-dog-doin"

    # Synthetic non-Latin board slug (katakana for "test"); percent-encoded in
    # URLs as "%E3%83%86%E3%82%B9%E3%83%88-2". Regression cover for issue #72.
    UNICODE_BOARD_SLUG = "テスト-2"

    def test_parse_board_url_with_percent_encoded_unicode(self):
        """Percent-encoded Unicode board slugs should decode (issue #72)."""
        api = Api("https://www.pinterest.com/testuser/%E3%83%86%E3%82%B9%E3%83%88-2/")
        assert api.username == "testuser"
        assert api.boardname == self.UNICODE_BOARD_SLUG

    def test_parse_board_url_with_raw_unicode(self):
        """Non-encoded Unicode board slugs should also parse."""
        api = Api(f"https://www.pinterest.com/testuser/{self.UNICODE_BOARD_SLUG}/")
        assert api.username == "testuser"
        assert api.boardname == self.UNICODE_BOARD_SLUG

    def test_parse_search_query_url(self):
        """Test parsing search query from URL."""
        api = Api("https://www.pinterest.com/search/pins/?q=nature&rs=typed")
        assert api.query == "nature"

    def test_invalid_url_sets_none(self):
        """Test that invalid URLs set attributes to None."""
        api = Api("https://www.pinterest.com/")
        assert api.pin_id is None
        assert api.query is None

    def test_is_pin_property(self):
        """Test is_pin attribute."""
        pin_api = Api("https://www.pinterest.com/pin/123456789012345/")
        assert pin_api.is_pin is True

        board_api = Api("https://www.pinterest.com/user/board/")
        assert board_api.is_pin is False

    def test_board_attributes_set(self):
        """Test board username and boardname are set correctly."""
        board_api = Api("https://www.pinterest.com/user/myboard/")
        assert board_api.username == "user"
        assert board_api.boardname == "myboard"

    def test_search_query_attribute(self):
        """Test search query attribute is set."""
        search_api = Api("https://www.pinterest.com/search/pins/?q=nature&rs=typed")
        assert search_api.query == "nature"

    def test_parse_section_url_valid(self):
        """Test parsing section URL with 3 path segments."""
        api = Api("https://id.pinterest.com/Murasaki_Akiyama/wallpaper/live-wallpaper/")
        assert api.username == "Murasaki_Akiyama"
        assert api.boardname == "wallpaper"
        assert api.section_slug == "live-wallpaper"
        assert api.is_section is True

    def test_parse_section_url_without_trailing_slash(self):
        """Test parsing section URL without trailing slash."""
        api = Api("https://www.pinterest.com/testuser/my-board/my-section")
        assert api.username == "testuser"
        assert api.boardname == "my-board"
        assert api.section_slug == "my-section"
        assert api.is_section is True

    def test_parse_section_url_with_query_parameters(self):
        """Test parsing section URL when query params are present."""
        api = Api(
            "https://www.pinterest.com/testuser/my-board/my-section/"
            "?invite_code=abc123&sender=123"
        )
        assert api.username == "testuser"
        assert api.boardname == "my-board"
        assert api.section_slug == "my-section"
        assert api.is_section is True

    def test_parse_section_url_with_percent_encoded_unicode(self):
        """Percent-encoded Unicode board/section slugs should decode (issue #72)."""
        api = Api("https://www.pinterest.com/testuser/%E3%83%86%E3%82%B9%E3%83%88-2/live/")
        assert api.username == "testuser"
        assert api.boardname == self.UNICODE_BOARD_SLUG
        assert api.section_slug == "live"
        assert api.is_section is True

    def test_board_url_is_not_section(self):
        """Test that regular board URL is not detected as section."""
        api = Api("https://www.pinterest.com/username/boardname/")
        assert api.is_section is False
        assert api.section_slug is None

    def test_section_url_with_different_subdomains(self):
        """Test section URL with various Pinterest subdomains."""
        # Japanese subdomain
        api = Api("https://jp.pinterest.com/user/board/section/")
        assert api.is_section is True
        assert api.section_slug == "section"

        # German subdomain
        api2 = Api("https://de.pinterest.com/user/board/section/")
        assert api2.is_section is True
        assert api2.section_slug == "section"


class TestScrapePinFallbacks:
    def test_scrape_falls_back_to_page_when_api_data_is_invalid(self):
        scraper = ApiScraper()
        expected = PinterestMedia(
            id=123456789012345,
            src="https://i.pinimg.com/originals/test.jpg",
            alt="caption",
            origin="https://www.pinterest.com/pin/123456789012345/",
            resolution=(1200, 1800),
        )

        with (
            patch.object(Api, "get_main_image", side_effect=ValueError("bad json")),
            patch.object(ApiScraper, "_get_main_pin_from_page", return_value=expected) as page_fallback,
        ):
            items = scraper.scrape("https://www.pinterest.com/pin/123456789012345/", num=1)

        assert items == [expected]
        page_fallback.assert_called_once()

    def test_scrape_rejects_unknown_resolution_when_min_resolution_is_requested(self):
        html = """
        <html>
            <meta property="og:image" content="https://i.pinimg.com/originals/test.jpg">
            <meta property="og:description" content="caption">
        </html>
        """

        scraper = ApiScraper()

        with (
            patch.object(Api, "get_main_image", side_effect=EmptyResponseError("no data")),
            patch.object(Api, "get_pin_page", return_value=html),
            patch.object(ApiScraper, "_pump") as pump,
        ):
            items = scraper.scrape(
                "https://www.pinterest.com/pin/123456789012345/",
                num=1,
                min_resolution=(1000, 1000),
            )

        assert items == []
        pump.assert_not_called()


class TestApiScraperRouting:
    def test_scrape_returns_only_the_pin_when_num_is_one(self):
        fake_api = SimpleNamespace(query=None, is_pin=True, is_section=False)
        expected = PinterestMedia(
            id=123,
            src="https://i.pinimg.com/originals/test.jpg",
            alt="caption",
            origin="https://www.pinterest.com/pin/123/",
            resolution=(1200, 1800),
        )

        with (
            patch("pinterest_dl.scrapers.api_scraper.Api", return_value=fake_api),
            patch.object(ApiScraper, "_scrape_one_pin", return_value=expected) as scrape_one_pin,
            patch.object(ApiScraper, "_pump") as pump,
        ):
            scraper = ApiScraper()
            items = scraper.scrape("https://www.pinterest.com/pin/123/", num=1)

        assert items == [expected]
        scrape_one_pin.assert_called_once_with(fake_api, (0, 0), False)
        # num=1 is satisfied by the pin alone, so the related stream is never tapped.
        pump.assert_not_called()

    def test_scrape_fills_with_related_when_num_exceeds_one(self):
        fake_api = SimpleNamespace(query=None, is_pin=True, is_section=False)
        pin = PinterestMedia(
            id=123,
            src="https://i.pinimg.com/originals/pin.jpg",
            alt="caption",
            origin="https://www.pinterest.com/pin/123/",
            resolution=(1200, 1800),
        )
        related = [
            PinterestMedia(
                id=456,
                src="https://i.pinimg.com/originals/related-1.jpg",
                alt="related 1",
                origin="https://www.pinterest.com/pin/456/",
                resolution=(1200, 1800),
            ),
            PinterestMedia(
                id=789,
                src="https://i.pinimg.com/originals/related-2.jpg",
                alt="related 2",
                origin="https://www.pinterest.com/pin/789/",
                resolution=(1200, 1800),
            ),
            PinterestMedia(
                id=101,
                src="https://i.pinimg.com/originals/related-3.jpg",
                alt="related 3",
                origin="https://www.pinterest.com/pin/101/",
                resolution=(1200, 1800),
            ),
        ]

        with (
            patch("pinterest_dl.scrapers.api_scraper.Api", return_value=fake_api),
            patch.object(ApiScraper, "_scrape_one_pin", return_value=pin),
            patch.object(ApiScraper, "_pump", return_value=iter(related)) as pump,
        ):
            scraper = ApiScraper()
            items = scraper.scrape("https://www.pinterest.com/pin/123/", num=3)

        # The pin counts as one item, so islice caps the related stream at num - 1 = 2.
        assert items == [pin, related[0], related[1]]
        pump.assert_called_once()

    def test_scrape_uses_board_flow_for_board_urls(self):
        fake_api = SimpleNamespace(query=None, is_pin=False, is_section=False)
        expected = [
            PinterestMedia(
                id=1,
                src="https://i.pinimg.com/originals/test.jpg",
                alt="caption",
                origin="https://www.pinterest.com/pin/1/",
                resolution=(1200, 1800),
            )
        ]

        with (
            patch("pinterest_dl.scrapers.api_scraper.Api", return_value=fake_api),
            patch.object(ApiScraper, "_iter_board", return_value=iter(expected)) as iter_board,
        ):
            scraper = ApiScraper()
            items = scraper.scrape("https://www.pinterest.com/user/board/", num=50)

        assert items == expected
        iter_board.assert_called_once()

    def test_related_requires_pin_urls(self):
        fake_api = SimpleNamespace(is_pin=False, is_section=False)

        with patch("pinterest_dl.scrapers.api_scraper.Api", return_value=fake_api):
            scraper = ApiScraper()

            try:
                scraper.related("https://www.pinterest.com/user/board/", num=10)
            except ValueError as e:
                assert str(e) == "related only supports Pinterest pin URLs"
            else:
                raise AssertionError("Expected ValueError for non-pin related scrape")
