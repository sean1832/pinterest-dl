# Tests

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_pinterest_media.py

# Run specific test
pytest tests/test_pinterest_api.py::TestPinterestAPIUrlParsing::test_parse_pin_id_valid_url
```