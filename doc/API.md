# Python API Guide

You can use the `PinterestDL` class directly in your Python code to scrape and download images programmatically.

## Table of Contents
- [1. High-level Scrape and Download](#1-high-level-scrape-and-download)
  - [1a. Scrape with Cookies for Private Boards](#1a-scrape-with-cookies-for-private-boards)
- [2. Detailed Scraping with Lower-Level Control](#2-detailed-scraping-with-lower-level-control)
  - [2a. With API](#2a-with-api)
  - [2b. With Browser (Playwright)](#2b-with-browser-playwright)
  - [2c. With Browser (Selenium - Legacy)](#2c-with-browser-selenium---legacy)

---

> **Note:** Browser automation now uses **Playwright** by default, which is faster and more reliable. Selenium is still available as a fallback via `PinterestDL.with_selenium()` for backward compatibility.

## 1. High-level Scrape and Download

### Scrape from URL

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

### Search and Download

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

### 1a. Scrape with Cookies for Private Boards

**Step 1: Obtain cookies**

You need to first log in to Pinterest to obtain browser cookies for scraping private boards and pins.

```python
import os
import json

from pinterest_dl import PinterestDL

# Make sure you don't expose your password in the code.
email = input("Enter Pinterest email: ")
password = os.getenv("PINTEREST_PASSWORD")

# Initialize browser and login to Pinterest (uses Playwright by default)
cookies = PinterestDL.with_browser(
    browser_type="chromium",  # 'chromium' or 'firefox'
    headless=True,
).login(email, password).get_cookies(
    after_sec=7,  # Time to wait before capturing cookies. Login may take time.
)

# Save cookies to a file
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=4)
```

**Step 2: Scrape with cookies**

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

---

## 2. Detailed Scraping with Lower-Level Control

Use these examples if you need more granular control over scraping and downloading images.

### 2a. With API

#### Scrape Media

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

# 5. Add Alt Text as text file (Optional)
# Extract `alt` text from media and save it as a text file in the downloaded directory
PinterestDL.add_captions_to_file(downloaded_items, output_dir, extension="txt")
```

#### Search Media

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

# 2-5. Same steps as "Scrape Media" above
# Download, save to JSON, add captions, etc.
```

### 2b. With Browser (Playwright)

Playwright is the default browser automation backend, offering faster and more reliable scraping.

```python
import json

from pinterest_dl import PinterestDL

# 1. Initialize PinterestDL with Browser (Playwright - default)
scraped_medias = PinterestDL.with_browser(
    browser_type="chromium",  # Browser type to use ('chromium' or 'firefox')
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

### 2c. With Browser (Selenium - Legacy)

Selenium is available as a fallback for backward compatibility.

```python
import json
import warnings

from pinterest_dl import PinterestDL

# Suppress deprecation warning (Selenium will be deprecated in 1.1.0)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    
    # Initialize PinterestDL with Selenium
    scraped_medias = PinterestDL.with_selenium(
        browser_type="chrome",  # Browser type to use ('chrome' or 'firefox')
        headless=True,  # Run browser in headless mode
        ensure_alt=True,  # Ensure every image has alt text (default: False)
    ).scrape(
        url="https://www.pinterest.com/pin/1234567",  # URL of the Pinterest page
        num=30,  # Maximum number of images to scrape
    )

# Continue with download, save to JSON, add captions, etc.
```
```
