# Optional Dependencies Guide

Starting from version 1.0.x, `pillow` and `pyexiv2` have been moved to optional dependencies to reduce installation size and allow users to install only what they need.

## Quick Reference

| Feature | Required Package | Install Command |
|---------|-----------------|-----------------|
| Core scraping & download (API client) | None (built-in) | `pip install pinterest-dl` |
| Browser automation (`--client chromium/firefox`, `login`) | `playwright` | `pip install pinterest-dl[browser]` |
| Image resolution detection | `pillow` | `pip install pinterest-dl[image]` |
| Image pruning (`min_resolution`) | `pillow` | `pip install pinterest-dl[image]` |
| EXIF metadata embedding | `pillow` + `pyexiv2` | `pip install pinterest-dl[metadata]` |
| All optional features | All of the above | `pip install pinterest-dl[all]` |

## Installation Options

### Basic Installation
Core functionality only - scraping and downloading without image analysis:
```bash
pip install pinterest-dl
```

### With Browser Automation
Enables the `--client chromium/firefox` scrapers and the interactive `login` command via Playwright:
```bash
pip install pinterest-dl[browser]
playwright install chromium   # download the browser binaries (or: firefox)
```
The default API client does not need this. To reuse cookies from a browser you already have, run `pinterest-dl login --from-browser` (Firefox) instead, which needs no Playwright.

### With Image Operations
Enables resolution detection and pruning features (Pillow):
```bash
pip install pinterest-dl[image]
```

### With EXIF Metadata Support
Enables embedding alt text as EXIF metadata in image files. Adds `pyexiv2` and includes the image operations above:
```bash
pip install pinterest-dl[metadata]
```

### With All Optional Features
Installs the browser, image, and metadata extras together:
```bash
pip install pinterest-dl[all]
```

### For Development
Includes all optional features plus testing tools (pytest, pytest-mock), so the full test suite runs without skips:
```bash
pip install pinterest-dl[dev]
```

## What Works Without Optional Dependencies?

✅ **Available without optional dependencies:**
- Scraping URLs (boards, pins)
- Searching for images
- Downloading images and videos
- Saving captions as separate text files (`caption="txt"`)
- Saving full metadata as JSON (`caption="json"`)
- Cookie-based authentication for private boards
- All CLI commands (except features requiring optional deps)

❌ **Requires optional dependencies:**
- Resolution detection (`set_local_resolution()`)
- Image pruning with `min_resolution` parameter (requires `pillow`)
- EXIF metadata embedding with `caption="metadata"` (requires `pyexiv2`)

## Error Messages

If you try to use a feature that requires an optional dependency without installing it, you'll see a clear error message:

```python
# Without pillow installed
images = scraper.scrape_and_download(
    url="...",
    min_resolution=(512, 512)  # Triggers pillow import
)
# ImportError: Pillow is required for image operations. Install it with: pip install pillow
```

```python
# Without pyexiv2 installed
from pinterest_dl.storage.media import write_exif_comment

write_exif_comment(media, "My caption")
# ImportError: pyexiv2 is required for EXIF operations. Install it with: pip install pyexiv2
```

## Performance Benefits

The optional dependency system uses **lazy loading** with module-level caching:

1. **First call**: Import is checked once and result is cached
2. **Subsequent calls**: Use cached module reference (near-zero overhead)
3. **Never used**: No import overhead if features aren't used

This design ensures:
- Zero performance impact in hotpaths (batch image processing)
- Fast startup time if optional features aren't needed
- Minimal installation size for core use cases

## Migration Guide

### For Existing Users

If you're upgrading from an earlier version where `pillow` and `pyexiv2` were required:

**Option 1: Install all features (recommended for most users)**
```bash
pip install --upgrade pinterest-dl[all]
```

**Option 2: Install only what you need**
```bash
# Check if you use these features:
# - min_resolution parameter
# - caption="metadata"

# If you use min_resolution:
pip install --upgrade pinterest-dl[image]

# If you use caption="metadata" (includes image operations):
pip install --upgrade pinterest-dl[metadata]

# If you use neither:
pip install --upgrade pinterest-dl
```

### For Package Maintainers

If you're packaging pinterest-dl for a distribution:

```python
# requirements.txt or setup.py
pinterest-dl[all]  # Include all optional features

# Or specify explicitly:
pinterest-dl
pillow>=10.4.0
pyexiv2
```

## Technical Details

### Lazy Import Implementation

The lazy import system is implemented in `pinterest_dl/storage/media.py`:

```python
# Module-level cache (checked only once per process)
_PIL: Optional[Any] = None
_PIL_available: Optional[bool] = None

def _get_PIL() -> Any:
    """Lazy import PIL, caching the result."""
    global _PIL, _PIL_available
    
    if _PIL_available is None:
        try:
            from PIL import Image
            _PIL = Image
            _PIL_available = True
        except ImportError:
            _PIL_available = False
    
    if not _PIL_available:
        raise ImportError(
            "Pillow is required for image operations. "
            "Install it with: pip install pillow"
        )
    
    return _PIL
```

Benefits:
- Import checked **once** per Python process
- Zero overhead in hotpaths (e.g., processing 1000s of images)
- Clear error messages if dependency missing
- Type-checker friendly with `TYPE_CHECKING` block

### Package Configuration

Optional dependencies are defined in `pyproject.toml`:

```toml
[project.optional-dependencies]
browser = ["playwright>=1.40.0"]
image = ["pillow==12.2.0"]
metadata = ["pinterest-dl[image]", "pyexiv2"]
all = ["pinterest-dl[browser,metadata]"]
dev = ["pinterest-dl[all]", "pytest>=9.0.3", "pytest-mock>=3.15.1"]
```

## FAQ

**Q: Why make these dependencies optional?**  
A: To reduce installation size and allow users to install only what they need. If you only need basic scraping without image analysis, you don't need pillow or pyexiv2.

**Q: Will my existing code break?**  
A: No, if you have pillow/pyexiv2 installed. Just run `pip install --upgrade pinterest-dl[all]` to ensure all optional dependencies are installed.

**Q: What if I forget which features need which dependencies?**  
A: The error messages will tell you exactly what to install. For example: "Pillow is required for image operations. Install it with: pip install pillow"

**Q: Does this affect performance?**  
A: No, lazy loading with caching ensures zero performance impact. The import check happens only once per process.

**Q: Can I install the dependencies separately?**  
A: Yes! You can install `pillow` and `pyexiv2` directly:
```bash
pip install pinterest-dl
pip install pillow pyexiv2
```

**Q: Which installation should I use?**  
A: 
- Most users: `pip install pinterest-dl[all]` (safest, includes everything)
- Minimal install: `pip install pinterest-dl` (if you don't need image analysis)
- Custom: Choose `[browser]`, `[image]`, or `[metadata]` based on your needs

## See Also

- [README.md](../README.md) - Installation instructions
- [API.md](API.md) - Python API documentation with optional dependency notes
- [CLI.md](CLI.md) - Command-line interface documentation