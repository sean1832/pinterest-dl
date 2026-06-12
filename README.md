# Pinterest Media Downloader (pinterest-dl)
[![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D3.10-blue
)](https://pypi.org/project/pinterest-dl/)
[![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>


**English | [中文](https://github.com/sean1832/pinterest-dl/blob/main/README_CN.md)**

> [!NOTE]
> **Version 1.0 is here!** This release brings improved stability, better error handling, and enhanced testing (56 comprehensive tests). All existing code continues to work without any changes - we've maintained full backward compatibility.

This library facilitates the scraping and downloading of medias (including images and video stream) from [Pinterest](https://pinterest.com). Using reverse engineered Pinterest API and browser automation ([Playwright](https://playwright.dev) by default, with [Selenium](https://selenium.dev) as fallback), it enables users to extract images from a specified Pinterest URL and save them to a chosen directory.

It includes a [CLI](#-cli-usage) for direct usage and a [Python API](#️-python-api) for programmatic access. The tool supports scraping medias from public and private boards and pins using browser cookies. It also allows users to save scraped URLs to a JSON file for future access.

> [!TIP]
> If you are looking for a GUI version of this tool, check out [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui).
> It provides a user-friendly interface for scraping and downloading media from Pinterest using the same underlying library. It could also serve as a reference for integrating the library into your own GUI application.

> [!WARNING] 
> This project is independent and not affiliated with Pinterest. It's designed solely for educational purposes. Please be aware that automating the scraping of websites might conflict with their [Terms of Service](https://developers.pinterest.com/terms/). The repository owner disclaims any liability for misuse of this tool. Use it responsibly and at your own legal risk.

> [!NOTE]
> This project draws inspiration from [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).


# Table of Contents
- [Pinterest Media Downloader (pinterest-dl)](#pinterest-media-downloader-pinterest-dl)
- [Table of Contents](#table-of-contents)
  - [🌟 Features](#-features)
  - [🚩 Known Issues](#-known-issues)
  - [📋 Requirements](#-requirements)
  - [📥 Installation](#-installation)
    - [Using pip (Recommended)](#using-pip-recommended)
    - [Cloning from GitHub](#cloning-from-github)
  - [🚀 Quick Start](#-quick-start)
    - [CLI Usage](#cli-usage)
    - [Python API](#python-api)
  - [📚 Documentation](#-documentation)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)

## 🌟 Features
- ✅ Scrape media directly from a Pinterest URL.
- ✅ Asynchronously download media from a list of URLs. ([#1](https://github.com/sean1832/pinterest-dl/pull/1))
- ✅ Save scraped URLs to a JSON file for future access.
- ✅ Incognito mode to keep your scraping discrete.
- ✅ Access detailed output for effective debugging.
- ✅ Support for the Firefox browser.
- ✅ Insert `alt` text for media as metadata `comment` in the downloaded media for searchability.
- ✅ Optionally save `alt` text as a separate text file for each media. ([#32](https://github.com/sean1832/pinterest-dl/pull/32))
- ✅ Scrape private boards and pins with browser cookies. ([#20](https://github.com/sean1832/pinterest-dl/pull/20))
- ✅ Scrape media using reversed engineered Pinterest API. (This will be default behaviour. You can use webdriver by specifying `--client chrome` or `--client firefox`) ([#21](https://github.com/sean1832/pinterest-dl/pull/21))
- ✅ Search for media on Pinterest using a query. ([#23](https://github.com/sean1832/pinterest-dl/pull/23))
- ✅ Support multiple urls and queries in a single command.
- ✅ Support for batch processing of URLs and queries from files.
- ✅ Download video streams if available.
- ✅ **Playwright support** - faster and more reliable browser automation (default), with Selenium as fallback (`--backend selenium`).

## 🚩 Known Issues
~~- 🔲 Not able to scrape nested boards yet.~~ (Supported since [#69](https://github.com/sean1832/pinterest-dl/pull/69))

## 📋 Requirements
- Python 3.10 or newer
- (Optional) Playwright browsers: `playwright install chromium` or `playwright install firefox`
- (Optional) For Selenium backend: Chrome or Firefox browser with matching WebDriver
- (Optional) [ffmpeg](https://ffmpeg.org/) for video remuxing to MP4 (with `--video` option). If remux fails, automatically falls back to re-encoding. Use `--skip-remux` to download raw .ts files without ffmpeg.
- (Optional) For image resolution detection and pruning, requires `pillow` library. Install with `pip install pinterest-dl[image]`.
- (Optional) For embedding `alt` text as metadata comment, requires `pyexiv2` library. Install with `pip install pinterest-dl[exif]`.

## 📥 Installation

### Using pip (Recommended)

**Basic installation** (core functionality only):
```bash
pip install pinterest-dl
```

**With optional dependencies**:
```bash
# With image operations (resolution detection, pruning)
pip install pinterest-dl[image]

# With EXIF metadata support (embed alt text as metadata)
pip install pinterest-dl[exif]

# With all image/metadata features
pip install pinterest-dl[metadata]

# For development (includes testing tools)
pip install pinterest-dl[dev,all]
```

> [!NOTE]
> **Optional Dependencies:**
> - `image` - Installs Pillow for image resolution detection and pruning features
> - `exif` - Installs pyexiv2 for EXIF metadata embedding (alt text as metadata comment)
> - `metadata` - Installs both Pillow and pyexiv2
> - `all` - Installs all optional dependencies (Currently Pillow and pyexiv2)
> - `dev` - Installs testing tools (pytest, pytest-mock)
>
> Without optional dependencies, you can still scrape and download images, but features requiring image analysis (resolution detection, metadata embedding) will raise an informative error.

### Cloning from GitHub
```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .
# Or with optional dependencies
pip install .[all]
```

## 🚀 Quick Start

### CLI Usage

Scrape images from Pinterest using the command line:

```bash
# Scrape a board, section, or the requested pin itself
pinterest-dl scrape <url> -o output_folder -n 50

# Download exactly one pin
pinterest-dl one <pin_url> -o output_folder

# Download pins related to a pin
pinterest-dl related <pin_url> -o output_folder -n 50

# Download videos as MP4 (requires ffmpeg)
pinterest-dl scrape <pin_url> --video -o output_folder

# Download videos as raw .ts files (no ffmpeg needed)
pinterest-dl scrape <pin_url> --video --skip-remux -o output_folder

# Search for images
pinterest-dl search "nature photography" -o output_folder -n 30

# Login to access private boards
pinterest-dl login -o cookies.json
```

**📖 [View Full CLI Documentation ->](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI.md)**

Available commands: `login`, `scrape`, `related`, `one`, `search`, `download`

---

### Python API

Use PinterestDL programmatically in your Python code:

```python
from pinterest_dl import PinterestDL

# Quick scrape and download
images = PinterestDL.with_api().scrape_and_download(
    url="https://www.pinterest.com/username/board-name/",
    output_dir="images/art",
    num=30
)

# Download the requested pin itself
pin = PinterestDL.with_api().scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",
    output_dir="images/pin",
    num=1
)

# Search for images
images = PinterestDL.with_api().search_and_download(
    query="landscape art",
    output_dir="images/landscapes",
    num=50
)
```

**📖 [View Full API Documentation ->](https://github.com/sean1832/pinterest-dl/blob/main/doc/API.md)**

Includes: High-level API, private board access, advanced scraping patterns

**💡 [See Complete Examples ->](https://github.com/sean1832/pinterest-dl/blob/main/examples/)**

Working examples covering:
- Basic scraping and downloading
- Search functionality  
- Cookie authentication for private boards
- Video downloading
- Advanced control with lower-level API
- Debug mode and troubleshooting

---

## 📚 Documentation

- **[CLI Guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI.md)** - Complete command-line interface documentation
- **[Python API Guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/API.md)** - Programmatic usage examples and patterns
- **[Contributing Guidelines](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md)** - How to contribute to the project

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md) for:
- Code of Conduct
- Commit message guidelines (semantic commits)
- Pull request process

## 📜 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE) file for details.

---

Made with ❤️ by [sean1832](https://github.com/sean1832)

**Note:** This project is not affiliated with Pinterest. All trademarks are property of their respective owners.
