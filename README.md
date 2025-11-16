# Pinterest Media Downloader (pinterest-dl)
[![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D3.10-blue
)](https://pypi.org/project/pinterest-dl/)
[![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>


**English | [中文](README_CN.md)**


This library facilitates the scraping and downloading of medias (including images and video stream) from [Pinterest](https://pinterest.com). Using reverse engineered Pinterest API and [Selenium](https://selenium.dev) for automation, it enables users to extract images from a specified Pinterest URL and save them to a chosen directory.

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
  - [🚀 CLI-Usage](#-cli-usage)
    - [General Command Structure](#general-command-structure)
    - [Commands](#commands)
      - [1. Login](#1-login)
      - [2. Scrape](#2-scrape)
      - [3. Search](#3-search)
      - [4. Download](#4-download)
  - [🛠️ Python API](#️-python-api)
    - [1. High-level Scrape and Download](#1-high-level-scrape-and-download)
      - [1a. Scrape with Cookies for Private Boards](#1a-scrape-with-cookies-for-private-boards)
    - [2. Detailed Scraping with Lower-Level Control](#2-detailed-scraping-with-lower-level-control)
      - [2a. With API](#2a-with-api)
        - [Scrape Media](#scrape-media)
        - [Search Media](#search-media)
      - [2b. With Browser](#2b-with-browser)
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

## 🚩 Known Issues
- 🔲 Not able to scrape nested boards yet.

## 📋 Requirements
- Python 3.10 or newer
- (Optional) Chrome or Firefox browser
- [ffmpeg](https://ffmpeg.org/) added to your PATH for video stream downloading (with `--video` option)

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

## 🚀 CLI-Usage

### General Command Structure
```bash
pinterest-dl [command] [options]
```

| Command                   | Description                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------- |
| [`login`](#1-login)       | Login to Pinterest to obtain browser cookies for scraping private boards and pins. |
| [`scrape`](#2-scrape)     | Scrape images from a Pinterest URL.                                                |
| [`search`](#3-search)     | Search for images on Pinterest using a query.                                      |
| [`download`](#4-download) | Download images from a list of URLs provided in a JSON file.                       |


---

### Commands

#### 1. Login  
Authenticate to Pinterest and save browser cookies for private boards/pins.

```bash
pinterest-dl login [options]
```

![login](doc/images/pinterest-dl-login.gif)

| Options                     | Description               | Default        |
| --------------------------- | ------------------------- | -------------- |
| `-o`, `--output [file]`     | Path to save cookies file | `cookies.json` |
| `--client [chrome/firefox]` | Browser client to use     | `chrome`       |
| `--headful`                 | Show browser window       | -              |
| `--incognito`               | Use incognito mode        | -              |
| `--verbose`                 | Enable debug output       | -              |

> [!TIP]
>  After running `login`, you’ll be prompted for your Pinterest email/password. Cookies are then saved to the specified file.


---

#### 2. Scrape  
Download images from a Pin, Board URL, or a list of URLs.

```bash
# Single or multiple URLs:
pinterest-dl scrape <url1> <url2> …

# From one or more files (one URL per line):
pinterest-dl scrape -f urls.txt [options]
pinterest-dl scrape -f urls1.txt -f urls2.txt [options]

# From stdin:
cat urls.txt | pinterest-dl scrape -f - [options]
```
![scrape](doc/images/pinterest-dl-scrape.gif)

| Options                              | Description                                              | Default        |
| ------------------------------------ | -------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                | Path to file with URLs (one per line); use `-` for stdin | –              |
| `<url>`                              | One or more Pinterest URLs                               | –              |
| `-o`, `--output [directory]`         | Directory to save images (stdout if omitted)             | –              |
| `-c`, `--cookies [file]`             | Path to cookies file (for private content)               | `cookies.json` |
| `-n`, `--num [number]`               | Maximum images to download                               | `100`          |
| `-r`, `--resolution [WxH]`           | Minimum image resolution (e.g. `512x512`)                | –              |
| `--video`                            | Download video stream (if available)                     | –              |
| `--timeout [seconds]`                | Request timeout                                          | `3`            |
| `--delay [seconds]`                  | Delay between requests                                   | `0.2`          |
| `--cache [path]`                     | Save scraped URLs to JSON                                | –              |
| `--caption [txt/json/metadata/none]` | Caption format: `txt`, `json`, `metadata`, or `none`     | `none`         |
| `--ensure-cap`                       | Require alt text on every image                          | –              |
| `--client [api/chrome/firefox]`      | Scraper backend                                          | `api`          |
| `--headful`                          | Show browser window (chrome/firefox only)                | –              |
| `--incognito`                        | Use incognito mode (chrome/firefox only)                 | –              |
| `--verbose`                          | Enable debug output                                      | –              |

---

#### 3. Search  
Find and download images via a search query (API mode only), or from URL-lists in files.

```bash
# Simple query:
pinterest-dl search <query1> <query2> ... [options]

# From one or more files:
pinterest-dl search -f queries.txt [options]
pinterest-dl search -f q1.txt -f q2.txt [options]

# From stdin:
cat queries.txt | pinterest-dl search -f - [options]
```

![search](doc/images/pinterest-dl-search.gif)

| Options                              | Description                                                 | Default        |
| ------------------------------------ | ----------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                | Path to file with queries (one per line); use `-` for stdin | –              |
| `<query>`                            | One or more search terms                                    | –              |
| `-o`, `--output [directory]`         | Directory to save images (stdout if omitted)                | –              |
| `-c`, `--cookies [file]`             | Path to cookies file                                        | `cookies.json` |
| `-n`, `--num [number]`               | Maximum images to download                                  | `100`          |
| `-r`, `--resolution [WxH]`           | Minimum image resolution                                    | –              |
| `--video`                            | Download video stream (if available)                        | –              |
| `--timeout [seconds]`                | Request timeout                                             | `3`            |
| `--delay [seconds]`                  | Delay between requests                                      | `0.2`          |
| `--cache [path]`                     | Save results to JSON                                        | –              |
| `--caption [txt/json/metadata/none]` | Caption format                                              | `none`         |
| `--ensure-cap`                       | Require alt text on every image                             | –              |
| `--verbose`                          | Enable debug output                                         | –              |

---

#### 4. Download  
Fetch images from a previously saved cache file.

```bash
pinterest-dl download <cache.json> [options]
```
![download](doc/images/pinterest-dl-download.gif)

| Options                    | Description              | Default             |
| -------------------------- | ------------------------ | ------------------- |
| `-o`, `--output [dir]`     | Directory to save images | `./<json_filename>` |
| `-r`, `--resolution [WxH]` | Minimum image resolution | -                   |
| `--verbose`                | Enable debug output      | -                   |


## 🛠️ Python API
You can also use the `PinterestDL` class directly in your Python code to scrape and download images programmatically.

### 1. High-level Scrape and Download
This example shows how to **scrape** and download images from a Pinterest URL in one step.

```python
from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
images = PinterestDL.with_api(
    timeout=3,  # Timeout in seconds for each request (default: 3)
    verbose=False,  # Enable detailed logging for debugging (default: False)
    ensure_alt=True,  # Ensure every image has alt text (default: False)
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest URL to scrape
    output_dir="images/art",  # Directory to save downloaded images
    num=30,  # Max number of images to download 
    download_streams=True,  # Download video streams if available (default: False)
    min_resolution=(512, 512),  # Minimum resolution for images (width, height) (default: None)
    cache_path="art.json",  #  Path to cache scraped data as json (default: None)
    caption="txt",  # Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' for no captions
    delay=0.4,  # Delay between requests (default: 0.2)
)
```

This example shows how to **search** with query and download images from a Pinterest URL in one step.

```python
from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
# `search_and_download` is only available in API mode
images = PinterestDL.with_api( 
    timeout=3,  # Timeout in seconds for each request (default: 3)
    verbose=False,  # Enable detailed logging for debugging (default: False)
    ensure_alt=True,  # Ensure every image has alt text (default: False)
).search_and_download(
    query="art",  # Pinterest search query
    output_dir="images/art",  # Directory to save downloaded images
    num=30,  # Max number of images to download 
    download_streams=True,  # Download video stream if available (default: False)
    min_resolution=(512, 512),  # Minimum resolution for images (width, height) (default: None)
    cache_path="art.json",  #  Path to cache scraped data as json (default: None)
    caption="txt",  # Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' for no captions
    delay=0.4,  # Delay between requests (default: 0.2)
)
```

#### 1a. Scrape with Cookies for Private Boards
**2a. Obtain cookies**
You need to first log in to Pinterest to obtain browser cookies for scraping private boards and pins.
```python
import os
import json

from pinterest_dl import PinterestDL

# Make sure you don't expose your password in the code.
email = input("Enter Pinterest email: ")
password = os.getenv("PINTEREST_PASSWORD")

# Initialize browser and login to Pinterest
cookies = PinterestDL.with_browser(
    browser_type="chrome",
    headless=True,
).login(email, password).get_cookies(
    after_sec=7,  # Time to wait before capturing cookies. Login may take time.
)

# Save cookies to a file
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=4)
```

**2b. Scrape with cookies**
After obtaining cookies, you can use them to scrape private boards and pins.
```python
import json
from pinterest_dl import PinterestDL

# Load cookies from a file
with open("cookies.json", "r") as f:
    cookies = json.load(f)

# Initialize and run the Pinterest image downloader with specified settings
images = (
    PinterestDL.with_api()
    .with_cookies(
        cookies,  # cookies in selenium format
    )
    .scrape_and_download(
        url="https://www.pinterest.com/pin/1234567",  # Assume this is a private board URL
        output_dir="images/art",  # Directory to save downloaded images
        num=30,  # Max number of images to download
    )
)
```

### 2. Detailed Scraping with Lower-Level Control

Use this example if you need more granular control over scraping and downloading images.

#### 2a. With API

##### Scrape Media
```python
import json

from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API and scrape media
scraped_medias = PinterestDL.with_api().scrape(
    url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
    num=30,  # Maximum number of images to scrape
    min_resolution=(512, 512),  # <- Only available to set in the API. Browser mode will have to pruned after download.
)

# 2. Download Media
# Download media to a specified directory
output_dir = "images/art"
downloaded_items = PinterestDL.download_media(
    media=scraped_medias, 
    output_dir=output_dir, 
    download_streams=True # Download video streams if available; otherwise download images only.
)


# 3. Save Scraped Data to JSON (Optional)
# Convert scraped data into a dictionary and save it to a JSON file for future access
media_data = [media.to_dict() for media in scraped_medias]
with open("art.json", "w") as f:
    json.dump(media_data, f, indent=4)

# 4. Add Alt Text as Metadata (Optional)
# Extract `alt` text from media and set it as metadata in the downloaded files
PinterestDL.add_captions_to_meta(images=downloaded_items)

# 4. Add Alt Text as text file (Optional)
# Extract `alt` text from media and save it as a text file in the downloaded directory
PinterestDL.add_captions_to_file(downloaded_items, output_dir, extension="txt")
```

##### Search Media
```python
import json
from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API.
scraped_medias = PinterestDL.with_api().search(
    query="art",  # Search query for Pinterest
    num=30,  # Maximum number of images to scrape
    min_resolution=(512, 512),  # Minimum resolution for images
    delay=0.4, # Delay between requests (default: 0.2)
)
# ... (Same as above)
```

#### 2b. With Browser
```python
import json

from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API.
scraped_medias = PinterestDL.with_browser(
    browser_type="chrome",  # Browser type to use ('chrome' or 'firefox')
    headless=True,  # Run browser in headless mode
    ensure_alt=True,  # Ensure every image has alt text (default: False)
).scrape(
    url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
    num=30,  # Maximum number of images to scrape
)

# 2. Save Scraped Data to JSON
# Convert scraped data into a dictionary and save it to a JSON file for future access
media_data = [media.to_dict() for media in scraped_medias]
with open("art.json", "w") as f:
    json.dump(media_data, f, indent=4)

# 3. Download Media
# Download media to a specified directory
output_dir = "images/art"
downloaded_media = PinterestDL.download_media(
    media=scraped_medias,
    output_dir=output_dir,
    download_streams=False,  # <- browser mode does not support video streams yet
)

# 4. Prune Media by Resolution (Optional)
# Remove media that do not meet the minimum resolution criteria
kept_media = PinterestDL.prune_images(images=downloaded_media, min_resolution=(200, 200))

# 5. Add Alt Text as Metadata (Optional)
# Extract `alt` text from media and set it as metadata in the downloaded files
PinterestDL.add_captions_to_meta(images=kept_media)

# 6. Add Alt Text as text file (Optional)
# Extract `alt` text from media and save it as a text file in the downloaded directory
PinterestDL.add_captions_to_file(kept_media, output_dir, extension="txt")
```

## 🤝 Contributing
Contributions are welcome! Please check the [Contribution Guidelines](CONTRIBUTING.md) before submitting a pull request.

## 📜 License
[Apache License 2.0](LICENSE)
