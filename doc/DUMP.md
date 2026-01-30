# Dump Mode Documentation

## Overview

Pinterest-DL includes a comprehensive dump mode that automatically dumps all API requests and responses to JSON files. This is invaluable for:

- Troubleshooting API failures
- Understanding Pinterest's API structure
- Debugging authentication issues
- Analyzing rate limiting or blocking
- Contributing to the project

## Quick Start

### CLI Usage

Add the `--dump` flag to any scrape or search command:

```bash
# Enable dump mode (dumps to .dump directory by default)
pinterest-dl scrape <URL> --dump

# Specify custom dump directory
pinterest-dl scrape <URL> --dump custom_logs

# Example with search
pinterest-dl search "cats" -n 50 --dump
```

### Python API Usage

```python
from pinterest_dl import PinterestDL

# Create scraper with dump mode enabled (uses .dump directory)
scraper = PinterestDL.with_api(
    dump=".dump"  # Specify dump directory, or None to disable
)

# All API calls will now be logged
medias = scraper.scrape("https://pinterest.com/pin/123456/", num=10)
```

## Dump File Structure

When dump mode is enabled, JSON files are created in the dump directory with the following naming patterns:

### Successful Requests

Format: `{operation}_{identifier}.json`

Examples:
- `get_related_images_pin_123456.json`
- `get_main_image_pin_789012.json`
- `get_board_username_boardname.json`
- `get_board_feed_board123.json`
- `get_search_cats.json`

### Failed Requests

Format: `error_{operation}_{identifier}.json`

Examples:
- `error_get_related_images_pin_123456.json`
- `error_get_search_dogs.json`

## Dump File Contents

Each dump file contains comprehensive request and response information:

```json
{
  "timestamp": "2026-01-30T10:30:45.123456",
  "request": {
    "url": "https://www.pinterest.com/resource/...",
    "method": "GET",
    "headers": {
      "User-Agent": "Mozilla/5.0...",
      "x-pinterest-pws-handler": "www/pin/[id].js"
    },
    "body": null
  },
  "response": {
    "status_code": 200,
    "reason": "OK",
    "headers": {
      "content-type": "application/json",
      "x-ratelimit-remaining": "95"
    },
    "url": "https://www.pinterest.com/resource/...",
    "elapsed_ms": 234.567,
    "json": {
      "resource_response": {
        "data": [...]
      }
    }
  },
  "metadata": {
    "api_endpoint": "/resource/RelatedPinFeedResource/get/",
    "api_options": {
      "pin_id": "123456",
      "page_size": 10,
      "bookmarks": []
    }
  }
}
```

### Error Files

Error files include additional error information:

```json
{
  "timestamp": "2026-01-30T10:35:12.789012",
  "error": {
    "type": "HTTPError",
    "message": "403 Client Error: Forbidden"
  },
  "request": {
    "url": "https://www.pinterest.com/..."
  },
  "response": {
    "status_code": 403,
    "reason": "Forbidden",
    "json": {
      "message": "Invalid authentication credentials"
    }
  }
}
```

## Use Cases

### 1. Debugging Authentication Issues

When scraping private boards fails:

```bash
pinterest-dl scrape <PRIVATE_BOARD_URL> -c cookies.json --dump
```

Check the dump files to see if:
- Cookies are being sent correctly (`request.headers`)
- Authentication errors are returned (`response.json.message`)
- Rate limiting is triggered (`response.headers.x-ratelimit-remaining`)

### 2. Analyzing API Changes

Pinterest's unofficial API can change without notice. Dump files help you:

```python
# Scrape with dump enabled
scraper = PinterestDL.with_api(dump=".dump")
medias = scraper.scrape(url, num=5)

# Check .dump/ directory for response structure changes
```

### 3. Reporting Issues

When reporting bugs, include dump files:

```bash
# Generate dump files
pinterest-dl scrape <URL> --dump

# Check .dump/ directory and attach relevant files to your GitHub issue
```

### 4. Development and Testing

During development, use dump mode to verify API interactions:

```python
from pinterest_dl.common.dump import RequestDumper

dumper = RequestDumper("my_tests")
# Manual usage in custom code
dump_path = dumper.dump_request_response(
    request_url="https://api.example.com",
    response=response_obj,
    filename="custom_test"
)
```

## Advanced Usage

### Programmatic Access

The dump utility can be used standalone:

```python
from pinterest_dl.common.dump import RequestDumper
import requests

dumper = RequestDumper(".dump")

# Make a request
response = requests.get("https://api.example.com/data")

# Dump it
dump_file = dumper.dump_request_response(
    request_url=response.url,
    response=response,
    filename="my_api_call",
    metadata={"test_case": "rate_limit_test"}
)

print(f"Dump saved to: {dump_file}")
```

### Dump API Calls with Custom Metadata

```python
from pinterest_dl.api.api import Api

api = Api(
    url="https://pinterest.com/pin/123456/",
    dump=".dump"
)

# All API calls automatically logged with endpoint and options
response = api.get_related_images(num=10, bookmark=[])
```

### Error-Only Logging

For production use, you can enable dump mode only on errors:

```python
from pinterest_dl.common.dump import RequestDumper

dumper = RequestDumper("error_logs")

try:
    # Your API calls
    pass
except Exception as e:
    # Dump only failures
    dumper.dump_error(
        error=e,
        request_url=url,
        response=response if 'response' in locals() else None
    )
```

## Privacy and Security

**Warning:** Dump files contain:
- Full request URLs (including query parameters)
- All request and response headers
- Complete response bodies
- Cookie values (if dumping is enabled at API level)

**Best Practices:**
1. Never commit dump files to version control
2. Sanitize dump files before sharing publicly
3. Delete dump files after troubleshooting
4. Add `.dump/` to your `.gitignore`

## Performance Considerations

Dump mode has minimal performance impact:
- JSON dumping is synchronous but fast
- Files are written only after response is received
- Typical overhead: < 10ms per request

For production scraping of thousands of items, consider disabling dump mode.

## Troubleshooting

### Dump files not created

1. Check directory permissions
2. Ensure dump parameter is set (e.g., `dump=".dump"`)
3. Verify the dump directory path is writable

### Files are empty or truncated

This shouldn't happen, but if it does:
- Check disk space
- Verify JSON encoding issues (non-ASCII characters)
- Check file system limits (FAT32 has 4GB limit)

### Too many dump files

Dump files accumulate in the `.dump/` directory. Clean them up periodically:

```bash
# Remove all dump files
rm -rf .dump/*

# Or organize by date
mkdir .dump/archive_2026_01_30
mv .dump/*.json .dump/archive_2026_01_30/
```

## Contributing

When contributing dump-related improvements:

1. Follow the existing pattern in `common/dump.py`
2. Add tests for new dump scenarios
3. Update this documentation
4. Ensure backward compatibility

## See Also

- [API Documentation](../doc/API.md)
- [CLI Documentation](../doc/CLI.md)
- [Exception Handling](../pinterest_dl/exceptions.py)
