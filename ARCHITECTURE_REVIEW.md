# Pinterest-DL 2.0 Architecture Review

**Date:** January 30, 2026  
**Status:** Proposal  
**Purpose:** Evaluate current structure and propose optimized architecture for 2.0

---

## Current Structure Analysis

### Directory Layout

```
pinterest_dl/
├── __init__.py              # Factory: PinterestDL
├── cli.py                   # CLI entry (311 lines)
├── exceptions.py            # Exception hierarchy ✅
├── data_model/              # ❓ Mixed concerns
│   ├── pinterest_media.py   # Domain model (141 lines) ✅
│   ├── response_parser.py   # API parsing (180 lines) ❌ Not "data model"
│   ├── media_file_handler.py # File I/O (120 lines) ❌ Not "data model"
│   ├── cookie.py            # Cookie utilities ✅
│   └── browser_version.py   # Browser version class ✅
├── scrapers/                # High-level scrapers
│   ├── scraper_api.py       # _ScraperAPI (650 lines) ⚠️ Still too large
│   ├── scraper_webdriver.py # _ScraperWebdriver (213 lines) ✅
│   └── utils.py             # Shared functions (221 lines) ✅
├── low_level/               # ❌ Vague name
│   ├── api/                 # Pinterest API client
│   ├── http/                # HTTP & download
│   ├── hls/                 # Video processing
│   └── webdriver/           # Selenium
└── utils/                   # ⚠️ Conflicts with scrapers/utils.py
    ├── io.py
    ├── progress_bar.py
    └── ensure_executable.py
```

---

## Issues Identified

### 1. ❌ CRITICAL: Naming Inconsistencies

#### Problem: Leading Underscores on Public Classes
```python
# __init__.py exports these as public API
class _ScraperAPI:         # ❌ Leading _ means "private" but it's public
class _ScraperWebdriver:   # ❌ Same issue
```

**Why it's wrong:**
- Leading underscore convention in Python means "internal implementation"
- These are explicitly exported in `__init__.py`
- Users directly import and use these classes
- Confusing: `from pinterest_dl import PinterestDL; PinterestDL.with_api()` returns `_ScraperAPI`

**Should be:**
```python
class ApiScraper:          # ✅ Clear, public
class WebDriverScraper:    # ✅ Clear, public
# Or
class PinterestApiScraper
class PinterestWebDriverScraper
```

#### Problem: Inconsistent Module Naming
- `scraper_api.py` - pattern: `{type}_{noun}`
- `pinterest_api.py` - pattern: `{platform}_{noun}`
- `http_client.py` - pattern: `{protocol}_{noun}`
- `media_file_handler.py` - pattern: `{domain}_{domain}_{noun}`

**Should be:** Consistent pattern, preferably `{noun}` or `{adjective}_{noun}`

#### Problem: Redundant Prefixes
```python
PinterestMedia          # ✅ Good
PinterestAPI            # ⚠️ Redundant - we're already in pinterest_dl package
PinterestDriver         # ⚠️ Redundant
PinterestMediaDownloader # ⚠️ Double redundant
PinterestCookieJar      # ⚠️ Redundant
```

**Better:**
```python
Media                   # ✅ Context is clear from import
ApiClient               # ✅ pinterest_dl.api.ApiClient
Driver                  # ✅ pinterest_dl.webdriver.Driver
MediaDownloader         # ✅ Clear without redundancy
CookieJar              # ✅ Or just use requests' CookieJar
```

---

### 2. ❌ CRITICAL: Misnamed Folders

#### `data_model/` Contains Non-Models
- `response_parser.py` - This is **parsing logic**, not a data model
- `media_file_handler.py` - This is **file I/O**, not a data model

**What belongs in data_model:**
- `PinterestMedia` ✅
- `VideoStreamInfo` ✅
- `Cookie` (if it's a domain concept) ✅
- `BrowserVersion` (if it's domain data) ✅

**What doesn't:**
- API response parsing
- File system operations
- HTTP requests

#### `low_level/` is Meaningless
"Low level" tells you nothing about what's inside. Better names:
- `core/` - Core infrastructure
- `infrastructure/` - Infrastructure layer (DDD terminology)
- `adapters/` - External adapters (Clean Architecture)
- Or flatten: `api/`, `http/`, `hls/`, `webdriver/` at top level

---

### 3. ⚠️ MEDIUM: Namespace Pollution

#### Two `utils` Modules
```
pinterest_dl/utils/          # General utilities
pinterest_dl/scrapers/utils.py  # Scraper utilities
```

**Problem:** Confusing imports
```python
from pinterest_dl.utils import io          # General
from pinterest_dl.scrapers import utils    # Scrapers
```

**Better:** Single `common/` or specific names
```
pinterest_dl/common/         # Shared utilities
pinterest_dl/scrapers/shared.py  # OR rename to 'operations', 'workflows'
```

---

### 4. ⚠️ MEDIUM: File Too Large

`scraper_api.py` still **650 lines** (goal: <300)

**Contains:**
- Cookie management (38-84)
- Pin scraping (86-126)
- Download orchestration (128-210)
- Search scraping (212-280)
- Image deduplication (282-340)
- Progress bar management (342-420)
- Board scraping (425-485)
- Helpers (500-650)

**Should be split** (Phase 2 task already planned)

---

### 5. ⚠️ MEDIUM: Static-Only Classes

Classes with only `@staticmethod` should be modules:

```python
class RequestBuilder:      # ❌ Static only
    @staticmethod
    def build_post(...):
        ...

class MediaFileHandler:    # ❌ Static only
    @staticmethod
    def save(...):
        ...
```

**Better:** Module-level functions
```python
# request_builder.py
def build_post(...):
    ...

# media_storage.py  
def save_media(...):
    ...
```

---

### 6. ✅ GOOD: What's Working Well

- Exception hierarchy is excellent
- Clear separation after Phase 1 refactoring
- `scrapers/utils.py` as module functions (not class)
- Type hints in newer code
- Flat scrapers/ structure
- HLS module separation (`hls_processor.py`, `key_cache.py`, `segment_info.py`)

---

## Proposed 2.0 Architecture

### High-Level Design Principles

1. **Domain-Driven Organization** - Group by business concern, not technical layer
2. **Explicit Over Implicit** - Clear names, no "utils" or "low_level"
3. **Flat When Possible** - Avoid deep nesting
4. **Consistent Naming** - One pattern for all modules
5. **No Redundant Prefixes** - Package context makes prefixes unnecessary

### Proposed Structure

```
pinterest_dl/
├── __init__.py              # Public API: PinterestDL factory
├── cli.py                   # CLI entry point
├── exceptions.py            # All exceptions
│
├── domain/                  # ✨ Core domain models
│   ├── media.py            # Media, VideoStreamInfo
│   ├── cookies.py          # Cookie handling
│   └── browser.py          # BrowserVersion
│
├── scrapers/                # ✨ Scraping orchestration (high-level)
│   ├── api.py              # ApiScraper (rename from _ScraperAPI)
│   ├── webdriver.py        # WebDriverScraper (rename from _ScraperWebdriver)
│   └── operations.py       # Shared operations (rename from utils.py)
│
├── parsers/                 # ✨ Data transformation
│   └── response.py         # ResponseParser (moved from data_model)
│
├── storage/                 # ✨ File system operations
│   └── media.py            # MediaStorage (rename from media_file_handler)
│
├── api/                     # ✨ Pinterest API client (moved from low_level)
│   ├── client.py           # ApiClient (rename from pinterest_api)
│   ├── endpoints.py        # Endpoint definitions
│   ├── bookmarks.py        # BookmarkManager
│   └── responses.py        # PinResponse
│
├── download/                # ✨ Download infrastructure (from low_level/http + hls)
│   ├── http.py             # HttpClient
│   ├── media.py            # MediaDownloader (rename from downloader)
│   ├── requests.py         # Request building (rename from request_builder)
│   └── video/              # Video-specific
│       ├── hls.py          # HlsProcessor
│       ├── segments.py     # SegmentInfo
│       └── keys.py         # KeyCache
│
├── webdriver/               # ✨ Selenium automation (moved from low_level)
│   ├── driver.py           # Driver (rename from pinterest_driver)
│   ├── browser.py          # Browser initialization
│   └── installer.py        # ChromeDriverInstaller
│
└── common/                  # ✨ Cross-cutting utilities (rename from utils)
    ├── io.py               # File I/O utilities
    ├── progress.py         # TqdmProgressBarCallback
    └── executables.py      # Executable checks
```

---

## Detailed Refactoring Plan

### Phase 2: Module Organization & Naming (NEW)

**Priority: CRITICAL** (before continuing with Phase 2 Task 2.1)  
**Estimated Effort:** 1-2 days  
**Risk:** HIGH (touches many files, but mechanical changes)

#### Task 2.0.1: Rename Public Scraper Classes

- [ ] Rename `_ScraperAPI` → `ApiScraper`
- [ ] Rename `_ScraperWebdriver` → `WebDriverScraper`
- [ ] Update `__init__.py` exports
- [ ] Update all import sites (CLI, tests)
- [ ] Update documentation references

**Files Changed:**
- `scrapers/scraper_api.py` → `scrapers/api_scraper.py`
- `scrapers/scraper_webdriver.py` → `scrapers/webdriver_scraper.py`
- `scrapers/__init__.py`
- `__init__.py`
- `cli.py`
- All tests

**Success Criteria:**
- ✅ No leading underscores on public classes
- ✅ Clear class names in public API
- ✅ All tests passing

---

#### Task 2.0.2: Flatten and Reorganize Directories

**Phase A: Flatten `low_level/`**

Move subdirectories to top level:
```
low_level/api/ → api/
low_level/http/ → download/
low_level/hls/ → download/video/
low_level/webdriver/ → webdriver/
```

**Phase B: Reorganize `data_model/`**

Split by actual concern:
```
data_model/pinterest_media.py → domain/media.py
data_model/response_parser.py → parsers/response.py
data_model/media_file_handler.py → storage/media.py
data_model/cookie.py → domain/cookies.py
data_model/browser_version.py → domain/browser.py
```

**Phase C: Consolidate `utils/`**

```
utils/ → common/
scrapers/utils.py → scrapers/operations.py
```

**Files Changed:**
- 30+ files (all imports need updating)
- Directory structure completely reorganized

**Success Criteria:**
- ✅ No `low_level/` directory
- ✅ Clear top-level organization
- ✅ No namespace conflicts
- ✅ All imports updated
- ✅ All tests passing

---

#### Task 2.0.3: Remove Redundant Prefixes

Rename classes to remove `Pinterest` prefix where context is clear:

```python
# api/client.py
class PinterestAPI → class ApiClient

# webdriver/driver.py
class PinterestDriver → class Driver

# download/media.py
class PinterestMediaDownloader → class MediaDownloader

# domain/cookies.py
class PinterestCookieJar → class CookieJar (or remove entirely, use requests')

# domain/media.py
class PinterestMedia → class Media  # ⚠️ BREAKING CHANGE
```

**Note:** `PinterestMedia → Media` is a **breaking change** for external users.

**Options:**
1. **Keep `PinterestMedia`** for backward compatibility (recommended for 2.0)
2. Make breaking change and bump to 3.0
3. Deprecate with warning, remove in 3.0

**Recommendation:** Keep `PinterestMedia` but rename internal classes.

**Files Changed:**
- `api/client.py`
- `webdriver/driver.py`
- `download/media.py`
- `domain/cookies.py`
- All import sites

**Success Criteria:**
- ✅ No redundant `Pinterest` prefixes on internal classes
- ✅ `PinterestMedia` kept for public API compatibility
- ✅ All tests passing

---

#### Task 2.0.4: Convert Static Classes to Modules

Remove unnecessary class wrappers:

```python
# Before: request_builder.py
class RequestBuilder:
    @staticmethod
    def build_post(...):
        ...

# After: requests.py (renamed)
def build_post_request(...):
    ...
```

**Classes to convert:**
- `RequestBuilder` → module functions in `download/requests.py`
- `MediaFileHandler` → module functions in `storage/media.py` (already done)

**Files Changed:**
- `download/requests.py` (rename from request_builder.py)
- `storage/media.py` (already module functions)
- All call sites

**Success Criteria:**
- ✅ No static-only classes (target: 0)
- ✅ Clear module-level functions
- ✅ All tests passing

---

### Phase 2 (Updated): Scraper Decomposition

*Continue with original Phase 2 after Phase 2.0 completes*

**Task 2.1:** Split `api_scraper.py` (650 lines → 3 files <200 lines each)

---

## Migration Strategy

### Incremental Approach (Recommended)

**Week 1:**
- Day 1-2: Task 2.0.1 (Rename scraper classes)
- Day 3-4: Task 2.0.2 Phase A (Flatten `low_level/`)
- Day 5: Test & commit

**Week 2:**
- Day 1-2: Task 2.0.2 Phase B (Reorganize `data_model/`)
- Day 3: Task 2.0.2 Phase C (Consolidate `utils/`)
- Day 4: Task 2.0.3 (Remove prefixes)
- Day 5: Task 2.0.4 (Convert static classes)

**Week 3:**
- Continue with original Phase 2 (scraper decomposition)

### Big Bang Approach (Faster but Riskier)

Do all Task 2.0.* in one large commit:
- **Pros:** Faster, atomic change
- **Cons:** Hard to review, risky if something breaks
- **Risk Mitigation:** Extensive testing, can revert entire commit

---

## Breaking Changes Assessment

### Public API Impact

**Currently Exposed:**
```python
from pinterest_dl import PinterestDL
from pinterest_dl.data_model.pinterest_media import PinterestMedia
from pinterest_dl.exceptions import *
```

**After Refactoring:**
```python
from pinterest_dl import PinterestDL       # ✅ Same
from pinterest_dl.domain.media import PinterestMedia  # ⚠️ Import path changed
from pinterest_dl.exceptions import *      # ✅ Same
```

**Mitigation Options:**

1. **Maintain backward compatibility aliases:**
```python
# pinterest_dl/data_model/__init__.py (keep empty dir)
from pinterest_dl.domain.media import PinterestMedia  # Re-export
```

2. **Update `__init__.py` to export from new locations:**
```python
# pinterest_dl/__init__.py
from pinterest_dl.domain.media import PinterestMedia
__all__ = ['PinterestDL', 'PinterestMedia']
```

3. **Document migration path in README**

**Recommendation:** Option 2 (re-export from `__init__.py`) + deprecation warnings

---

## Comparison: Before vs After

### Directory Count
- **Before:** 7 top-level items (cli, data_model, scrapers, low_level, utils, exceptions, __init__)
- **After:** 10 top-level items (cli, domain, scrapers, parsers, storage, api, download, webdriver, common, exceptions, __init__)

**Why more is better:** Each directory has **clear, single purpose**

### Import Depth
```python
# Before
from pinterest_dl.low_level.api.pinterest_api import PinterestAPI
from pinterest_dl.data_model.media_file_handler import MediaFileHandler

# After
from pinterest_dl.api.client import ApiClient
from pinterest_dl.storage.media import save_media
```

**Improvement:** Clearer path, shorter imports

### Class Naming
```python
# Before
_ScraperAPI                  # ❌ Leading underscore but public
PinterestMediaDownloader     # ❌ Redundant prefix
RequestBuilder               # ❌ Static-only class

# After
ApiScraper                   # ✅ Clear public name
MediaDownloader              # ✅ No redundancy
build_post_request()         # ✅ Module function
```

---

## Decision: Should We Do This?

### Arguments FOR (Recommended ✅)

1. **This is 2.0** - Perfect time for breaking changes
2. **Current structure has debt** - Will only get worse
3. **Early in 2.0 development** - Less user impact now vs later
4. **Incremental approach** - Can do step by step with testing
5. **Future maintainability** - Clear structure easier to extend
6. **Industry standards** - Follows DDD/Clean Architecture patterns

### Arguments AGAINST

1. **Risk** - Large refactoring could introduce bugs
2. **Time** - 1-2 weeks of work
3. **Testing** - Need comprehensive tests (we only have 35 unit tests)
4. **Documentation** - All docs need updating

### Recommendation

**✅ YES, do the refactoring** with these conditions:

1. **Do Phase 2.0 BEFORE Phase 2** (scrapers decomposition)
2. **Incremental commits** - One task at a time
3. **Maintain public API compatibility** via `__init__.py` re-exports
4. **Add more tests** as we go (integration tests for scrapers)
5. **Update docs** after each phase

**Priority Order:**
1. Phase 2.0.1: Rename scraper classes (LOW RISK)
2. Phase 2.0.2: Reorganize directories (MEDIUM RISK)
3. Phase 2.0.3: Remove prefixes (LOW RISK)
4. Phase 2.0.4: Convert static classes (LOW RISK)
5. Phase 2.1+: Continue with scraper decomposition

---

## Questions for You

1. **Breaking changes:** Are you OK with changing import paths? (can mitigate with re-exports)
2. **PinterestMedia rename:** Keep as-is or rename to `Media`? (recommend keep for compatibility)
3. **Timeline:** Incremental (slower, safer) or big bang (faster, riskier)?
4. **Priorities:** Do all of Phase 2.0 or just critical parts (2.0.1 and 2.0.2)?

Let me know your preferences and I'll proceed with the refactoring!
