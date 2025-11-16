"""Tests for Pinterest API URL parsing."""
from pinterest_dl.low_level.api.pinterest_api import PinterestAPI


class TestPinterestAPIUrlParsing:
    """Test URL parsing methods in PinterestAPI."""

    def test_parse_pin_id_valid_url(self):
        """Test parsing pin ID from valid Pinterest URL."""
        api = PinterestAPI("https://www.pinterest.com/pin/123456789012345/")
        assert api.pin_id == "123456789012345"

    def test_parse_pin_id_without_trailing_slash(self):
        """Test parsing pin ID - URL needs trailing slash."""
        # Note: The API requires trailing slash, so this will be None
        api = PinterestAPI("https://www.pinterest.com/pin/987654321098765")
        # Without trailing slash, it won't parse
        assert api.pin_id is None

    def test_parse_board_url_valid(self):
        """Test parsing board URL."""
        api = PinterestAPI("https://www.pinterest.com/username/board-name/")
        assert api.username == "username"
        assert api.boardname == "board-name"

    def test_parse_board_url_without_trailing_slash(self):
        """Test parsing board URL without trailing slash."""
        api = PinterestAPI("https://www.pinterest.com/testuser/my-board")
        assert api.username == "testuser"
        assert api.boardname == "my-board"

    def test_parse_search_query_url(self):
        """Test parsing search query from URL."""
        api = PinterestAPI("https://www.pinterest.com/search/pins/?q=nature&rs=typed")
        assert api.query == "nature"

    def test_invalid_url_sets_none(self):
        """Test that invalid URLs set attributes to None."""
        api = PinterestAPI("https://www.pinterest.com/")
        assert api.pin_id is None
        assert api.query is None

    def test_is_pin_property(self):
        """Test is_pin attribute."""
        pin_api = PinterestAPI("https://www.pinterest.com/pin/123456789012345/")
        assert pin_api.is_pin is True

        board_api = PinterestAPI("https://www.pinterest.com/user/board/")
        assert board_api.is_pin is False

    def test_board_attributes_set(self):
        """Test board username and boardname are set correctly."""
        board_api = PinterestAPI("https://www.pinterest.com/user/myboard/")
        assert board_api.username == "user"
        assert board_api.boardname == "myboard"

    def test_search_query_attribute(self):
        """Test search query attribute is set."""
        search_api = PinterestAPI("https://www.pinterest.com/search/pins/?q=nature&rs=typed")
        assert search_api.query == "nature"
