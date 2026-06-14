"""Tests for CLI utility functions."""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import pytest

from pinterest_dl.cli import combine_inputs, get_parser, main, parse_resolution, sanitize_url
from pinterest_dl.domain.media import PinterestMedia


class TestParseResolution:
    """Test resolution parsing function."""

    def test_parse_valid_resolution(self):
        """Test parsing valid resolution string."""
        assert parse_resolution("1920x1080") == (1920, 1080)
        assert parse_resolution("512x512") == (512, 512)
        assert parse_resolution("3840x2160") == (3840, 2160)

    def test_parse_resolution_with_spaces(self):
        """Test parsing resolution with extra spaces."""
        assert parse_resolution("1920 x 1080") == (1920, 1080)

    def test_parse_invalid_resolution_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_resolution("1920-1080")

        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_resolution("invalid")

        with pytest.raises(ValueError, match="Invalid resolution format"):
            parse_resolution("1920")


class TestSanitizeUrl:
    """Test URL sanitization function."""

    def test_add_trailing_slash(self):
        """Test that trailing slash is added when missing."""
        assert sanitize_url("https://pinterest.com/pin/123") == "https://pinterest.com/pin/123/"
        assert sanitize_url("https://pinterest.com") == "https://pinterest.com/"

    def test_keep_existing_slash(self):
        """Test that existing trailing slash is preserved."""
        assert sanitize_url("https://pinterest.com/pin/123/") == "https://pinterest.com/pin/123/"
        assert sanitize_url("https://pinterest.com/") == "https://pinterest.com/"

    def test_empty_string(self):
        """Test empty string gets trailing slash."""
        assert sanitize_url("") == "/"


class TestCombineInputs:
    """Test combining inputs from different sources."""

    def test_combine_positionals_only(self):
        """Test combining only positional arguments."""
        result = combine_inputs(["url1", "url2", "url3"], None)
        assert result == ["url1", "url2", "url3"]

    def test_combine_empty_lists(self):
        """Test combining empty lists."""
        result = combine_inputs([], None)
        assert result == []

    def test_combine_with_file(self, tmp_path):
        """Test combining with file input."""
        # Create a test file with URLs
        test_file = tmp_path / "urls.txt"
        test_file.write_text("https://pinterest.com/pin/1/\nhttps://pinterest.com/pin/2/\n")

        result = combine_inputs(["url3"], [str(test_file)])
        assert "https://pinterest.com/pin/1/" in result
        assert "https://pinterest.com/pin/2/" in result
        assert "url3" in result

    def test_combine_skip_empty_lines(self, tmp_path):
        """Test that empty lines in file are skipped."""
        test_file = tmp_path / "urls.txt"
        test_file.write_text("url1\n\nurl2\n  \nurl3")

        result = combine_inputs([], [str(test_file)])
        assert result == ["url1", "url2", "url3"]


class TestJsonMode:
    def test_parser_accepts_json_flag(self):
        parser = get_parser()

        assert parser.parse_args(["scrape", "--json", "url"]).json is True
        assert parser.parse_args(["search", "--json", "cats"]).json is True
        assert parser.parse_args(["download", "--json", "cache.json"]).json is True

    def test_scrape_json_mode_prints_structured_json(self):
        media = PinterestMedia(
            id=123,
            src="https://i.pinimg.com/test.jpg",
            alt="caption",
            origin="https://www.pinterest.com/pin/123/",
            resolution=(1200, 1800),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("sys.argv", ["pinterest-dl", "scrape", "--json", "https://www.pinterest.com/pin/123/"]),
            patch("pinterest_dl.cli.PinterestDL") as dl,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            dl.with_api.return_value.with_cookies_path.return_value.scrape.return_value = [media]
            main()

        payload = json.loads(stdout.getvalue())
        assert payload["command"] == "scrape"
        assert payload["results"][0]["input"] == "https://www.pinterest.com/pin/123/"
        assert payload["results"][0]["items"][0]["id"] == 123
        assert stderr.getvalue() == ""

    def test_search_json_mode_sends_errors_to_stderr(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("sys.argv", ["pinterest-dl", "search", "--json", "cats"]),
            patch("pinterest_dl.cli.PinterestDL") as dl,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            dl.with_api.return_value.with_cookies_path.return_value.search.side_effect = RuntimeError("boom")
            with pytest.raises(SystemExit) as exc:
                main()

        assert exc.value.code == 1
        assert stdout.getvalue() == ""
        assert "Error: boom" in stderr.getvalue()
