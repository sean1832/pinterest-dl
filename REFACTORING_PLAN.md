# Pinterest-DL Architecture Analysis & Refactoring Plan

**Date Started:** January 30, 2026  
**Status:** 🔄 **IN PROGRESS** - Phase 1 Complete  
**Last Updated:** January 30, 2026  
**Goal:** Align codebase with Locality, Simplicity, and Explicitness principles

---

## Progress Overview

### Completed Tasks ✅
- **Phase 1, Task 1.1:** Split PinterestMedia Class (COMPLETED)
  - Created `response_parser.py` (180 lines)
  - Created `media_file_handler.py` (120 lines)
  - Refactored `pinterest_media.py` (244 → 141 lines)
  - All 35 tests passing

### Current Metrics
| Metric               | Original  | Current   | Target     | Status        |
| -------------------- | --------- | --------- | ---------- | ------------- |
| **Largest file**     | 649 lines | 649 lines | <300 lines | ⏳ Next phase  |
| **Data model size**  | 244 lines | 141 lines | <150 lines | ✅ Achieved    |
| **Files >300 lines** | 3 files   | 2 files   | 0 files    | 🔄 In progress |
| **Test pass rate**   | 35/35     | 35/35     | 35/35      | ✅ Maintained  |

---

## Executive Summary

The current codebase has grown to 3,000+ lines across 20+ modules with several critical violations of our stated engineering philosophy. Major issues include:

- **649-line god class** (`scraper_api.py`) with multiple responsibilities
- ~~**300-line data model** mixing data structure, parsing, and file I/O~~ ✅ **FIXED**
- **Fake inheritance hierarchy** providing no polymorphism
- **Premature abstractions** extracted before second use case existed
- **30+ lines of CLI argument duplication**
- **Missing type hints** in ~15% of functions

**Target Metrics:**
- Largest file: 649 → <300 lines
- Files >300 lines: 3 → 0
- Inheritance depth: 2 → 0 levels
- Static-only classes: 4 → 0
- Type hint coverage: 85% → 100%

---

## Current Architecture Overview

### Module Structure

```
pinterest_dl/
├── __init__.py              # Factory class (88 lines)
├── data_model/
│   ├── pinterest_media.py   # ✅ REFACTORED: 141 lines (was 244)
│   ├── response_parser.py   # ✅ NEW: 180 lines (API response parsing)
│   ├── media_file_handler.py # ✅ NEW: 120 lines (file operations)
│   ├── cookie.py
│   └── browser_version.py
├── cli.py                   # CLI entry point (311 lines)
├── exceptions.py            # Exception hierarchy (well-designed ✅)
├── data_model/
│   ├── pinterest_media.py   # 🔴 CRITICAL: 300 lines, multiple concerns
│   ├── cookie.py            # Cookie conversion utilities
│   └── browser_version.py   # Simple version class
├── scrapers/
│   ├── scraper_base.py      # 🔴 CRITICAL: Fake inheritance base (168 lines)
│   ├── scraper_api.py       # 🔴 CRITICAL: 649-line god class
│   └── scraper_webdriver.py # WebDriver scraper (213 lines)
├── low_level/
│   ├── api/                 # Pinterest API client
│   ├── http/                # HTTP client & downloader
│   ├── hls/                 # HLS video processing ✅
│   └── webdriver/           # Selenium automation
└── utils/                   # I/O, progress bars, executable checks
```

### Dependency Flow

```
CLI → Scrapers (high-level, logging) → Low-Level (raise only) → Data Model
```

**Jump Test Results:**
- Understanding `scraper_api.scrape()`: **7 file jumps** ❌ (target: <3)
- Understanding `PinterestMedia`: **5 concept jumps** ❌ (data → parsing → PIL → pyexiv2 → HLS)

---

## Critical Issues (Must Fix)

### 1. LOCALITY VIOLATION: PinterestMedia Doing Too Much

**File:** `pinterest_dl/data_model/pinterest_media.py` (300 lines)

**Problem:** Single class mixing 6 different concerns:
1. **Data structure** (lines 15-28)
2. **Serialization** (`to_dict()`, `from_dict()`)
3. **API response parsing** (`from_responses()` - 100+ lines)
4. **Video variant selection** (`_select_video_by_resolution()`)
5. **File I/O operations** (`add_caption()`, `save_img()`, `save_media()`)
6. **Metadata manipulation** (`add_text_caption()`, `add_json_caption()`)

**Cognitive Load:** To understand what a `PinterestMedia` object *is*, you must read:
- Data fields (scattered)
- PIL Image operations
- pyexiv2 metadata operations  
- Complex Pinterest API response parsing
- HLS video stream logic

**Example Violation:**
```python
# Lines 120-230: API response parsing in data model class
@classmethod
def from_responses(cls, response_data: List[Dict[str, Any]], ...):
    # 100+ lines of nested dict navigation
    # Video stream resolution logic
    # min_resolution filtering
    # This should be in ResponseParser, not data model!
```

**Refactoring Plan:**
```
pinterest_media.py (300 lines)
    ↓ SPLIT INTO ↓
pinterest_media.py (80 lines)      # Pure data class + validation
response_parser.py (120 lines)     # from_responses() → PinterestMedia
media_file_handler.py (100 lines)  # File I/O, caption embedding
```

**Benefits:**
- ✅ Data locality: Data structure separate from operations
- ✅ Single responsibility per file
- ✅ Easy to test each concern independently
- ✅ Jump test: Understanding data model = 1 file (currently 5 concepts)

---

### 2. SIMPLICITY VIOLATION: Fake Inheritance Hierarchy

**Files:** 
- `pinterest_dl/__init__.py` (PinterestDL inherits _ScraperBase)
- `pinterest_dl/scrapers/scraper_base.py` (static-only base class)

**Problem:** Inheritance providing ZERO polymorphism:

```python
# __init__.py
class PinterestDL(_ScraperBase):  # ❌ WHY INHERIT?
    def __init__(self):
        pass  # No state!
    
    @staticmethod
    def with_api(...) -> "_ScraperAPI":  # Returns different class
        return _ScraperAPI(...)
    
    @staticmethod
    def with_browser(...) -> "_ScraperWebdriver":  # Returns different class
        return _ScraperWebdriver(...)
```

**Reality Check:**
- ❌ `PinterestDL` has NO instance state
- ❌ All methods are `@staticmethod`
- ❌ Callers receive concrete types (`_ScraperAPI`, `_ScraperWebdriver`), not base type
- ❌ No polymorphic behavior (can't substitute base for derived)
- ❌ `_ScraperBase` is also all static methods (no shared state)

**Violation:** "Rule of Three" - abstraction created before pattern emerged. There's no third scraper to justify the base class.

**Refactoring Plan:**
```python
# __init__.py - Remove inheritance entirely
class PinterestDL:
    """Factory for creating Pinterest scrapers."""
    
    @staticmethod
    def with_api(...) -> "ScraperAPI":
        return ScraperAPI(...)
    
    @staticmethod
    def with_browser(...) -> "ScraperWebdriver":
        return ScraperWebdriver(...)

# scraper_base.py → scraper_utils.py (module, not class)
def download_media(media_list: List[PinterestMedia], ...):
    """Module-level function, not class method."""
    # Shared download logic

def add_captions_to_file(file_path: Path, ...):
    """Module-level function for caption embedding."""
    # Shared caption logic
```

**Benefits:**
- ✅ No fake OOP - use modules for organization
- ✅ Explicit: Functions are just functions
- ✅ Shallow hierarchy: 2 levels → 0 levels
- ✅ Inheritance depth metric: 100% flat

---

### 3. LOCALITY VIOLATION: 649-Line God Class

**File:** `pinterest_dl/scrapers/scraper_api.py` (LARGEST FILE)

**Problem:** Single class with 7+ responsibilities:

| Lines   | Responsibility             | Jump Count |
| ------- | -------------------------- | ---------- |
| 38-84   | Cookie management          | Internal   |
| 86-126  | Pin scraping               | +2 files   |
| 128-210 | Download orchestration     | +3 files   |
| 212-280 | Search scraping            | +2 files   |
| 282-340 | Image uniqueness filtering | +1 file    |
| 342-420 | Progress bar management    | Internal   |
| 425-485 | Board scraping             | +3 files   |

**Jump Test Failure:** Understanding `scrape()` requires jumping to:
1. `_get_images()` (same file)
2. `_scrape_pin()` or `_scrape_board()` (same file)
3. `_download_and_dedupe()` (same file)
4. `BookmarkManager.get()` (different file)
5. `PinterestAPI.get_*()` (different file)
6. `download_media()` (scraper_base.py)
7. `PinterestMediaDownloader.download()` (downloader.py)

**Total: 7 jumps** ❌ (target: <3)

**Refactoring Plan:**
```
scraper_api.py (649 lines)
    ↓ SPLIT INTO ↓
pin_scraper.py (180 lines)        # Pin-specific scraping logic
board_scraper.py (160 lines)      # Board-specific scraping logic
search_scraper.py (140 lines)     # Search-specific scraping logic
scraper_api.py (169 lines)        # Factory + shared cookie/bookmark logic
```

**Benefits:**
- ✅ Each scraper type in its own file (locality)
- ✅ Related logic stays together
- ✅ Jump test: <3 files per workflow
- ✅ No file >300 lines

---

### 4. SIMPLICITY VIOLATION: Premature Abstraction

**File:** `pinterest_dl/low_level/http/downloader.py`

**Problem:** Two-layer abstraction where one would suffice:

1. `_ConcurrentCoordinator` (lines 10-65) - Generic concurrent executor
2. `PinterestMediaDownloader` (lines 68-160) - Wraps HttpClient, uses coordinator

**Issue:**
- ❌ `_ConcurrentCoordinator` is ONLY used by `PinterestMediaDownloader`
- ❌ Never reused elsewhere in codebase
- ❌ Adds 65 lines of indirection for no benefit
- ❌ Generic "worker" callback pattern when direct implementation clearer

**Violation:** "Usage-Based Extraction" - extracted before second use case existed.

**Example:**
```python
# downloader.py lines 24-40
class _ConcurrentCoordinator:
    def run(self, items, output_dir, worker: Callable, ...):
        # Generic implementation that could be inline
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            result = worker(item, output_dir)  # ❌ Callback abstraction
```

**Refactoring Plan:**
```python
# Inline the concurrent logic directly in PinterestMediaDownloader
class PinterestMediaDownloader:
    def download_concurrent(self, media_list, output_dir, ...):
        """Direct implementation, no coordinator abstraction."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._download_single, m, output_dir): m
                for m in media_list
            }
            # ... handle results directly (40 lines total)
```

**Benefits:**
- ✅ -65 lines of unnecessary abstraction
- ✅ Linear control flow (no callbacks)
- ✅ Easier to debug (fewer indirection layers)
- ✅ Follows "extract on third use" rule

---

### 5. LOCALITY VIOLATION: CLI Argument Duplication

**File:** `pinterest_dl/cli.py` lines 71-123

**Problem:** `scrape` and `search` commands share 15+ identical arguments, but defined separately (90% duplication):

```python
# Lines 71-95: scrape command
scrape_cmd.add_argument("-o", "--output", type=str, help="Output directory")
scrape_cmd.add_argument("-c", "--cookies", type=str, help="...")
scrape_cmd.add_argument("-n", "--num", type=int, default=100, ...)
scrape_cmd.add_argument("--video", action="store_true", ...)
# ... 15+ arguments

# Lines 97-123: search command - EXACT SAME ARGUMENTS ❌
search_cmd.add_argument("-o", "--output", type=str, help="Output directory")
search_cmd.add_argument("-c", "--cookies", type=str, help="...")
# ... copy-pasted 15+ arguments
```

**Impact:** 30+ lines of duplication. Changes to shared options (like `--caption-format`) must be made in 2 places.

**Refactoring Plan:**
```python
def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by scrape and search commands."""
    parser.add_argument("-o", "--output", type=str, help="Output directory")
    parser.add_argument("-c", "--cookies", type=str, help="...")
    parser.add_argument("-n", "--num", type=int, default=100, ...)
    # ... all 15+ shared arguments

# Usage:
scrape_cmd = subparsers.add_parser("scrape", ...)
_add_common_arguments(scrape_cmd)

search_cmd = subparsers.add_parser("search", ...)
_add_common_arguments(search_cmd)
```

**Benefits:**
- ✅ -30 lines duplication
- ✅ Single source of truth for shared arguments
- ✅ Locality: All argument definitions in one place

---

## High-Priority Issues (Should Fix)

### 6. EXPLICITNESS VIOLATION: Implicit Control Flow

**File:** `pinterest_dl/scrapers/scraper_api.py` lines 500-545

**Problem:** Boolean parameter changes entire method behavior:

```python
def _get_images(
    self, api, batch_size, bookmarks, min_resolution,
    board_id: Optional[str] = None,  # ❌ Implicit mode switch
):
    response = (
        api.get_related_images(batch_size, bookmarks.get())
        if not board_id  # ❌ Hard to trace which path taken
        else api.get_board_feed(board_id, batch_size, bookmarks.get())
    )
```

**Issues:**
- ❌ Non-linear reading (must evaluate `board_id` state mentally)
- ❌ Magic parameter changes entire behavior
- ❌ Ternary operator obscures control flow
- ❌ Duplicate code: `_get_videos()` (lines 547-570) is 90% identical

**Refactoring Plan:**
```python
# Explicit, separate methods
def _get_pin_images(self, api, batch_size, bookmarks, min_resolution):
    """Get images for a pin (no board_id needed)."""
    response = api.get_related_images(batch_size, bookmarks.get())
    # ... clear linear flow

def _get_board_images(self, api, board_id: str, batch_size, bookmarks, min_resolution):
    """Get images for a board (board_id required)."""
    response = api.get_board_feed(board_id, batch_size, bookmarks.get())
    # ... clear linear flow
```

**Benefits:**
- ✅ Linear readability (top to bottom)
- ✅ Explicit: Method name declares intent
- ✅ No magic parameters
- ✅ Type system enforces required parameters

---

### 7. EXPLICITNESS VIOLATION: Magic Numbers

**File:** `pinterest_dl/scrapers/scraper_api.py` multiple locations

**Problem:** Unexplained magic numbers for bookmark manager:

```python
# Line 94
bookmarks = BookmarkManager(3)  # ❌ WHY 3? What does this mean?

# Line 233
bookmarks = BookmarkManager(1)  # ❌ Different for search, why?

# Line 443
bookmarks = BookmarkManager(3)  # ❌ Again 3, but why?
```

**Missing Context:**
- No constant explaining what numbers represent
- No comment explaining semantic difference
- Reader must jump to `BookmarkManager` class to understand `last` parameter
- Inconsistent values suggest different behaviors but no documentation

**Refactoring Plan:**
```python
# At module top
PIN_BOOKMARK_HISTORY = 3      # Keep last 3 bookmarks for pin pagination
SEARCH_BOOKMARK_HISTORY = 1   # Keep only last bookmark for search (faster)
BOARD_BOOKMARK_HISTORY = 3    # Keep last 3 bookmarks for board pagination

# Usage (explicit)
bookmarks = BookmarkManager(PIN_BOOKMARK_HISTORY)
```

**Benefits:**
- ✅ Self-documenting code
- ✅ Single source of truth for constants
- ✅ Comments explain *why* values differ

---

### 8. EXPLICITNESS VIOLATION: Missing Type Hints

**Examples Found:**

#### `browser.py` line 81:
```python
def Firefox(self, image_enable=False, incognito=False, headful=False):
    # ❌ All parameters missing type hints
```

**Fixed:**
```python
def Firefox(
    self,
    image_enable: bool = False,
    incognito: bool = False,
    headful: bool = False
) -> webdriver.Firefox:
```

#### `io.py` line 17:
```python
@staticmethod
def randdelay(a, b) -> None:  # ❌ a, b have no type hints
    time.sleep(random.uniform(a, b))
```

**Fixed:**
```python
@staticmethod
def randdelay(a: float, b: float) -> None:
    """Sleep for random duration between a and b seconds."""
    time.sleep(random.uniform(a, b))
```

#### `io.py` lines 45-50:
```python
def unzip(zip_path: Path, extract_to: Path, target_file: Optional[str] = None, verbose: bool = False) -> None:
    # Good type hints ✅, but...
    if not zip_path or not str(zip_path).endswith(".zip"):  # ❌ Runtime check instead of type
```

**Fixed:**
```python
def unzip(
    zip_path: Path,
    extract_to: Path,
    target_file: Optional[str] = None,
    verbose: bool = False
) -> None:
    """Extract zip file. Raises ValueError if path invalid."""
    if not zip_path.exists():
        raise ValueError(f"Zip file does not exist: {zip_path}")
    if zip_path.suffix != ".zip":
        raise ValueError(f"Not a zip file: {zip_path}")
    # ...
```

**Target:** 100% type hint coverage on public APIs

---

### 9. ERROR HANDLING VIOLATION: Print in Low-Level Code

**File:** `pinterest_dl/low_level/webdriver/driver_installer.py`

**Problem:** Low-level module printing directly to stdout:

```python
# Line 35
print(f"Current Chrome driver version: {current_version}")  # ❌ LOW-LEVEL PRINT

# Line 63
print(f"Installing latest Chrome driver...")  # ❌ LOW-LEVEL PRINT

# Line 67
print("Running in incognito mode")  # ❌ LOW-LEVEL PRINT
```

**Violation:** Per architecture guidelines:
> **Low-Level Modules** (API, HTTP, HLS, WebDriver utils):
> - **NO logging** - only raise exceptions with clear, informative messages
> - Exceptions bubble up to higher levels

**Refactoring Plan:**
```python
# Option 1: Return status to caller (preferred for informational messages)
def install_driver(self, version: Optional[str] = None) -> InstallStatus:
    """Install ChromeDriver. Returns status for caller to log/print."""
    current = self._get_current_version()
    if version:
        # ... install logic
        return InstallStatus(current_version=current, installed_version=version)

# Option 2: Use logging at WARNING level only (for actual issues)
import logging
logger = logging.getLogger(__name__)

def install_driver(self, version: Optional[str] = None):
    """Install ChromeDriver."""
    # logger.warning() for problems only, not info
    if not self._check_compatibility():
        logger.warning("ChromeDriver version may be incompatible")
```

**Benefits:**
- ✅ Caller controls output (CLI can print, tests can suppress)
- ✅ Follows stated architecture (low-level raises, high-level logs)
- ✅ Testable (no stdout pollution in tests)

---

## Medium-Priority Issues (Nice to Have)

### 10. Code Smell: Long Functions

**Examples:**

1. `scraper_api.py` `scrape_board()` (lines 425-485) - **60 lines**
2. `pinterest_media.py` `from_responses()` (lines 120-230) - **110 lines**
3. `cli.py` `main()` (lines 135-311) - **176 lines**

**Refactoring Strategy:**
- Extract to smaller, named functions
- Target: <50 lines per function
- Use early returns to reduce nesting

---

### 11. Code Smell: Deep Nesting

**Example:** `pinterest_media.py` lines 145-190 (5 levels deep):

```python
for item in response_data:
    if not isinstance(item, dict):
        continue
    orig = item.get("images", {}).get("orig")
    if not orig:
        continue
    try:
        width = int(orig.get("width", 0))
        height = int(orig.get("height", 0))
    except (TypeError, ValueError):
        continue
    if width < min_width or height < min_height:
        continue
    # ... 40 more lines at 4+ indent levels
```

**Refactoring Strategy:**
```python
def _parse_media_item(item: Dict[str, Any], min_width: int, min_height: int) -> Optional[PinterestMedia]:
    """Parse single media item. Returns None if invalid."""
    if not isinstance(item, dict):
        return None
    
    orig = item.get("images", {}).get("orig")
    if not orig:
        return None
    
    try:
        width = int(orig.get("width", 0))
        height = int(orig.get("height", 0))
    except (TypeError, ValueError):
        return None
    
    if width < min_width or height < min_height:
        return None
    
    # ... rest of parsing (now at 1-2 indent levels)

# Main loop (simple)
media_items = [
    parsed for item in response_data
    if (parsed := _parse_media_item(item, min_width, min_height))
]
```

**Benefits:**
- ✅ Max 2 indent levels
- ✅ Early returns (guard clauses)
- ✅ Named extraction function (self-documenting)

---

### 12. Code Smell: Unclear Naming

**Examples:**

1. `scraper_api.py` line 152: `_prune_by_count()`
   - **Issue:** "prune" suggests removing, but it RETURNS kept images
   - **Better:** `_limit_to_count()` or `_take_first_n()`

2. `bookmark_manager.py` line 8: `last` parameter
   - **Issue:** Unclear what "last" means without reading docs
   - **Better:** `history_size` or `max_bookmarks`

3. `key_cache.py` line 76: `_prefetch_keys()` vs `_fetch_keys()`
   - **Issue:** Naming doesn't convey "cached" vs "current"
   - **Better:** `_load_cached_keys()` vs `_download_keys()`

---

### 13. Documentation: Missing Docstrings

**Missing or Incomplete:**

1. `pinterest_dl/__init__.py` - `PinterestDL` class has no docstring
2. `low_level/api/pinterest_api.py` - Inconsistent doc formats (some `"""`, some don't)
3. `scrapers/scraper_base.py` - `download_media()` lacks parameter documentation

**Target:** All public classes/functions have:
- One-line summary
- Parameter descriptions
- Return value description
- Raises section (for exceptions)

---

### 14. Documentation: Over-Commented Tutorial Code

**File:** `pinterest_dl/low_level/api/__init__.py` lines 35-70

**Problem:** 45+ lines of commented-out example code in `__init__.py`:

```python
# # ==============================================
# # Example usage [Requests -> Selenium]:
# # ==============================================
# # from pinterest_dl.low_level.api import PinterestAPI
# # api = PinterestAPI()
# # ... 40 more lines
```

**Issue:** Tutorial content shouldn't be in production code.

**Refactoring Plan:**
- Move to `examples/api_usage.py`
- Or move to `README.md`
- Or move to `docs/tutorials/`

---

### 15. Import Organization: Inconsistent Style

**File:** `pinterest_dl/low_level/api/__init__.py`

**Issues:**

```python
# ruff: noqa: F401  # ❌ Suppresses linting warnings

from typing import Any, Dict, Literal, Union
import requests
from pinterest_dl.low_level.http.http_client import HttpClient

USER_AGENT = (...)  # ❌ Mixed imports with constants

def fetch(url, ...):  # ❌ Function in __init__.py (anti-pattern)
    if isinstance(url, str):
        req = requests.get(url)  # ❌ Direct requests, not using HttpClient
```

**Problems:**
1. `fetch()` duplicates `HttpClient` functionality
2. Mixing module-level constants with functions in `__init__.py`
3. Not following import order (third-party mixed with local)

**Refactoring Plan:**
- Remove `fetch()` function (use `HttpClient`)
- Move `USER_AGENT` to `constants.py`
- Clean imports (stdlib → third-party → local)

---

### 16. Import Organization: Circular Import Risk

**File:** `pinterest_dl/low_level/webdriver/pinterest_driver.py` line 8

**Problem:**
```python
from pinterest_dl.low_level.webdriver.pinterest_driver import PinterestDriver, PinterestMedia
```

Imports `PinterestMedia` from driver (wrong layer) instead of from `data_model/`.

**Refactoring Plan:**
```python
from pinterest_dl.data_model.pinterest_media import PinterestMedia
from pinterest_dl.low_level.webdriver.pinterest_driver import PinterestDriver
```

---

## Positive Patterns (Keep These!) ✅

### 1. Excellent Exception Hierarchy

**File:** `pinterest_dl/exceptions.py`

**What's Good:**
- Clear inheritance tree (`PinterestAPIError` → specific errors)
- `HttpResponseError` has useful `.dump()` method for debugging
- Exception names are descriptive (`InvalidBoardUrlError` vs generic `ValueError`)
- Each exception includes context (URL, status code, raw response)

**Example:**
```python
class HttpResponseError(PinterestAPIError):
    def dump(self, file_path: Path) -> None:
        """Save raw response to file for debugging."""
        # ... helpful debugging functionality
```

**Keep this pattern!**

---

### 2. Good Use of Dataclasses

**File:** `pinterest_dl/low_level/hls/segment_info.py`

**What's Good:**
```python
@dataclass
class SegmentInfo:
    index: int
    uri: str
    method: Optional[Literal["AES-128"]]
    key_uri: Optional[str]
    iv: Optional[bytes]
    media_sequence: int
```

- Simple, explicit, type-safe
- Perfect locality (data + validation in one place)
- Self-documenting structure

**Keep this pattern!**

---

### 3. Clear Separation in HLS Module

**Files:** `pinterest_dl/low_level/hls/`

**What's Good:**
- `hls_processor.py` - Orchestration logic
- `key_cache.py` - Caching concern (single responsibility)
- `segment_info.py` - Data structure

Each file has ONE clear responsibility. This is the target pattern!

---

### 4. Explicit Error Handling in HlsProcessor

**File:** `pinterest_dl/low_level/hls/hls_processor.py` lines 50-85

**What's Good:**
```python
def enumerate_segments(self, playlist, base_uri):
    if not playlist.segments:
        raise HlsDownloadError("Playlist has no segments")
    # ...
    if method != "AES-128":
        raise HlsDownloadError(f"Unsupported encryption method: {method}")
    if not key_info.uri:
        raise HlsDownloadError("Encrypted segment without key URI")
```

- Clear early returns
- Explicit error messages with context
- No implicit behavior
- Low-level code raises (doesn't log) ✅

**Keep this pattern!**

---

### 5. Good Type Usage in Newer Code

**File:** `pinterest_dl/low_level/http/downloader.py`

**What's Good:**
```python
from typing import Callable, Dict, List, Optional, TypeVar

ProgressCallback = Callable[[int, int], None]  # Type alias for clarity
T = TypeVar("T")  # Generic type variable

class PinterestMediaDownloader:
    def __init__(self, http_client: HttpClient, progress_callback: Optional[ProgressCallback] = None):
        # ...
```

- Type aliases for complex types
- TypeVar for generic code
- Full type hint coverage

**Keep this pattern!**

---

### 6. Flat Directory Structure

**What's Good:**
```
pinterest_dl/
  scrapers/        # High-level (logging, error handling)
  low_level/       # Low-level utilities (raise only)
    api/
    http/
    hls/
    webdriver/
  data_model/      # Shared data structures
  utils/           # Cross-cutting concerns
```

- Only 2-3 levels deep
- Organized by technical concern (not arbitrary business logic)
- Clear separation: high-level vs low-level

**Keep this structure!**

---

## Refactoring Implementation Plan

### Phase 1: Foundation (Core Data & Utils)

**Priority: CRITICAL**  
**Estimated Effort:** 2-3 days  
**Status:** ✅ **COMPLETED** (January 30, 2026)

#### Task 1.1: Split PinterestMedia Class ✅ COMPLETED
- [x] Create `response_parser.py` - Extract `from_responses()` static method (180 lines)
- [x] Create `media_file_handler.py` - Extract file I/O methods (120 lines)
- [x] Refactor `pinterest_media.py` to pure data class (141 lines)
- [x] Update all imports across codebase (scraper_api.py, scraper_base.py)
- [x] Run test suite: All 35 tests passing ✅

**Files Changed:**
- NEW: `pinterest_dl/data_model/response_parser.py` (180 lines)
- NEW: `pinterest_dl/data_model/media_file_handler.py` (120 lines)
- MODIFIED: `pinterest_dl/data_model/pinterest_media.py` (244 → 141 lines, -103 lines)
- MODIFIED: `pinterest_dl/scrapers/scraper_api.py` (added ResponseParser import, 4 call sites updated)
- MODIFIED: `pinterest_dl/scrapers/scraper_base.py` (added MediaFileHandler import, 3 method calls updated)

**Success Criteria:**
- ✅ `PinterestMedia` is pure dataclass (141 lines, target <150)
- ✅ All 35 tests pass
- ✅ Zero functionality regression
- ✅ Clean separation: Data model / Response parsing / File operations

**Actual Results:**
- Response parser: 180 lines (includes comprehensive docstrings)
- File handler: 120 lines (static methods for file operations)
- Data model: 141 lines (pure data + serialization only)
- Test suite: 35/35 passing
- No breaking changes to public API

---

#### Task 1.2: Eliminate Fake Inheritance
- [ ] Remove `PinterestDL` inheritance from `_ScraperBase`
- [ ] Convert `_ScraperBase` static methods to module functions
- [ ] Create `scrapers/utils.py` for shared scraper utilities
- [ ] Update `__init__.py` to remove inheritance
- [ ] Remove `_ScraperBase` class entirely
- [ ] Update all scraper imports

**Files Changed:**
- DELETED: `pinterest_dl/scrapers/scraper_base.py` (168 lines)
- NEW: `pinterest_dl/scrapers/utils.py` (module-level functions)
- MODIFIED: `pinterest_dl/__init__.py` (remove inheritance)
- MODIFIED: `pinterest_dl/scrapers/scraper_api.py` (import updates)
- MODIFIED: `pinterest_dl/scrapers/scraper_webdriver.py` (import updates)

**Success Criteria:**
- ✅ Inheritance depth: 2 → 0 levels
- ✅ Static-only classes: 4 → 2 remaining
- ✅ All tests pass

---

### Phase 2: Scraper Decomposition

**Priority: CRITICAL**  
**Estimated Effort:** 3-4 days

#### Task 2.1: Decompose scraper_api.py
- [ ] Extract pin scraping logic to `scrapers/pin_scraper.py` (180 lines)
- [ ] Extract board scraping logic to `scrapers/board_scraper.py` (160 lines)
- [ ] Extract search scraping logic to `scrapers/search_scraper.py` (140 lines)
- [ ] Keep factory + shared logic in `scraper_api.py` (169 lines)
- [ ] Update CLI to use new scraper classes
- [ ] Run full test suite

**Files Changed:**
- NEW: `pinterest_dl/scrapers/pin_scraper.py`
- NEW: `pinterest_dl/scrapers/board_scraper.py`
- NEW: `pinterest_dl/scrapers/search_scraper.py`
- MODIFIED: `pinterest_dl/scrapers/scraper_api.py` (649 → 169 lines)
- MODIFIED: `pinterest_dl/cli.py` (import updates)

**Success Criteria:**
- ✅ No file >300 lines
- ✅ Each scraper type isolated
- ✅ Jump test: <3 files per workflow
- ✅ All tests pass

---

### Phase 3: Simplification

**Priority: HIGH**  
**Estimated Effort:** 1-2 days

#### Task 3.1: Inline Premature Abstractions
- [ ] Inline `_ConcurrentCoordinator` into `PinterestMediaDownloader`
- [ ] Convert `RequestBuilder` class to module functions
- [ ] Simplify `request_builder.py`

**Files Changed:**
- MODIFIED: `pinterest_dl/low_level/http/downloader.py` (-65 lines)
- MODIFIED: `pinterest_dl/low_level/http/request_builder.py` (class → functions)

**Success Criteria:**
- ✅ -65 lines of abstraction removed
- ✅ Linear control flow (no callbacks)
- ✅ All tests pass

---

#### Task 3.2: Fix CLI Duplication
- [ ] Extract `_add_common_arguments()` function
- [ ] Apply to `scrape` and `search` commands
- [ ] Verify both commands work identically

**Files Changed:**
- MODIFIED: `pinterest_dl/cli.py` (-30 lines duplication)

**Success Criteria:**
- ✅ -30 lines duplication
- ✅ Single source of truth for shared args
- ✅ Both commands functional

---

### Phase 4: Explicitness

**Priority: HIGH**  
**Estimated Effort:** 2 days

#### Task 4.1: Add Type Hints
- [ ] Add type hints to `browser.py` (all methods)
- [ ] Add type hints to `io.py` (all functions)
- [ ] Add type hints to `scraper_webdriver.py`
- [ ] Add type hints to `driver_installer.py`
- [ ] Run mypy for validation

**Files Changed:**
- MODIFIED: `pinterest_dl/low_level/webdriver/browser.py`
- MODIFIED: `pinterest_dl/utils/io.py`
- MODIFIED: `pinterest_dl/scrapers/scraper_webdriver.py`
- MODIFIED: `pinterest_dl/low_level/webdriver/driver_installer.py`

**Success Criteria:**
- ✅ 100% type hint coverage on public APIs
- ✅ mypy passes with no errors

---

#### Task 4.2: Extract Magic Numbers
- [ ] Define `PIN_BOOKMARK_HISTORY`, `SEARCH_BOOKMARK_HISTORY` constants
- [ ] Replace all magic numbers with constants
- [ ] Add docstring comments explaining values

**Files Changed:**
- MODIFIED: `pinterest_dl/scrapers/pin_scraper.py` (if split, else scraper_api.py)
- MODIFIED: `pinterest_dl/scrapers/search_scraper.py` (if split)
- MODIFIED: `pinterest_dl/scrapers/board_scraper.py` (if split)

**Success Criteria:**
- ✅ No magic numbers in bookmark initialization
- ✅ Self-documenting constants

---

#### Task 4.3: Fix Implicit Control Flow
- [ ] Split `_get_images()` into `_get_pin_images()` and `_get_board_images()`
- [ ] Split `_get_videos()` similarly
- [ ] Update callers to use explicit methods

**Files Changed:**
- MODIFIED: Scraper files (after Phase 2 split)

**Success Criteria:**
- ✅ No magic optional parameters changing behavior
- ✅ Linear, explicit control flow

---

### Phase 5: Polish

**Priority: MEDIUM**  
**Estimated Effort:** 1-2 days

#### Task 5.1: Fix Error Handling
- [ ] Remove `print()` from `driver_installer.py`
- [ ] Return status objects or use logging at WARNING level only
- [ ] Update callers to handle status

**Files Changed:**
- MODIFIED: `pinterest_dl/low_level/webdriver/driver_installer.py`
- MODIFIED: `pinterest_dl/scrapers/scraper_webdriver.py` (status handling)

---

#### Task 5.2: Clean Up Documentation
- [ ] Add docstrings to all public classes/functions
- [ ] Move tutorial code from `__init__.py` to `examples/` or `README.md`
- [ ] Standardize docstring format (Google style)

---

#### Task 5.3: Flatten Deep Nesting
- [ ] Refactor `from_responses()` parsing (after Phase 1 split)
- [ ] Use early returns and guard clauses
- [ ] Extract validation to named functions

**Target:** Max 2-3 indent levels per function

---

## Testing Strategy

### Test Coverage Requirements

**Before Refactoring:**
- Run full test suite: `pytest tests/ -v`
- Document current pass/fail state
- Current: 35 unit tests ✅

**During Refactoring (Per Phase):**
- Run tests after each major change
- Fix any breaking tests immediately
- Add new tests for extracted modules

**After Refactoring:**
- Full regression test suite
- Integration test with real Pinterest URLs (manual `test.py`)
- CLI smoke tests for all commands

### Test Additions Needed

**Phase 1:**
- [ ] Tests for `ResponseParser.from_responses()`
- [ ] Tests for `MediaFileHandler` file operations

**Phase 2:**
- [ ] Tests for individual scraper classes (`PinScraper`, `BoardScraper`, `SearchScraper`)

**Phase 3-5:**
- [ ] Type checking with mypy
- [ ] Linting with ruff

---

## Architecture Metrics: Before vs After

| Metric                       | Before         | After Target     |
| ---------------------------- | -------------- | ---------------- |
| **Largest file**             | 649 lines      | <300 lines       |
| **Files >300 lines**         | 3 files        | 0 files          |
| **Inheritance depth**        | 2 levels       | 0 levels         |
| **Static-only classes**      | 4 classes      | 0 classes        |
| **Missing type hints**       | ~15% functions | 0% (public APIs) |
| **Print in low-level**       | 3 occurrences  | 0 occurrences    |
| **CLI duplication**          | 30+ lines      | 0 lines          |
| **God classes (>500 lines)** | 1              | 0                |
| **Jump test failures**       | 7 jumps        | <3 jumps         |
| **Code duplication**         | ~100 lines     | <20 lines        |

---

## Estimated Total Effort

| Phase                   | Effort        | Risk                    |
| ----------------------- | ------------- | ----------------------- |
| Phase 1: Foundation     | 2-3 days      | HIGH (touches core)     |
| Phase 2: Decomposition  | 3-4 days      | HIGH (largest refactor) |
| Phase 3: Simplification | 1-2 days      | LOW                     |
| Phase 4: Explicitness   | 2 days        | LOW                     |
| Phase 5: Polish         | 1-2 days      | LOW                     |
| **Total**               | **9-13 days** | -                       |

**Risk Mitigation:**
- Run tests after each phase
- Commit after each successful task
- Keep `main` branch working (use feature branches)
- Manual testing with `test.py` after major changes

---

## Success Criteria

### Code Quality
- ✅ No file exceeds 300 lines
- ✅ No inheritance hierarchies (all flat)
- ✅ No static-only classes
- ✅ 100% type hint coverage on public APIs
- ✅ No print statements in low-level code
- ✅ No code duplication >10 lines

### Architecture Philosophy
- ✅ **Locality:** Related code colocated, <3 file jumps to understand workflows
- ✅ **Simplicity:** No premature abstractions, flat hierarchies, direct implementations
- ✅ **Explicitness:** No magic parameters, full type hints, clear control flow

### Functionality
- ✅ All 35 unit tests pass
- ✅ Manual test script (`test.py`) works
- ✅ CLI commands work identically to before refactoring
- ✅ Zero regression in features

### Documentation
- ✅ All public APIs have docstrings
- ✅ README updated if architecture changes
- ✅ This plan archived as `REFACTORING_COMPLETE.md` when done

---

## Rollback Plan

If refactoring introduces regressions:

1. **Per-Phase Rollback:** Revert to last working commit
2. **Full Rollback:** Revert to commit before Phase 1
3. **Git Tags:** Tag each phase completion for easy rollback points

**Commands:**
```bash
# Tag after each phase
git tag -a phase1-complete -m "Phase 1: Foundation refactoring complete"

# Rollback to phase
git checkout phase1-complete
```

---

## Notes & Considerations

### Why This Order?

**Phase 1 first** because `PinterestMedia` is used everywhere. Splitting it first provides clean foundation for scraper decomposition.

**Phase 2 critical** because god class creates most technical debt. Must be tackled while momentum is high.

**Phase 3-5 incremental** because they're lower risk and can be done in parallel or skipped if time-constrained.

### Incremental vs. Big Bang?

**Decision: Incremental refactoring per phase**

**Rationale:**
- 35 tests provide safety net, but not comprehensive
- Incremental allows testing at each checkpoint
- Can pause between phases if needed
- Lower risk of breaking production

### Breaking Changes?

**Public API:** `PinterestDL.with_api()` and `PinterestDL.with_browser()` remain unchanged.

**Internal APIs:** Significant changes to internal module structure.

**Impact:** No breaking changes for external users. Internal code requires updates (already planned in tasks).

---

## Changelog

### January 30, 2026 - Phase 1, Task 1.1 Complete

**Split PinterestMedia Class ✅**

*What was done:*
- Created `pinterest_dl/data_model/response_parser.py` (180 lines)
  - Extracted `from_responses()` classmethod and all video parsing helpers
  - Added comprehensive docstrings and type hints
  - Handles Pinterest API response → PinterestMedia object conversion
  
- Created `pinterest_dl/data_model/media_file_handler.py` (120 lines)
  - Extracted `set_local_resolution()`, `prune_local()`, `write_exif_comment()`, `write_exif_subject()`
  - All methods are static and accept PinterestMedia as first parameter
  - Clear separation of file I/O concerns from data model
  
- Refactored `pinterest_dl/data_model/pinterest_media.py` (244 → 141 lines, -103 lines)
  - Removed all parsing logic
  - Removed all file operation methods
  - Kept pure data structure + `to_dict()` / `from_dict()` serialization
  - Fixed `to_dict()` to treat `(0, 0)` resolution as `None`
  
- Updated `pinterest_dl/scrapers/scraper_api.py`
  - Added `from pinterest_dl.data_model.response_parser import ResponseParser`
  - Replaced 4 call sites: `PinterestMedia.from_responses()` → `ResponseParser.from_responses()`
  
- Updated `pinterest_dl/scrapers/scraper_base.py`
  - Added `from pinterest_dl.data_model.media_file_handler import MediaFileHandler`
  - Replaced 3 method calls to use `MediaFileHandler` static methods

*Testing:*
- All 35 unit tests passing (pytest tests/ -v)
- Zero regressions
- Public API unchanged

*Benefits achieved:*
- ✅ **Locality:** Related parsing logic colocated in `response_parser.py`
- ✅ **Simplicity:** Each module has one clear responsibility
- ✅ **Explicitness:** Clear module names indicate purpose
- ✅ Jump test: Understanding PinterestMedia data structure = 1 file (was 5 concepts)

*Next steps:*
- Phase 1, Task 1.2: Eliminate fake inheritance hierarchy

---

## Future Considerations (Post-Refactor)

After completing this refactoring:

1. **Add more unit tests** - Target 80%+ coverage
2. **Consider mypy strict mode** - Enable stricter type checking
3. **Add integration tests** - Automated CLI testing
4. **Performance profiling** - Identify bottlenecks after cleanup
5. **Documentation site** - Generate API docs from docstrings

---

## References

- [Engineering Philosophy](.github/copilot-instructions.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Current Test Suite](tests/)
- [TODO List](TODO.md)

---

**Status:** ⏳ PLANNING PHASE  
**Last Updated:** January 30, 2026  
**Owner:** Project Maintainer  
**Reviewer:** TBD
