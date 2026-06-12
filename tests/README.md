# Tests

The default suite is **offline** and makes no requests to Pinterest. This is
enforced by an autouse fixture in `conftest.py`; a test that reaches the network
fails loudly. Live API tests live in `tests/integration/` behind the
`integration` marker and are excluded by default.

See the [Testing Guide](../doc/TESTING.md) for the full policy, rationale, and
how to write tests that need the network.

## Running Tests

```bash
# Run the default (offline) suite
pytest

# Verbose
pytest -v

# A single file or test
pytest tests/test_pinterest_media.py
pytest tests/test_pinterest_api.py::TestPinterestAPIUrlParsing::test_parse_pin_id_valid_url

# Live integration tests (hit the real Pinterest API; run deliberately)
pytest -m integration
```
