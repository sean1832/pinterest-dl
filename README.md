# Pinterest Image Downloader
![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)
![Static Badge](https://img.shields.io/badge/python-3.10%2B-yellow)
![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)



This CLI (Command Line Interface) tool facilitates the scraping and downloading of images from [Pinterest](https://pinterest.com). Using [Selenium](https://selenium.dev) for automation, it enables users to extract images from a specified Pinterest URL and save them to a chosen directory.

> **⚠️ Disclaimer:**  
> This project is independent and not affiliated with Pinterest. It's designed solely for educational purposes. Please be aware that automating the scraping of websites might conflict with their [Terms of Service](https://developers.pinterest.com/terms/). The repository owner disclaims any liability for misuse of this tool. Use it responsibly and at your own legal risk.

> **🗒️ Note:**  
> This project draws inspiration from [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).

## 🌟 Features
- ✅ Scrape images directly from a Pinterest URL.
- ✅ Asynchronously download images from a list of URLs. ([see pull request](https://github.com/sean1832/pinterest-dl/pull/1))
- ✅ Configure the output directory to your liking.
- ✅ Save scraped URLs to a JSON file for easy access.
- ✅ Utilize incognito mode to keep your scraping discreet.
- ✅ Access detailed output for effective debugging.
- ✅ Perform dry-runs to receive URLs without downloading the images.
- ✅ Full support for the Firefox browser.
- ✅ Customize scroll threshold and page persistence for tailored scraping.

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

### Commands

#### 1. Scrape
Extract images from a specified Pinterest URL.

**Syntax:**
```bash
pinterest-dl scrape [url] [options]
```

**Options:**
- `-o`, `--output [directory]`: Set the directory to save images (default: `imgs`).
- `-w`, `--write [file]`: Save scraped URLs to a JSON file.
- `-t`, `--threshold [number]`: Set the number of page scrolls (default: 20).
- `-p`, `--persistence [seconds]`: Wait time for page loading (default: 120 seconds).
- `-r`, `--resolution [width]x[height]`: Minimum image resolution for download (e.g., 512x512).
- `--incognito`: Activate incognito mode for scraping.
- `--dry-run`: Execute scrape without downloading images.
- `--firefox`: Opt for Firefox as the scraping browser.
- `--verbose`: Enable detailed output for debugging.

#### 2. Download
Download images from a list of URLs provided in a file.

**Syntax:**
```bash
pinterest-dl download [url_list] [options]
```

**Options:**
- `-o`, `--output [directory]`: Specify the output directory for the images (default: `imgs`).
- `-r`, `--resolution [width]x[height]`: minimum resolution to download (e.g. 512x512).
- `--verbose`: Enable verbose output.

### Examples

**Scraping Images:**
```bash
pinterest-dl scrape "https://www.pinterest.com/exampleBoard" -o myimages -t 30 --verbose
```

**Downloading Images:**
```bash
pinterest-dl download urls.json -o downloaded_imgs --verbose
```

## 📜 License
[Apache License 2.0](LICENSE)
