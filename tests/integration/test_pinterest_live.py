"""Live checks against the real Pinterest API.

These are the canary tests: they hit Pinterest for real so we get alerted when
the unofficial API changes shape. They are excluded from the default suite and
run deliberately (locally or on a schedule):

    pytest -m integration

Keep this file small. A couple of real assertions are enough to detect drift;
more requests just add load on Pinterest without adding signal.
"""

import pytest

from pinterest_dl import PinterestDL
from pinterest_dl.api.api import Api

pytestmark = pytest.mark.integration


def test_default_cookies_endpoint_serves_cookies():
    """The base URL still hands out cookies (Api.__init__ depends on this)."""
    cookies = Api._get_default_cookies("https://www.pinterest.com")
    assert isinstance(cookies, dict)
    assert cookies, "Pinterest returned no default cookies; the endpoint may have changed"


def test_search_scrape_returns_usable_images():
    """End-to-end: search resource + response parsing still yield image URLs."""
    results = PinterestDL.with_api().scrape("https://www.pinterest.com/search/pins/?q=nature", num=5)

    assert results, "Search returned no media; the API response shape may have changed"
    for media in results:
        assert media.src.startswith("https://"), f"Unexpected image src: {media.src!r}"
