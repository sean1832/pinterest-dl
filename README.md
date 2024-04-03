# Pinterest Image Downloader CLI (pinterest-dl)
[![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)


This CLI (Command Line Interface) tool facilitates the scraping and downloading of images from [Pinterest](https://pinterest.com). Using [Selenium](https://selenium.dev) for automation, it enables users to extract images from a specified Pinterest URL and save them to a chosen directory.

> **⚠️ Disclaimer:**  
> This project is independent and not affiliated with Pinterest. It's designed solely for educational purposes. Please be aware that automating the scraping of websites might conflict with their [Terms of Service](https://developers.pinterest.com/terms/). The repository owner disclaims any liability for misuse of this tool. Use it responsibly and at your own legal risk.

> **🗒️ Note:**  
> This project draws inspiration from [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).

## 🌟 Features
- ✅ Scrape images directly from a Pinterest URL.
- ✅ Asynchronously download images from a list of URLs. ([see pull request](https://github.com/sean1832/pinterest-dl/pull/1))
- ✅ Save scraped URLs to a JSON file for future access.
- ✅ Incognito mode to keep your scraping discreet.
- ✅ Access detailed output for effective debugging.
- ✅ Support for the Firefox browser.
- ✅ Insert `alt` text for images as metadata `comment` in the downloaded image for searchability.

## 🚩 Known Issues
- 🔲 Experimental Firefox browser support might not perform as expected.
- 🔲 Limited functionality with Pinterest URLs requiring login.
- 🔲 Incompatibility with Pinterest URLs that include search queries.
- 🔲 Currently does not support MacOS and Linux platforms.

## 📋 Requirements
- Python 3.10 or newer
- Chrome or Firefox browser

## 📥 Installation

### Using pip (Recommended)
```bash
pip install pinterest-dl
```

### Cloning from GitHub
```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .
```

## 🛠 Usage

### General Command Structure
```bash
pinterest-dl [command] [options]
```

---
### Examples

**Scraping Images:**

Scrape images to the `./images/art` directory from the Pinterest URL `https://www.pinterest.com/pin/1234567` with a limit of `30` images and a minimum resolution of `512x512`. Save scraped URLs to a `JSON` file.
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" "images/art" -l 30 -r 512x512 --json
```

**Downloading Images:**

Download images from the `art.json` file to the `./downloaded_imgs` directory with a minimum resolution of `1024x1024`.
```bash
pinterest-dl download art.json -o downloaded_imgs -r 1024x1024
```
---
### Commands

#### 1. Scrape
Extract images from a specified Pinterest URL.

**Syntax:**
```bash
pinterest-dl scrape [url] [output_dir] [options]
```

**Options:**
- `-l`, `--limit [number]`: Max number of image to download (default: 100).
- `-r`, `--resolution [width]x[height]`: Minimum image resolution for download (e.g., 512x512).
- `-p`, `--persistence [number]`: Retry count if page does not load new content (default: 120 time).
- `--incognito`: Activate incognito mode for scraping.
- `--json`: Save scraped URLs to a JSON file.
- `--dry-run`: Execute scrape without downloading images.
- `--firefox`: Opt for Firefox as the scraping browser.
- `--headful`: Run in headful mode with browser window.
- `--verbose`: Enable detailed output for debugging.

#### 2. Download
Download images from a list of URLs provided in a file.

**Syntax:**
```bash
pinterest-dl download [url_list] [options]
```

**Options:**
- `-o`, `--output [directory]`: Output directory (default: ./<json_filename>).
- `-r`, `--resolution [width]x[height]`: minimum resolution to download (e.g. 512x512).
- `--verbose`: Enable verbose output.



## 📜 License
[Apache License 2.0](LICENSE)
