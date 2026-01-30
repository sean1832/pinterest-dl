# Debug Mode Documentation

## Overview

Pinterest-DL includes a comprehensive debug mode that automatically dumps all API requests and responses to JSON files. This is invaluable for:

- Troubleshooting API failures
- Understanding Pinterest's API structure
- Debugging authentication issues
- Analyzing rate limiting or blocking
- Contributing to the project

## Quick Start

### CLI Usage

Add the `--debug` flag to any scrape or search command:

```bash
# Enable debug mode with default debug directory
pinterest-dl scrape <URL> --debug

# Specify custom debug directory
pinterest-dl scrape <URL> --debug --debug-dir my_debug_logs

# Example with search
pinterest-dl search "cats" -n 50 --debug
```

### Python API Usage

```python
from pinterest_dl import PinterestDL

# Create scraper with debug mode enabled
scraper = PinterestDL.with_api(
    debug_mode=True,
    debug_dir="debug"  # Optional, defaults to "debug"
)

# All API calls will now be logged
medias = scraper.scrape("https://pinterest.com/pin/123456/", num=10)
```

## Debug File Structure

When debug mode is enabled, JSON files are created in the debug directory with the following naming patterns:

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

## Debug File Contents

Each debug file contains comprehensive request and response information:

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
pinterest-dl scrape <PRIVATE_BOARD_URL> -c cookies.json --debug
```

Check the debug files to see if:
- Cookies are being sent correctly (`request.headers`)
- Authentication errors are returned (`response.json.message`)
- Rate limiting is triggered (`response.headers.x-ratelimit-remaining`)

### 2. Analyzing API Changes

Pinterest's unofficial API can change without notice. Debug files help you:

```python
# Scrape with debug enabled
scraper = PinterestDL.with_api(debug_mode=True)
medias = scraper.scrape(url, num=5)

# Check debug/ directory for response structure changes
```

### 3. Reporting Issues

When reporting bugs, include debug files:

```bash
# Generate debug files
pinterest-dl scrape <URL> --debug --debug-dir issue_123_logs

# Attach files from issue_123_logs/ to your GitHub issue
```

### 4. Development and Testing

During development, use debug mode to verify API interactions:

```python
from pinterest_dl.common.debug import RequestDebugger

debugger = RequestDebugger("my_tests")
# Manual usage in custom code
dump_path = debugger.dump_request_response(
    request_url="https://api.example.com",
    response=response_obj,
    filename="custom_test"
)
```

## Advanced Usage

### Programmatic Access

The debug utility can be used standalone:

```python
from pinterest_dl.common.debug import RequestDebugger
import requests

debugger = RequestDebugger("debug_output")

# Make a request
response = requests.get("https://api.example.com/data")

# Dump it
debug_file = debugger.dump_request_response(
    request_url=response.url,
    response=response,
    filename="my_api_call",
    metadata={"test_case": "rate_limit_test"}
)

print(f"Debug saved to: {debug_file}")
```

### Dump API Calls with Custom Metadata

```python
from pinterest_dl.api.api import Api

api = Api(
    url="https://pinterest.com/pin/123456/",
    debug_mode=True,
    debug_dir="custom_debug"
)

# All API calls automatically logged with endpoint and options
response = api.get_related_images(num=10, bookmark=[])
```

### Error-Only Logging

For production use, you can enable debug mode only on errors:

```python
from pinterest_dl.common.debug import RequestDebugger

debugger = RequestDebugger("error_logs")

try:
    # Your API calls
    pass
except Exception as e:
    # Dump only failures
    debugger.dump_error(
        error=e,
        request_url=url,
        response=response if 'response' in locals() else None
    )
```

## Privacy and Security

**Warning:** Debug files contain:
- Full request URLs (including query parameters)
- All request and response headers
- Complete response bodies
- Cookie values (if debug mode is enabled at a low level)

**Best Practices:**
1. Never commit debug files to version control
2. Sanitize debug files before sharing publicly
3. Delete debug files after troubleshooting
4. Add `debug/` to your `.gitignore`

## Performance Considerations

Debug mode has minimal performance impact:
- JSON dumping is asynchronous (non-blocking)
- Files are written only after response is received
- Typical overhead: < 10ms per request

For production scraping of thousands of items, consider disabling debug mode.

## Troubleshooting

### Debug files not created

1. Check directory permissions
2. Ensure debug_mode=True is set
3. Verify the debug directory path is writable

### Files are empty or truncated

This shouldn't happen, but if it does:
- Check disk space
- Verify JSON encoding issues (non-ASCII characters)
- Check file system limits (FAT32 has 4GB limit)

### Too many debug files

Use custom debug directories per operation:

```python
# Different directory per scraping session
scraper = PinterestDL.with_api(
    debug_mode=True,
    debug_dir=f"debug/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
```

## Contributing

When contributing debug-related improvements:

1. Follow the existing pattern in `common/debug.py`
2. Add tests for new debug scenarios
3. Update this documentation
4. Ensure backward compatibility

## See Also

- [API Documentation](../doc/API.md)
- [CLI Documentation](../doc/CLI.md)
- [Exception Handling](../pinterest_dl/exceptions.py)
