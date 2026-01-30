# CLI Usage Guide

## General Command Structure
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

## Commands

### 1. Login  
Authenticate to Pinterest and save browser cookies for private boards/pins.

```bash
pinterest-dl login [options]
```

![login](images/pinterest-dl-login.gif)

| Options                           | Description                | Default        |
| --------------------------------- | -------------------------- | -------------- |
| `-o`, `--output [file]`           | Path to save cookies file  | `cookies.json` |
| `--client [chromium/firefox]`     | Browser type to use        | `chromium`     |
| `--backend [playwright/selenium]` | Browser automation backend | `playwright`   |
| `--headful`                       | Show browser window        | -              |
| `--incognito`                     | Use incognito mode         | -              |
| `--verbose`                       | Enable debug output        | -              |

> [!TIP]
>  After running `login`, you'll be prompted for your Pinterest email/password. Cookies are then saved to the specified file.


---

### 2. Scrape  
Download images from a Pin, Board URL, or a list of URLs.

```bash
# Single or multiple URLs:
pinterest-dl scrape <url1> <url2> ...

# From one or more files (one URL per line):
pinterest-dl scrape -f urls.txt [options]
pinterest-dl scrape -f urls1.txt -f urls2.txt [options]

# From stdin:
cat urls.txt | pinterest-dl scrape -f - [options]
```
![scrape](images/pinterest-dl-scrape.gif)

| Options                              | Description                                              | Default        |
| ------------------------------------ | -------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                | Path to file with URLs (one per line); use `-` for stdin | -              |
| `<url>`                              | One or more Pinterest URLs                               | -              |
| `-o`, `--output [directory]`         | Directory to save images (stdout if omitted)             | -              |
| `-c`, `--cookies [file]`             | Path to cookies file (for private content)               | `cookies.json` |
| `-n`, `--num [number]`               | Maximum images to download                               | `100`          |
| `-r`, `--resolution [WxH]`           | Minimum image resolution (e.g. `512x512`)                | -              |
| `--video`                            | Download video stream (if available)                     | -              |
| `--timeout [seconds]`                | Request timeout                                          | `3`            |
| `--delay [seconds]`                  | Delay between requests                                   | `0.2`          |
| `--cache [path]`                     | Save scraped URLs to JSON                                | -              |
| `--caption [txt/json/metadata/none]` | Caption format: `txt`, `json`, `metadata`, or `none`     | `none`         |
| `--ensure-cap`                       | Require alt text on every image                          | -              |
| `--client [api/chromium/firefox]`    | Scraper backend                                          | `api`          |
| `--backend [playwright/selenium]`    | Browser automation backend (for browser clients)         | `playwright`   |
| `--headful`                          | Show browser window (browser clients only)               | -              |
| `--incognito`                        | Use incognito mode (browser clients only)                | -              |
| `--verbose`                          | Enable debug output                                      | -              |

---

### 3. Search  
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

![search](images/pinterest-dl-search.gif)

| Options                              | Description                                                 | Default        |
| ------------------------------------ | ----------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                | Path to file with queries (one per line); use `-` for stdin | -              |
| `<query>`                            | One or more search terms                                    | -              |
| `-o`, `--output [directory]`         | Directory to save images (stdout if omitted)                | -              |
| `-c`, `--cookies [file]`             | Path to cookies file                                        | `cookies.json` |
| `-n`, `--num [number]`               | Maximum images to download                                  | `100`          |
| `-r`, `--resolution [WxH]`           | Minimum image resolution                                    | -              |
| `--video`                            | Download video stream (if available)                        | -              |
| `--timeout [seconds]`                | Request timeout                                             | `3`            |
| `--delay [seconds]`                  | Delay between requests                                      | `0.2`          |
| `--cache [path]`                     | Save results to JSON                                        | -              |
| `--caption [txt/json/metadata/none]` | Caption format                                              | `none`         |
| `--ensure-cap`                       | Require alt text on every image                             | -              |
| `--verbose`                          | Enable debug output                                         | -              |

---

### 4. Download  
Fetch images from a previously saved cache file.

```bash
pinterest-dl download <cache.json> [options]
```
![download](images/pinterest-dl-download.gif)

| Options                    | Description              | Default             |
| -------------------------- | ------------------------ | ------------------- |
| `-o`, `--output [dir]`     | Directory to save images | `./<json_filename>` |
| `-r`, `--resolution [WxH]` | Minimum image resolution | -                   |
| `--verbose`                | Enable debug output      | -                   |
