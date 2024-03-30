# Pinterest Image Scraper CLI

This CLI tool allows for the scraping and downloading of images from Pinterest. Using Selenium for automation, it provides functionality to scrape images from a given Pinterest URL and download them to a specified directory. 

> **⚠️Disclaimer:**
>This project is not affiliated with Pinterest. It is intended for educational purposes only. Automating the scraping of websites may violate their [terms of service](https://developers.pinterest.com/terms/). Repo owner is not responsible for any misuse of this tool. Use at your own legal risk.

> **🗒️Note:**
> This project is inspired by [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).

### Features
- [x] Scrape images from a Pinterest URL.
- [x] Download images from a list of URLs.
- [x] Customizable output directory.
- [x] Write scraped URLs to a JSON file.
- [x] Incognito mode for scraping.
- [x] Verbose output for debugging.
- [x] Dry-run mode for outputting URLs without downloading images.
- [x] Support for Firefox browser.
- [x] Customizable scroll threshold and page persistence.

### Known Issues
- [ ] Firefox browser support is experimental and may not work as expected.
- [ ] May not work with Pinterest URLs that require login.
- [ ] May not work with Pinterest URLs with search queries.
- [ ] Does not support MacOS and Linux.


## Requirements
- Python 3.10+
- Chrome or Firefox browser

## Installation

### Using pip (recommended)
```bash
pip install pinterest-cli
```

### Using git
```bash
git clone https://github.com/sean1832/pinterest-cli.git
cd pinterest-cli
pip install .
```

## Usage

### General Command Structure
```bash
pinterest-cli [command] [options]
```

### Commands

#### 1. Scrape
Scrape images from a specified Pinterest URL.

**Syntax:**
```bash
pinterest-cli scrape [url] [options]
```

**Options:**
- `-o`, `--output [directory]`: Specify the output directory for the images (default: `imgs`).
- `-w`, `--write [file]`: Write scraped URLs to a JSON file.
- `-t`, `--threshold [number]`: Number of scrolls to perform on the page (default: 20).
- `-p`, `--persistence [seconds]`: Time to wait for the page to load (default: 120 seconds).
- `--incognito`: Enable incognito mode.
- `--dry-run`: Run the scrape without downloading images.
- `--firefox`: Use the Firefox browser for scraping.
- `--verbose`: Enable verbose output.

#### 2. Download
Download images from a list of URLs specified in a file.

**Syntax:**
```bash
python scraper.py download [url_list] [options]
```

**Options:**
- `-o`, `--output [directory]`: Specify the output directory for the images (default: `imgs`).
- `--verbose`: Enable verbose output.

### Examples

**Scraping Images:**
```bash
python scraper.py scrape "https://www.pinterest.com/exampleBoard" -o myimages -t 30 --verbose
```

**Downloading Images:**
```bash
python scraper.py download urls.json -o downloaded_imgs --verbose
```

## License
[Apache License 2.0](LICENSE)


