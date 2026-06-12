# Testing

## Policy: the default suite never touches the network

Pinterest's API is unofficial and reverse engineered. Running the test suite
must not send requests to Pinterest. Hitting their servers on every test run is
wasteful, risks rate limiting, and is not a polite thing to do to a service we
do not own. Unit tests verify *our* code, so they have no reason to go online.

The default suite is therefore fully offline and runs with no internet
connection. This is enforced automatically, not by convention.

## Running tests

```bash
# Run the default (offline) suite
pytest

# Verbose
pytest -v

# A single file or test
pytest tests/test_pinterest_api.py
pytest tests/test_pinterest_api.py::TestPinterestAPIUrlParsing::test_parse_pin_id_valid_url
```

Install the test tools first if needed:

```bash
pip install -e ".[dev]"
```

## How offline is enforced

`tests/conftest.py` has an autouse fixture, `_offline_guard`, that applies to
every test:

1. It stubs `Api._get_default_cookies` so constructing `Api(...)` no longer
   fetches default cookies from `https://www.pinterest.com`. Without this, every
   `Api(...)` in a test fires a real request as a side effect of `__init__`.
2. It blocks real outbound socket connections. Loopback (`127.*`, `::1`,
   `localhost`) is still allowed so local machinery such as the asyncio event
   loop and Playwright keeps working. Any other connection attempt raises:

   ```
   RuntimeError: Network access is not allowed in unit tests.
   Mark the test with @pytest.mark.integration to hit the real API.
   ```

This means a new test that accidentally reaches the network fails loudly instead
of silently hammering Pinterest.

## Integration tests (the API canary)

Unit tests cannot detect Pinterest changing its API, because they assert against
our own parsing of fixed inputs. To catch API drift we keep a small set of
deliberate live tests in `tests/integration/`, marked with
`@pytest.mark.integration`. These are excluded from the default run (see
`addopts` in `pyproject.toml`) and are exempt from the offline guard.

Run them only when you mean to:

```bash
pytest -m integration
```

Keep this suite small. A couple of real assertions are enough to detect drift;
more requests just add load on Pinterest without adding signal.

### Scheduled runs

`.github/workflows/integration.yml` runs the integration suite on a monthly cron
and on manual dispatch, never on push. One controlled run a month is a negligible
load on Pinterest, and it alerts us when the unofficial API changes.

## Writing a test that needs the network

Default to offline. Mock the boundary (the HTTP client, `requests`, `m3u8.load`,
`subprocess.run`) and test your logic against the mocked response. Most of the
suite already does this.

Only when the point of the test is to verify Pinterest's real behavior should it
go online. In that case put it under `tests/integration/` and mark it:

```python
import pytest

pytestmark = pytest.mark.integration

def test_something_live():
    ...
```

## See Also

- [Dump Mode](DUMP.md) - capture real API requests/responses for debugging and analysis
- [API Documentation](API.md)
