# Pinterest-DL AI Coding Instructions

## Project Overview

Pinterest-DL is a Python-based Pinterest media scraper/downloader supporting both reverse-engineered API and Selenium WebDriver approaches. Core purpose: scrape images/videos from Pinterest boards/pins (including private content with cookies) and download them asynchronously.

**Version**: 1.0.0 (Refactored Architecture)

**Key Architecture Pattern**: Dual scraping strategy with unified interface via `PinterestDL` factory class:

- **API mode** (`ApiScraper`): Fast, reverse-engineered Pinterest API (default)
- **WebDriver mode** (`WebDriverScraper`): Selenium-based, slower but more reliable

# Engineering Philosophy

_"Clay becomes pottery through craft, but it's the emptiness that makes a pot useful."_ — Laozi

Our engineering culture is built on **Locality**, **Simplicity**, and **Explicitness**. We prioritize code that is easy to reason about, easy to delete, and easy to maintain over code that is "clever" or "dry" at the cost of cognitive load.

## 1. Locality First

**Cognitive Proximity**
Code logic must reside as close as possible to the data it manipulates. Minimize the physical distance between variable declaration and usage.

- **The "Jump" Test:** If understanding a function requires opening more than two other files, the code is too fragmented.
- **Minimizing Context Switching:** Engineers should be able to interact with documentation and code using the same tools.

**Data Locality**
Prioritize contiguous memory layouts (arrays/structs) over pointer-chasing structures (linked lists/trees) to maximize CPU cache hits.

## 2. Radical Simplicity

**The "Rule of Three"**
Strictly prohibit abstraction until a pattern emerges three times. Duplication is preferable to the wrong abstraction.

**Usage-Based Extraction**
Functions or classes exist solely to reduce complexity, not for semantic categorization. If a block of logic is used once, it remains inline.

**Shallow Hierarchies**
Enforce flat dependency structures. Deep inheritance trees and multi-layer wrappers ("lasagna code") are anti-patterns. Composition is strictly preferred over inheritance.

## 3. Explicit Execution

**Linearity**
Prefer explicit control flow over implicit behaviors (e.g., magic methods, AOP, hidden middleware). Code should be readable linearly from top to bottom.

- **Early Returns:** Minimize nesting depth. Use guard clauses to exit functions early.
- **Switch/Match Completeness:** Exhaustive pattern matching is mandatory.

**Type Strictness**
Use strong, static typing to enforce constraints at compile time. Avoid `any` or `void` pointers unless interfacing with low-level boundaries.

## 4. Documentation & Maintenance

**Minimum Viable Documentation**
Docs thrive when they're treated like tests: a necessary chore. Brief and utilitarian is better than long and exhaustive.

- **Readable Source Text:** Content and presentation should not mingle. Plain text suffices.
- **Freshness:** Static content is better than dynamic, but fresh is better than stale.

**Better is Better than Best**
Incremental improvement is better than prolonged debate. Patience and tolerance of imperfection allow projects to evolve organically.

**Deprecation Policy**
Dead code is deleted immediately, not commented out. Version control is the archive; the codebase is the current state.

**ASCII-Only Documentation**
Use only ASCII characters in documentation and user-facing text:
- Use `->` instead of `→` for arrows
- Use `-` instead of `–` (en-dash) in tables
- Use `...` instead of `…` (ellipsis)
- Exception: Non-ASCII is acceptable in translated content (e.g., Chinese README)
- Rationale: Better compatibility across terminals, editors, and systems

## Critical Architecture Components (Version 1.0)

### 1. Entry Points & Factory Pattern

- `pinterest_dl/__init__.py`: Main factory class `PinterestDL` with static methods:
  - `PinterestDL.with_api()` -> `ApiScraper` instance (renamed from `_ScraperAPI`)
  - `PinterestDL.with_browser()` -> `WebDriverScraper` instance (renamed from `_ScraperWebdriver`)
- Both scrapers use shared operations from `scrapers/operations.py` module
- CLI entry point: `pinterest_dl/cli.py` (also aliased as `pin-dl`)

**Key 1.0 Changes:**
- Removed `Pinterest` prefix from internal class names
- Scrapers now use clear public names: `ApiScraper`, `WebDriverScraper`
- Deprecated old names (`_ScraperAPI`, `_ScraperWebdriver`) with warnings (removal in 1.1.0)
- Converted base class to module functions (removed inheritance pattern)

### 2. Data Flow Architecture

```
User Input (URL/Query)
  |
  v
Scraper (API or WebDriver) -> PinterestMedia objects
  |
  v
Downloader (concurrent, ThreadPoolExecutor) -> Local files
  |
  v
Optional: Caption embedding (metadata/txt/json)
```

### 3. Core Data Model & Layer Separation

**Domain Layer** (`domain/`): Core business objects

- `domain/media.py`: `PinterestMedia` dataclass
  - Holds image/video metadata, resolution, URLs
  - `VideoStreamInfo`: HLS stream metadata (resolution, duration, URL)
  - **Critical**: Media can have both static image (`src`) and video stream (`video_stream`)
- `domain/cookies.py`: Cookie management utilities
- `domain/browser.py`: Browser configuration (Chrome/Firefox types)

**Storage Layer** (`storage/`): File I/O operations

- `storage/media.py`: Save media to disk, handle caption files (txt/json/metadata)

**Parser Layer** (`parsers/`): Data transformation

- `parsers/response.py`: Pinterest API response parsing

**Legacy Support** (`data_model/`):
- Maintained for backward compatibility
- Re-exports from `domain/` with deprecation warnings
- Will be removed in 1.1.0

### 4. Scraper Layer

**Scrapers** (`scrapers/`):

- `scrapers/api_scraper.py`: `ApiScraper` class
  - Methods: `scrape()`, `search()`, `scrape_and_download()`, `search_and_download()`
- `scrapers/webdriver_scraper.py`: `WebDriverScraper` class
  - Methods: `scrape()`, `scrape_and_download()`, `login()`
- `scrapers/operations.py`: Shared scraper operations (module functions)
  - `download_media()`, `add_captions_to_file()`, `add_captions_to_meta()`, `prune_images()`

**Key 1.0 Refactoring:**
- Converted `_ScraperBase` static-only class to module functions
- Removed inheritance (was causing maintenance overhead)
- Scrapers import functions directly from `operations.py`

### 5. Low-Level Subsystems

**API Layer** (`api/`):

- `api/api.py`: Pinterest API client (renamed from `pinterest_api.py`)
  - URL parsing, cookie handling, request construction
  - Removed `Pinterest` prefixes from method names
- `api/bookmark_manager.py`: Pagination bookmark management
- `api/endpoints.py`: API endpoint definitions
- `api/pinterest_response.py`: Legacy response parsing (use `parsers/response.py`)

**Download Layer** (`download/`):

- `download/http_client.py`: HTTP session with retry logic, HLS integration
- `download/downloader.py`: `MediaDownloader` (renamed from `PinterestMediaDownloader`)
  - Concurrent coordinator using `ThreadPoolExecutor`
  - Progress callbacks via `TqdmProgressBarCallback`
- `download/request_builder.py`: Pinterest API request URL construction

**Video Processing** (`download/video/`):

- `download/video/hls_processor.py`: HLS video stream downloader
  - M3U8 playlist parsing, AES-128 decryption
  - Requires **ffmpeg** in PATH
- `download/video/key_cache.py`: Decryption key cache
- `download/video/segment_info.py`: Segment metadata

**WebDriver Layer** (`webdriver/`):

- `webdriver/driver.py`: Selenium scraping (renamed from `pinterest_driver.py`)
  - Removed `Pinterest` prefix from classes
- `webdriver/browser.py`: Browser initialization (Chrome/Firefox)
- `webdriver/driver_installer.py`: Auto-download ChromeDriver/GeckoDriver

**Common Utilities** (`common/`):

- `common/ensure_executable.py`: Check for required executables (ffmpeg)
- `common/io.py`: File I/O utilities

### 6. Cookie Authentication Pattern

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

# Local - use domain layer for models
from pinterest_dl.domain.media import PinterestMedia
from pinterest_dl.exceptions import DownloadError
```

**Key 1.0 Import Changes:**
- Import `PinterestMedia` from `pinterest_dl.domain.media` (not `data_model`)
- Use `ApiScraper`/`WebDriverScraper` (not `_ScraperAPI`/`_ScraperWebdriver`)
- Import from `pinterest_dl.api.api` (not `pinterest_dl.low_level.api.pinterest_api`)

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

- See `_ConcurrentCoordinator` in `download/downloader.py`
- Progress callbacks via `report(done, total)`
- Error accumulation with optional `fail_fast` mode

## Version 1.0 Refactoring Summary

### Architectural Improvements

**1. Layer Separation:**
- Split `data_model/` into `domain/`, `parsers/`, and `storage/`
- Clear separation of concerns: business logic vs data transformation vs I/O

**2. Naming Clarity:**
- Removed `Pinterest` prefix from internal classes (`PinterestAPI` -> `API`)
- Public scrapers now use descriptive names (`ApiScraper`, `WebDriverScraper`)
- Deprecated old internal names (`_ScraperAPI`, `_ScraperWebdriver`)

**3. Reduced Coupling:**
- Converted static-only base class to module functions
- Removed inheritance-based code sharing
- Scrapers now compose functionality from `operations.py`

**4. Directory Reorganization:**
- Moved `low_level/hls/` -> `download/video/`
- Moved `low_level/webdriver/` -> `webdriver/`
- Renamed `utils/` -> `common/` for clarity
- Moved `low_level/http/` -> `download/`
- Created `api/` at top level (from `low_level/api/`)

**5. Backward Compatibility:**
- Full compatibility maintained via deprecation warnings
- Old names still work (e.g., `_ScraperAPI`, `data_model.PinterestMedia`)
- Warnings added for all deprecated APIs
- Removal planned for 1.1.0

**6. Testing:**
- 56 comprehensive tests (35 original + 22 backward compatibility tests)
- All tests passing
- Covers deprecated APIs, new APIs, and migration paths

### Version History

- **1.0.0**: Architecture refactoring, improved stability
- **0.8.x**: Pre-refactor versions with `low_level/` structure

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

**56 unit tests** covering critical paths (pytest framework):

- ✅ `tests/test_pinterest_media.py` - Data models and serialization
- ✅ `tests/test_pinterest_api.py` - URL parsing and validation
- ✅ `tests/test_cli_utils.py` - CLI utility functions
- ✅ `tests/test_exceptions.py` - Exception handling and error messages
- ✅ `tests/test_backward_compatibility.py` - Deprecated API warnings (22 tests)

Run tests:

```powershell
# All tests
pytest tests/

# Verbose output
pytest tests/ -v

# Specific file
pytest tests/test_pinterest_media.py

# Backward compatibility tests only
pytest tests/test_backward_compatibility.py -v
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
__version__ = "1.0.0"  # Increment here
```

## Key Workflows

### Adding New Caption Formats

1. Update `cli.py` choices: `["txt", "json", "metadata", "none", "YOUR_FORMAT"]`
2. Implement in `operations.py` module function `add_captions_to_file()` or new function
3. Update README examples

### Supporting New Media Types

1. Add URL parsing to `api/api.py` `_parse_*` methods
2. Create endpoint in `api/endpoints.py`
3. Implement scraping logic in `scrapers/api_scraper.py` or `scrapers/webdriver_scraper.py`
4. Handle in `download/downloader.py` `MediaDownloader.download()`

### Extending HLS Processing

- Modify `download/video/hls_processor.py` for new encryption methods
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

- [x] Unit testing framework (pytest with 56 tests)
- [ ] Scrape nested boards support
- [ ] Video scraping enhancements (m3u8 improvements)
