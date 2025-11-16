# Pinterest-DL AI Coding Instructions

## Project Overview
Pinterest-DL is a Python-based Pinterest media scraper/downloader supporting both reverse-engineered API and Selenium WebDriver approaches. Core purpose: scrape images/videos from Pinterest boards/pins (including private content with cookies) and download them asynchronously.

**Key Architecture Pattern**: Dual scraping strategy with unified interface via `PinterestDL` factory class:
- **API mode** (`_ScraperAPI`): Fast, reverse-engineered Pinterest API (default)
- **WebDriver mode** (`_ScraperWebdriver`): Selenium-based, slower but more reliable

## Critical Architecture Components

### 1. Entry Points & Factory Pattern
- `pinterest_dl/__init__.py`: Main factory class `PinterestDL` with static methods:
  - `PinterestDL.with_api()` → `_ScraperAPI` instance
  - `PinterestDL.with_browser()` → `_ScraperWebdriver` instance
- Both scrapers inherit from `_ScraperBase` (shared download/caption logic)
- CLI entry point: `pinterest_dl/cli.py` (also aliased as `pin-dl`)

### 2. Data Flow Architecture
```
User Input (URL/Query)
  ↓
Scraper (API or WebDriver) → PinterestMedia objects
  ↓
Downloader (async, concurrent) → Local files
  ↓
Optional: Caption embedding (metadata/txt/json)
```

### 3. Core Data Model
`pinterest_dl/data_model/pinterest_media.py`:
- `PinterestMedia`: Central data class holding image/video metadata
- `VideoStreamInfo`: HLS stream metadata (resolution, duration, URL)
- **Critical**: Media can have both static image (`src`) and video stream (`video_stream`)

### 4. Low-Level Subsystems
**API Layer** (`low_level/api/`):
- `pinterest_api.py`: Pinterest API client with URL parsing, cookie handling
- `bookmark_manager.py`: Manages pagination bookmarks (keeps last N bookmarks)
- `endpoints.py`: API endpoint definitions
- `pinterest_response.py`: Response parsing and validation

**HTTP Layer** (`low_level/http/`):
- `http_client.py`: Requests session with retry logic, HLS processor integration
- `downloader.py`: `PinterestMediaDownloader` - concurrent download coordinator
  - Uses `ThreadPoolExecutor` for parallel downloads
  - Callback-based progress reporting via `TqdmProgressBarCallback`
- `request_builder.py`: Constructs Pinterest API request URLs

**HLS Video Processing** (`low_level/hls/`):
- `hls_processor.py`: Downloads encrypted HLS video streams
  - Fetches m3u8 playlists, resolves variants, decrypts AES-128 segments
  - Requires **ffmpeg** in PATH (checked via `ensure_executable.py`)
- `key_cache.py`: Caches decryption keys to avoid redundant requests
- `segment_info.py`: Segment metadata (URL, encryption method, IV)

**WebDriver Layer** (`low_level/webdriver/`):
- `pinterest_driver.py`: Selenium-based scraping logic
- `browser.py`: Browser initialization (Chrome/Firefox)
- `driver_installer.py`: Auto-downloads ChromeDriver/GeckoDriver

### 5. Cookie Authentication Pattern
Both scrapers support **Selenium cookie format** (list of dicts):
- Load via `.with_cookies(cookies)` or `.with_cookies_path("cookies.json")`
- Required for private boards/pins
- Generate via `pinterest-dl login` command (uses WebDriver)

## Development Conventions

### Import Organization
Follow existing pattern:
```python
# Standard library
import json
from pathlib import Path
from typing import List, Optional

# Third-party
import requests
from tqdm import tqdm

# Local
from pinterest_dl.data_model import PinterestMedia
from pinterest_dl.exceptions import DownloadError
```

### Exception Hierarchy
All custom exceptions in `exceptions.py`:
- `PinterestAPIError` (base)
  - `HttpResponseError` (has `.dump()` method for debugging)
  - `UrlParseError` → `InvalidPinterestUrlError`, `InvalidBoardUrlError`, `InvalidSearchUrlError`
  - `PinResponseError` → `BoardIDException`, `PinCountException`, `BookmarkException`
  - `EmptyResponseError`
- Other: `InvalidBrowser`, `ExecutableNotFoundError`, `UnsupportedMediaTypeError`, `DownloadError`, `HlsDownloadError`

### Progress Reporting Pattern
Use `tqdm` with `disable=verbose` pattern:
```python
for item in tqdm.tqdm(items, desc="Processing", disable=verbose):
    # verbose=True shows detailed logs instead of progress bar
```

### Path Handling
- Always use `pathlib.Path`, convert strings immediately
- Create dirs: `output_dir.mkdir(parents=True, exist_ok=True)`
- Check existence: `Path(file).exists()`

### Async Download Strategy
Not true asyncio, but `ThreadPoolExecutor` concurrent downloads:
- See `_ConcurrentCoordinator` in `downloader.py`
- Progress callbacks via `report(done, total)`
- Error accumulation with optional `fail_fast` mode

## Error Handling Architecture

### Layered Error Handling
Pinterest-DL follows a **separation of concerns** approach for error handling:

**Low-Level Modules** (API, HTTP, HLS, WebDriver utils):
- **NO logging** - only raise exceptions with clear, informative messages
- Exceptions bubble up to higher levels
- Include context in error messages (URLs, paths, error codes, retry counts)

**High-Level Modules** (Scrapers, CLI):
- **Handle and log** errors from lower levels
- Control user communication (print messages, progress bars)
- Decide error recovery strategy (continue/abort)
- Use `logging` module for structured logging

**Example Flow**:
```python
# Low-level (downloader.py) - raises exception
raise DownloadError(f"Failed to download {len(errors)} out of {total} items:\n{summary}")

# Scraper (scraper_base.py) - catches, logs, re-raises
try:
    local_paths = dl.download_concurrent(...)
except Exception as e:
    logger.error(f"Download failed: {e}")
    raise

# CLI (cli.py) - final handler, user-friendly message
except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)
    print(f"\nError: {e}")
    print("\nRun with --verbose for full traceback.")
    sys.exit(1)
```

### Logging Configuration
- Scrapers and CLI use `logging.getLogger(__name__)`
- CLI configures logging at `WARNING` level by default
- Verbose mode (`--verbose`) enables full tracebacks
- Low-level code has **no logging imports**

## Testing & Debugging

### Test Suite
**35 unit tests** covering critical paths (pytest framework):
- ✅ `tests/test_pinterest_media.py` - Data models and serialization
- ✅ `tests/test_pinterest_api.py` - URL parsing and validation
- ✅ `tests/test_cli_utils.py` - CLI utility functions
- ✅ `tests/test_exceptions.py` - Exception handling and error messages

Run tests:
```powershell
# All tests
pytest tests/

# Verbose output
pytest tests/ -v

# Specific file
pytest tests/test_pinterest_media.py
```

### Manual Testing
- Manual testing via `test.py` (example: scrape private board with cookies)
- Debug files: `debug_response.json`, `board_structure.json`

### Running Tests Manually
```powershell
# Activate venv
& .\venv\Scripts\Activate.ps1

# Run test suite
pytest tests/ -v

# Test API scraping manually
python test.py

# Test CLI
pinterest-dl scrape "https://pinterest.com/pin/123/" "output" -n 10 --verbose
```

### Debugging API Issues
- Enable `--verbose` for detailed logging
- Check `HttpResponseError.dump()` output for raw API responses
- Use `debug_response.json` to inspect Pinterest API payloads

## Build & Installation

### Package Structure
- `pyproject.toml`: Modern setuptools config, version from `__version__` in `__init__.py`
- Entry points: `pinterest-dl` and `pin-dl` aliases
- Dependencies: selenium, pillow, tqdm, pyexiv2, requests, m3u8, cryptography

### Install for Development
```powershell
pip install -e ".[dev]"  # Includes pytest and pytest-mock
```

### Version Bumping
Update `pinterest_dl/__init__.py`:
```python
__version__ = "0.8.3"  # Increment here
```

## Key Workflows

### Adding New Caption Formats
1. Update `cli.py` choices: `["txt", "json", "metadata", "none", "YOUR_FORMAT"]`
2. Implement in `_ScraperBase.add_captions_to_file()` or new method
3. Update README examples

### Supporting New Media Types
1. Add URL parsing to `PinterestAPI._parse_*` methods
2. Create endpoint in `endpoints.py`
3. Implement scraping logic in `_ScraperAPI.scrape()` or `_ScraperWebdriver.scrape()`
4. Handle in `PinterestMediaDownloader.download()`

### Extending HLS Processing
- Modify `hls_processor.py` for new encryption methods
- Update `decrypt()` method for additional cipher modes
- Test with `--video` flag in CLI

## Common Pitfalls

1. **Forgetting ffmpeg check**: Always check `ensure_executable.ensure_executable("ffmpeg")` before HLS downloads
2. **Cookie format confusion**: Selenium format (list of dicts) ≠ browser export format
3. **Resolution tuple order**: Always `(width, height)` not `(height, width)`
4. **URL sanitization**: CLI adds trailing slash via `sanitize_url()`, API parser expects it
5. **Bookmark manager**: Requires `last` param 0-4, manages pagination state
6. **Context manager pattern**: WebDriver scrapers need `.quit()` in finally block (see CLI)
7. **Logging placement**: Only add logging to high-level modules (scrapers, CLI), never in low-level code
8. **Error handling**: Low-level code raises exceptions, high-level code catches and logs

## Code Quality Guidelines

### When Adding Features
- Write unit tests for new utility functions and data models
- Use existing fixtures in `tests/conftest.py` for test data
- Keep tests focused on pure logic, avoid external API dependencies
- Update `tests/README.md` if adding new test categories

### Error Handling Best Practices
- **Low-level functions**: Raise exceptions with detailed messages, no logging
- **Scrapers**: Catch specific exceptions, log with context, re-raise or handle gracefully
- **CLI**: Final exception handler, user-friendly messages, `--verbose` for tracebacks
- Include relevant context in error messages (file paths, URLs, counts)

## Semantic Commit Messages
Per `CONTRIBUTING.md`, use conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation
- `style:` formatting (no logic change)
- `chore:` maintenance (deps, etc.)

## External Dependencies
- **Pinterest API**: Unofficial, reverse-engineered (may break)
- **ffmpeg**: Required for video downloads (user must install)
- **Selenium**: WebDriver automation requires ChromeDriver/GeckoDriver
- **pyexiv2**: Metadata embedding (requires exiv2 library)

## Future Directions (from TODO.md)
- [x] Unit testing framework (pytest with 35 tests)
- [ ] Scrape nested boards support
- [ ] Video scraping enhancements (m3u8 improvements)
