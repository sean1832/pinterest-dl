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
- ✅ Scrape private boards and pins with browser cookies. ([see pull request](https://github.com/sean1832/pinterest-dl/pull/20))

## 🚩 Known Issues
- 🔲 Incompatibility with Pinterest URLs that include search queries.
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

---
### Examples

**Scraping Images in anonymous mode:**

Scrape images in anonymous mode, without login, to the `./images/art` directory from the Pinterest URL `https://www.pinterest.com/pin/1234567` with a limit of `30` images and a minimum resolution of `512x512`. Save scraped URLs to a `JSON` file.
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" "images/art" -l 30 -r 512x512 --json
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
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" "images/art" -l 30 -c cookies.json
```

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

**Options:**
- `-o`, `--output [file]`: File to save browser cookies for future use. (default: `cookies.json`)
- `--firefox`: Opt for Firefox as the scraping browser.
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
pinterest-dl scrape [url] [output_dir] [options]
```

**Options:**
- `-c`, `--cookies [file]`: File containing browser cookies for private boards/pins. Run `login` command to obtain cookies.
- `-l`, `--limit [number]`: Max number of image to download (default: 100).
- `-r`, `--resolution [width]x[height]`: Minimum image resolution for download (e.g., 512x512).
- `--timeout [second]`: Timeout in seconds for requests (default: 3).
- `--incognito`: Activate incognito mode for scraping.
- `--json`: Save scraped URLs to a JSON file.
- `--dry-run`: Execute scrape without downloading images.
- `--firefox`: Opt for Firefox as the scraping browser.
- `--headful`: Run in headful mode with browser window.
- `--verbose`: Enable detailed output for debugging.

#### 3. Download
Download images from a list of URLs provided in a file.

**Syntax:**
```bash
pinterest-dl download [url_list] [options]
```

**Options:**
- `-o`, `--output [directory]`: Output directory (default: ./<json_filename>).
- `-r`, `--resolution [width]x[height]`: minimum resolution to download (e.g. 512x512).
- `--verbose`: Enable verbose output.


## 🛠️ Python Usage
You can also use the `PinterestDL` class directly in your Python code to scrape and download images programmatically.

### 1. Quick Scrape and Download
The following example shows how to scrape and download images from a Pinterest URL in one step.

```python
from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
images = PinterestDL.with_browser(
    "chrome",  # Browser type to use for scraping (choose "chrome" or "firefox")
    timeout=3,  # Timeout in seconds for each request (default: 3)
    headless=True,  # Run browser in headless mode (default: True)
    incognito=False,  # Enable incognito mode to avoid saving browsing data (default: False)
    verbose=False,  # Enable detailed logging for debugging (default: False)
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest URL to scrape
    output_dir="images/art",  # Directory to save downloaded images
    limit=30,  # Max number of images to download 
    min_resolution=(512, 512),  # Minimum resolution for images (width, height) (default: None)
    json_output="art.json",  # File to save URLs of scraped images (default: None)
    dry_run=False,  # If True, performs a scrape without downloading images (default: False)
    add_captions=True,  # Adds image `alt` text as metadata to images (default: False)
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
from pinterest_dl import PinterestDL

# Initialize and run the Pinterest image downloader with specified settings
images = (
    PinterestDL.with_browser(
        "chrome",  # Browser type to use for scraping (choose "chrome" or "firefox")
    )
    .with_cookies(
        "cookies.json",  # Path to cookies file
        wait_sec=1,  # Time to wait after go to homepage. Default 1 second
    )
    .scrape_and_download(
        url="https://www.pinterest.com/pin/1234567",  # Assume this is a private board URL
        output_dir="images/art",  # Directory to save downloaded images
        limit=30,  # Max number of images to download
    )
)
```

### 3. Detailed Scraping with Lower-Level Control

Use this example if you need more granular control over scraping and downloading images.

```python
from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with browser settings and scrape images
scraped_images = PinterestDL.with_browser("chrome").scrape(
    url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
    limit=30,  # Maximum number of images to scrape
)

# 2. Save Scraped Data to JSON
# Convert scraped data into a dictionary and save it to a JSON file for future access
images_data = [img.to_dict() for img in scraped_images]
PinterestDL.write_json(images_data, "art.json", indent=4)

# 3. Download Images
# Download images to a specified directory
downloaded_imgs = PinterestDL.download_images(images=scraped_images, output_dir="images/art")

# 4. Prune Images by Resolution
# Remove images that do not meet the minimum resolution requirements
min_resolution = (512, 512)
valid_indices = PinterestDL.prune_images(downloaded_imgs, min_resolution)

# 5. Add Alt Text as Metadata
# Extract `alt` text from images and set it as metadata in the downloaded files
PinterestDL.add_captions(images=downloaded_imgs, indices=valid_indices)
```

## 📜 License
[Apache License 2.0](LICENSE)
