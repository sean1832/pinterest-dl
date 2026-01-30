# Pinterest-DL Examples

This directory contains comprehensive examples demonstrating various use cases of the Pinterest-DL library.

## Available Examples

### 1. `basic_scraping.py`
**Basic scraping and downloading functionality**

Examples included:
- Simple pin scraping
- Board scraping
- Resolution filtering
- Caption handling (txt, json, metadata)
- Caching scraped data
- Video stream downloading
- Verbose logging mode

**Quick start:**
```bash
python examples/basic_scraping.py
```

---

### 2. `search_functionality.py`
**Search Pinterest and download results**

Examples included:
- Basic search queries
- Search with filters (resolution, captions)
- Multiple programmatic searches
- Search result caching
- Search with video downloads
- Ensuring alt text availability

**Quick start:**
```bash
python examples/search_functionality.py
```

---

### 3. `authentication_cookies.py`
**Cookie-based authentication for private boards**

Examples included:
- Login and save cookies (Playwright)
- Load cookies from file
- Use cookies path directly
- Authenticated search
- Selenium login (legacy)

**Quick start:**
```bash
python examples/authentication_cookies.py
```

**Prerequisites:**
- Set `PINTEREST_PASSWORD` environment variable
- Or input credentials when prompted

---

### 4. `advanced_control.py`
**Lower-level API for granular control**

Examples included:
- Separate scrape and download steps
- Save metadata to JSON
- Add captions as image metadata
- Add captions as txt/json files
- Prune images by resolution
- Search with separate steps
- Browser mode scraping (Playwright)

**Quick start:**
```bash
python examples/advanced_control.py
```

---

### 5. `video_downloading.py`
**Video stream downloading and processing**

Examples included:
- Basic video downloads
- Videos with captions
- Video search
- Videos with JSON metadata
- Separate video scrape/download
- Video caching
- Resolution filtering for images
- Verbose mode for HLS debugging

**Quick start:**
```bash
python examples/video_downloading.py
```

**Prerequisites:**
- `ffmpeg` must be installed and available in PATH

---

### 6. `debug_mode_example.py`
**Debug mode for API inspection**

Examples included:
- Basic debug mode
- Custom debug directory
- Debug with cookies
- Error debugging
- Search debugging
- Manual debug utilities

**Quick start:**
```bash
python examples/debug_mode_example.py
```

---

## Running Examples

### Run Individual Examples

```bash
# Run a specific example
python examples/basic_scraping.py
python examples/search_functionality.py
python examples/video_downloading.py
```

### Modify for Your Use Case

**Important:** All examples use placeholder URLs. You MUST change these constants at the top of each file to real Pinterest URLs before running:

```python
# At the top of each example file, change:
PIN_URL = "https://www.pinterest.com/pin/12345678/"  # <- Change to your actual Pinterest URL
BOARD_URL = "https://www.pinterest.com/username/board-name/"  # <- Change to your actual board URL
SEARCH_QUERY = "your search term"  # <- Change to your search query
```

Example:
```python
# Change from:
PIN_URL = "https://www.pinterest.com/pin/12345678/"

# To a real URL:
PIN_URL = "https://www.pinterest.com/pin/900438519273272242/"
```

### Comment Out Unused Examples

Each example file runs multiple sub-examples. Comment out the ones you don't need:

```python
if __name__ == "__main__":
    # Run only the examples you need
    example_1_basic_search()
    # example_2_search_with_filters()  # <- commented out
    # example_3_multiple_searches()    # <- commented out
```

---

## Common Parameters

Most examples use these common parameters:

| Parameter          | Type  | Description                             | Default             |
| ------------------ | ----- | --------------------------------------- | ------------------- |
| `url`              | str   | Pinterest URL to scrape                 | Required            |
| `output_dir`       | str   | Directory to save files                 | Required            |
| `num`              | int   | Max items to download                   | Required            |
| `query`            | str   | Search query                            | Required for search |
| `download_streams` | bool  | Download videos                         | `False`             |
| `min_resolution`   | tuple | Min (width, height)                     | `None`              |
| `caption`          | str   | Caption format (txt/json/metadata/none) | `None`              |
| `cache_path`       | str   | Path to save JSON cache                 | `None`              |
| `delay`            | float | Delay between requests (seconds)        | `0.2`               |
| `verbose`          | bool  | Enable detailed logging                 | `False`             |
| `timeout`          | int   | Request timeout (seconds)               | `3`                 |
| `ensure_alt`       | bool  | Skip items without alt text             | `False`             |

---

## Example Workflows

### Workflow 1: Quick Download
```python
from pinterest_dl import PinterestDL

# One-liner to download 20 images
images = PinterestDL.with_api().scrape_and_download(
    url="YOUR_URL",
    output_dir="downloads",
    num=20
)
```

### Workflow 2: Download with Captions
```python
images = PinterestDL.with_api().scrape_and_download(
    url="YOUR_URL",
    output_dir="downloads",
    num=20,
    caption="txt"  # Adds .txt files with alt text
)
```

### Workflow 3: Search and Download High-Res
```python
images = PinterestDL.with_api().search_and_download(
    query="your search query",
    output_dir="downloads",
    num=30,
    min_resolution=(1024, 1024)
)
```

### Workflow 4: Private Board with Cookies
```python
# Step 1: Login and save cookies (run once)
cookies = PinterestDL.with_browser().login(email, password).get_cookies()

# Step 2: Use cookies for scraping
images = (
    PinterestDL.with_api()
    .with_cookies(cookies)
    .scrape_and_download(url="PRIVATE_URL", output_dir="downloads", num=20)
)
```

### Workflow 5: Videos with Metadata
```python
items = PinterestDL.with_api().scrape_and_download(
    url="YOUR_URL",
    output_dir="downloads",
    num=20,
    download_streams=True,  # Download videos
    caption="json",         # Save metadata as JSON
)
```

---

## Tips

1. **Start Small**: Test with `num=5` before downloading hundreds of images
2. **Use Verbose Mode**: Add `verbose=True` when debugging issues
3. **Cache Results**: Use `cache_path` to save metadata for reuse
4. **Respect Rate Limits**: Use `delay=0.5` or higher to avoid rate limiting
5. **Check Requirements**: Video downloads require `ffmpeg` installed
6. **Use Cookies**: Required for private boards and may improve reliability

---

## Troubleshooting

### ffmpeg not found
```bash
# Windows (using Chocolatey)
choco install ffmpeg

# Windows (using Scoop)
scoop install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### Rate limiting errors
- Increase `delay` parameter (e.g., `delay=0.5`)
- Reduce `num` to download fewer items
- Use cookies for authentication

### Browser automation issues
- Set `headless=False` to see what's happening
- Try different `browser_type` ('chromium' or 'firefox')
- Ensure browser drivers are installed (auto-downloads on first run)

---

## Need Help?

- Check the [main documentation](../README.md)
- See [API documentation](../doc/API.md)
- See [CLI documentation](../doc/CLI.md)
- Report issues on GitHub

---

## Contributing

Found a useful pattern? Consider contributing an example! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
