# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development
pip install -e ".[dev]"          # pytest + pytest-mock + playwright (needed for browser tests)
pip install -e ".[all]"          # + pillow + pyexiv2 + playwright
pip install -e ".[browser]"      # playwright only (browser scraping + login)

# Run tests (integration tests excluded by default)
pytest tests/
pytest tests/test_pinterest_media.py   # single file
pytest -m integration -v               # hits real Pinterest network

# Run CLI
pinterest-dl scrape "https://pinterest.com/user/board/" output/ -n 30
pin-dl scrape ...                      # alias
```

No linter is configured. Version is sourced from `pinterest_dl/__init__.py.__version__`.

## Architecture

Dual scraping strategy with a factory entry point:

```
PinterestDL (factory, __init__.py)
  .with_api()      -> ApiScraper        (fast, reverse-engineered API)
  .with_browser()  -> PlaywrightScraper (browser automation, Playwright)
```

**Playwright is an optional dependency** (`[browser]` extra). `import pinterest_dl` must never import it. The three `__init__.py` files in `pinterest_dl/`, `scrapers/`, and `webdriver/` expose Playwright classes lazily via PEP 562 `__getattr__`; `with_browser()` and those `__getattr__`s call `common.ensure_playwright.ensure_playwright()` first, which raises `BrowserDependencyError` (with install guidance) when the package is missing. The factory logs and re-raises (library); the CLI pre-checks with `require_playwright_or_exit()` and prints/exits before launching a browser.

Layers (top to bottom):

| Layer | Path | Purpose |
|-------|------|---------|
| CLI | `cli.py` | argparse entry, final exception handler |
| Scrapers | `scrapers/` | orchestrate scrape + download, handle logging |
| Operations | `scrapers/operations.py` | shared module functions (download, captions, pruning) |
| API client | `api/` | reverse-engineered Pinterest API, bookmark pagination |
| Downloader | `download/` | `MediaDownloader` via `ThreadPoolExecutor`, HLS video |
| Storage | `storage/` | write files, caption formats (txt/json/exif) |
| Domain | `domain/` | `PinterestMedia` dataclass, cookies, browser config |
| Parsers | `parsers/response.py` | parse raw Pinterest API JSON |

Legacy `data_model/` re-exports from `domain/` with deprecation warnings (removal in 1.1.0). Use `pinterest_dl.domain.media` imports.

## Key Conventions

**Error handling layering** - the single most important convention:
- Low-level code (`api/`, `download/`, `webdriver/`) raises exceptions, **never logs**.
- Scrapers catch, log with `logging.getLogger(__name__)`, and re-raise or recover.
- CLI is the only final handler; prints user-friendly messages and calls `sys.exit(1)`.

**Logging placement**: never add `import logging` to low-level modules. Log only in `scrapers/` and `cli.py`.

**Imports**: use current 1.0 paths:
```python
from pinterest_dl.domain.media import PinterestMedia   # not data_model
from pinterest_dl.api.api import API                   # not low_level.api
```

**Path handling**: always `pathlib.Path`, never raw strings.

**Progress bars**: use `tqdm` with `disable=verbose` — verbose mode shows log lines instead of a bar.

## Video Download Pipeline

HLS streams -> AES-128 decrypt -> one of three explicit outputs:
- `concat_to_ts()` - no ffmpeg, raw `.ts`
- `remux_to_mp4()` - ffmpeg stream copy (fast); auto-falls back to re-encode on failure
- `reencode_to_mp4()` - ffmpeg re-encode (slow, compatible)

`--skip-remux` flag bypasses ffmpeg entirely (outputs `.ts`). `ffmpeg` must be on `PATH` for MP4 output.

## Common Pitfalls

- **Cookie format**: cookies are stored as a list of dicts with an `expiry` key; Playwright's own format uses `expires` and is converted via `CookieJar.to_playwright()`.
- **Resolution order**: always `(width, height)`, not `(height, width)`.
- **URL trailing slash**: CLI sanitizes URLs via `sanitize_url()`; the API parser expects this.
- **Bookmark manager**: `last` param must be 0-4; manages pagination state across requests.
- **WebDriver cleanup**: call `.quit()` in a `finally` block for browser scrapers.
- **ffmpeg check**: call `ensure_executable("ffmpeg")` before any HLS remux path.
