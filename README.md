# Pinterest Image Downloader (pinterest-dl)
[![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

This library facilitates the scraping and downloading of images from [Pinterest](https://pinterest.com). Using [Selenium](https://selenium.dev) and reverse engineered Pinterest API for automation, it enables users to extract images from a specified Pinterest URL and save them to a chosen directory.

It includes a [CLI](#-cli-usage) for direct usage and a [Python API](#️-python-api) for programmatic access. The tool supports scraping images from public and private boards and pins using browser cookies. It also allows users to save scraped URLs to a JSON file for future access.

> [!TIP]
> If you are looking for a GUI version of this tool, check out [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui).
> It provides a user-friendly interface for scraping and downloading images from Pinterest using the same underlying library. It could also serve as a reference for integrating the library into your own GUI application.

> [!WARNING] 
> This project is independent and not affiliated with Pinterest. It's designed solely for educational purposes. Please be aware that automating the scraping of websites might conflict with their [Terms of Service](https://developers.pinterest.com/terms/). The repository owner disclaims any liability for misuse of this tool. Use it responsibly and at your own legal risk.

> [!NOTE]
> This project draws inspiration from [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).


# Table of Contents
- [Pinterest Image Downloader (pinterest-dl)](#pinterest-image-downloader-pinterest-dl)
- [Table of Contents](#table-of-contents)
  - [🌟 Features](#-features)
  - [🚩 Known Issues](#-known-issues)
  - [📋 Requirements](#-requirements)
  - [📥 Installation](#-installation)
    - [Using pip (Recommended)](#using-pip-recommended)
    - [Cloning from GitHub](#cloning-from-github)
  - [🚀 CLI-Usage](#-cli-usage)
    - [General Command Structure](#general-command-structure)
    - [Examples](#examples)
    - [Commands](#commands)
      - [1. Login](#1-login)
      - [2. Scrape](#2-scrape)
      - [3. Search](#3-search)
      - [4. Download](#4-download)
  - [🛠️ Python API](#️-python-api)
    - [1. Quick Scrape and Download](#1-quick-scrape-and-download)
    - [2. Scrape with Cookies for Private Boards](#2-scrape-with-cookies-for-private-boards)
    - [3. Detailed Scraping with Lower-Level Control](#3-detailed-scraping-with-lower-level-control)
      - [3a. With API](#3a-with-api)
        - [Scrape Images](#scrape-images)
        - [Search Images](#search-images)
      - [3b. With Browser](#3b-with-browser)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)

## 🌟 Features
- ✅ Scrape images directly from a Pinterest URL.
- ✅ Asynchronously download images from a list of URLs. ([#1](https://github.com/sean1832/pinterest-dl/pull/1))
- ✅ Save scraped URLs to a JSON file for future access.
- ✅ Incognito mode to keep your scraping discrete.
- ✅ Access detailed output for effective debugging.
- ✅ Support for the Firefox browser.
- ✅ Insert `alt` text for images as metadata `comment` in the downloaded image for searchability.
- ✅ Scrape private boards and pins with browser cookies. ([#20](https://github.com/sean1832/pinterest-dl/pull/20))
- ✅ Scrape images using reversed engineered Pinterest API. (This will be default behaviour. You can use webdriver by specifying `--client chrome` or `--client firefox`) ([#21](https://github.com/sean1832/pinterest-dl/pull/21))
- ✅ Search for images on Pinterest using a query. ([#23](https://github.com/sean1832/pinterest-dl/pull/23))

## 🚩 Known Issues
- 🔲 Not yet implement testing.
- 🔲 Not sorely tested on Linux and Mac. Please create an [Issue](https://github.com/sean1832/pinterest-dl/issues) to report any bugs.

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
### Examples

**Scraping Images in anonymous mode:**

Scrape images in anonymous mode, without login, to the `./images/art` directory from the Pinterest URL `https://www.pinterest.com/pin/1234567` with a num of `30` images and a minimum resolution of `512x512`. Save scraped URLs to a `JSON` file.
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" -o "images/art" -n 30 -r 512x512 --cache art.json
```

**Get Browser Cookies:**

Get browser cookies for Pinterest login and save them to the `cookies.json` file in headful mode (with browser window).
```bash
pinterest-dl login -o cookies.json --headful
```
> [!TIP]
> You will be prompted to enter your Pinterest email and password. The tool will save the browser cookies to the specified file for future use.

**Scraping Private Boards:**

Scrape images from a private Pinterest board using the cookies saved in the `cookies.json` file.
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" "images/art" -n 30 -c cookies.json
```

> [!TIP]
> You can use the `--client` option to use `chrome` or `firefox` Webdriver for scraping. This is slower but more reliable.
> It will open a browser in headless mode to scrape images. You can also use the `--headful` flag to run the browser in windowed mode.

**Downloading Images:**

Download images from the `art.json` file to the `./downloaded_imgs` directory with a minimum resolution of `1024x1024`.
```bash
pinterest-dl download art.json -o downloaded_imgs -r 1024x1024
```
---
### Commands

#### 1. Login
Login to Pinterest using your credentials to obtain browser cookies for scraping private boards and pins.

**Syntax:**
```bash
pinterest-dl login [options]
```

![login](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-login.gif)

**Options:**
- `-o`, `--output [file]`: File to save browser cookies for future use. (default: `cookies.json`)
- `--client`: Choose the scraping client (`chrome` / `firefox`). (default: `chrome`)
- `--headful`: Run in headful mode with browser window.
- `--verbose`: Enable detailed output for debugging.
- `--incognito`: Activate incognito mode for scraping.

> [!TIP]
> After entering `login` command, you will be prompted to enter your Pinterest email and password.
> The tool will then save the browser cookies to the specified file for future use. (if not specified, it will save to `./cookies.json`)

#### 2. Scrape
Extract images from a specified Pinterest URL.

**Syntax:**
```bash
pinterest-dl scrape [url] [options]
```

![scrape](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-scrape.gif)

**Options:**

- `-o`, `--output [directory]`: Output directory for downloaded images. Print to console if not specified.
- `-c`, `--cookies [file]`: File containing browser cookies for private boards/pins. Run `login` command to obtain cookies.
- `-n`, `--num [number]`: Max number of image to download (default: 100).
- `-r`, `--resolution [width]x[height]`: Minimum image resolution for download (e.g., 512x512).
- `--timeout [second]`: Timeout in seconds for requests (default: 3).
- `--delay [second]`: Delay between requests (default: 0.2).
- `--cache [path]`: Save scraped URLs to a JSON file.
- `--caption [format]`: Caption format for downloaded images: `txt` for alt text in separate text files, `json` for full image data in seperate json file, `metadata` embeds in image files, `none` for no captions. (default: `none`)
- `--verbose`: Enable detailed output for debugging.
- `--client`: Choose the scraping client (`api` / `chrome` / `firefox`). (default: api)
- `--incognito`: Activate incognito mode for scraping. (*chrome / firefox only*)
- `--headful`: Run in headful mode with browser window. (*chrome / firefox only*)

#### 3. Search
Search for images on Pinterest using a query. (*Currently only available in API mode*)

**Syntax:**
```bash
pinterest-dl search [query] [options]
```

![search](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-search.gif)

**Options:**
- `-o`, `--output [directory]`: Output directory for downloaded images. Print to console if not specified.
- `-c`, `--cookies [file]`: File containing browser cookies for private boards/pins. Run `login` command to obtain cookies.
- `-n`, `--num [number]`: Max number of image to download (default: 100).
- `-r`, `--resolution [width]x[height]`: Minimum image resolution for download (e.g., 512x512).
- `--timeout [second]`: Timeout in seconds for requests (default: 3).
- `--delay [second]`: Delay between requests (default: 0.2).
- `--cache [path]`: Save scraped URLs to a JSON file.
- `--caption [format]`: Caption format for downloaded images: `txt` for alt text in separate text files, `json` for full image data in seperate json file, `metadata` embeds in image files, `none` for no captions. (default: `none`)
- `--verbose`: Enable detailed output for debugging.

#### 4. Download
Download images from cache file (JSON) to a specified directory.

**Syntax:**
```bash
pinterest-dl download [cache] [options]
```

![download](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-download.gif)

**Options:**
- `-o`, `--output [directory]`: Output directory (default: ./<json_filename>).
- `-r`, `--resolution [width]x[height]`: minimum resolution to download (e.g. 512x512).
- `--verbose`: Enable verbose output.


## 🛠️ Python API
You can also use the `PinterestDL` class directly in your Python code to scrape and download images programmatically.

### 1. Quick Scrape and Download
This example shows how to **scrape** and download images from a Pinterest URL in one step.

```python
from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
images = PinterestDL.with_api(
    timeout=3,  # Timeout in seconds for each request (default: 3)
    verbose=False,  # Enable detailed logging for debugging (default: False)
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest URL to scrape
    output_dir="images/art",  # Directory to save downloaded images
    num=30,  # Max number of images to download 
    min_resolution=(512, 512),  # Minimum resolution for images (width, height) (default: None)
    cache_path="art.json",  #  Path to cache scraped data as json (default: None)
    caption="txt",  # Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' for no captions
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
).search_and_download(
    query="art",  # Pinterest search query
    output_dir="images/art",  # Directory to save downloaded images
    num=30,  # Max number of images to download 
    min_resolution=(512, 512),  # Minimum resolution for images (width, height) (default: None)
    cache_path="art.json",  #  Path to cache scraped data as json (default: None)
    caption="txt",  # Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' for no captions
)
```

### 2. Scrape with Cookies for Private Boards
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

### 3. Detailed Scraping with Lower-Level Control

Use this example if you need more granular control over scraping and downloading images.

#### 3a. With API

##### Scrape Images
```python
import json

from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API.
scraped_images = PinterestDL.with_api().scrape(
    url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
    num=30,  # Maximum number of images to scrape
    min_resolution=(512, 512),  # <- Only available to set in the API. Browser mode will have to pruned after download.
)

# 2. Save Scraped Data to JSON
# Convert scraped data into a dictionary and save it to a JSON file for future access
images_data = [img.to_dict() for img in scraped_images]
with open("art.json", "w") as f:
    json.dump(images_data, f, indent=4)

# 3. Download Images
# Download images to a specified directory
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(images=scraped_images, output_dir=output_dir)

valid_indices = list(range(len(downloaded_imgs)))  # All images are valid to add captions

# 4. Add Alt Text as Metadata (Optional)
# Extract `alt` text from images and set it as metadata in the downloaded files
PinterestDL.add_captions_to_meta(images=downloaded_imgs, indices=valid_indices)

# 4. Add Alt Text as text file (Optional)
# Extract `alt` text from images and save it as a text file in the downloaded directory
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, extension="txt")
```

##### Search Images
```python
import json
from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API.
scraped_images = PinterestDL.with_api().search(
    query="art",  # Search query for Pinterest
    num=30,  # Maximum number of images to scrape
    min_resolution=(512, 512),  # Minimum resolution for images
    delay=0.4, # Delay between requests (default: 0.2)
)
# ... (Same as above)
```

#### 3b. With Browser
```python
import json

from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with API.
scraped_images = PinterestDL.with_browser(
    browser_type="chrome",  # Browser type to use ('chrome' or 'firefox')
    headless=True,  # Run browser in headless mode
).scrape(
    url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
    num=30,  # Maximum number of images to scrape
)

# 2. Save Scraped Data to JSON
# Convert scraped data into a dictionary and save it to a JSON file for future access
images_data = [img.to_dict() for img in scraped_images]
with open("art.json", "w") as f:
    json.dump(images_data, f, indent=4)

# 3. Download Images
# Download images to a specified directory
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(images=scraped_images, output_dir=output_dir)

# 4. Prune Images by Resolution (Optional)
# Remove images that do not meet the minimum resolution criteria
valid_indices = PinterestDL.prune_images(images=downloaded_imgs, min_resolution=(200, 200))

# 5. Add Alt Text as Metadata (Optional)
# Extract `alt` text from images and set it as metadata in the downloaded files
PinterestDL.add_captions_to_meta(images=downloaded_imgs, indices=valid_indices)

# 6. Add Alt Text as text file (Optional)
# Extract `alt` text from images and save it as a text file in the downloaded directory
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, extension="txt")
```

## 🤝 Contributing
Contributions are welcome! Please check the [Contribution Guidelines](CONTRIBUTING.md) before submitting a pull request.

## 📜 License
[Apache License 2.0](LICENSE)
