# CLI Usage Guide

## General Command Structure
```bash
pinterest-dl [command] [options]
```

| Command                   | Description                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------- |
| [`login`](#1-login)       | Login to Pinterest to obtain browser cookies for scraping private boards and pins. |
| [`scrape`](#2-scrape)     | Download the requested pin or scrape a board/section URL.                          |
| [`related`](#3-related)   | Download pins related to a specific Pinterest pin.                                 |
| [`one`](#4-one)           | Download exactly one Pinterest pin.                                                |
| [`search`](#5-search)     | Search for images on Pinterest using a query.                                      |
| [`download`](#6-download) | Download images from a list of URLs provided in a JSON file.                       |


---

## Commands

### 1. Login  
Authenticate to Pinterest and save browser cookies for private boards/pins.

```bash
pinterest-dl login [options]
```

![login](images/pinterest-dl-login.gif)

| Options                                     | Description                | Default        |
| ------------------------------------------- | -------------------------- | -------------- |
| `-o`, `--output [file]`                     | Path to save cookies file  | `cookies.json` |
| `--client [chromium/firefox]`               | Browser type to use        | `chromium`     |
| `--backend [playwright/selenium]` (**NEW**) | Browser automation backend | `playwright`   |
| `--headful`                                 | Show browser window        | -              |
| `--incognito`                               | Use incognito mode         | -              |
| `--verbose`                                 | Enable debug output        | -              |

> [!TIP]
>  After running `login`, you'll be prompted for your Pinterest email/password. Cookies are then saved to the specified file.


---

### 2. Scrape  
Download the requested pin itself, or scrape a Board/Section URL.

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

| Options                                     | Description                                               | Default        |
| ------------------------------------------- | --------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                       | Path to file with URLs (one per line); use `-` for stdin  | -              |
| `<url>`                                     | One or more Pinterest URLs                                | -              |
| `-o`, `--output [directory]`                | Directory to save images (stdout if omitted)              | -              |
| `-c`, `--cookies [file]`                    | Path to cookies file (for private content)                | `cookies.json` |
| `-n`, `--num [number]`                      | Maximum images to download (`scrape` returns 1 for pin URLs) | `100`       |
| `-r`, `--resolution [WxH]`                  | Minimum image resolution (e.g. `512x512`)                 | -              |
| `--video`                                   | Download video stream (if available)                      | -              |
| `--skip-remux` (**NEW**)                    | Skip ffmpeg remux, output raw .ts file (no ffmpeg needed) | -              |
| `--timeout [seconds]`                       | Request timeout                                           | `10`           |
| `--delay [seconds]`                         | Delay between requests                                    | `0.2`          |
| `--cache [path]`                            | Save scraped URLs to JSON                                 | -              |
| `--caption [txt/json/metadata/none]`        | Caption format: `txt`, `json`, `metadata`, or `none`      | `none`         |
| `--ensure-cap`                              | Require alt text on every image                           | -              |
| `--cap-from-title`                          | Use image title as caption                                | -              |
| `--dump [PATH]` (**NEW**)                   | Dump API requests/responses to PATH (default: `.dump`)    | -              |
| `--client [api/chromium/firefox]`           | Scraper backend                                           | `api`          |
| `--backend [playwright/selenium]` (**NEW**) | Browser automation backend (for browser clients)          | `playwright`   |
| `--headful`                                 | Show browser window (browser clients only)                | -              |
| `--incognito`                               | Use incognito mode (browser clients only)                 | -              |
| `--verbose`                                 | Enable debug output                                       | -              |

---

### 3. Related
Download pins related to one or more Pinterest pins (API mode).

```bash
# Single or multiple pin URLs:
pinterest-dl related <pin_url1> <pin_url2> ... [options]

# From one or more files:
pinterest-dl related -f urls.txt [options]
```

| Options                              | Description                                                 | Default        |
| ------------------------------------ | ----------------------------------------------------------- | -------------- |
| `-f`, `--file [file]`                | Path to file with URLs (one per line); use `-` for stdin    | -              |
| `<pin_url>`                          | One or more Pinterest pin URLs                              | -              |
| `-o`, `--output [directory]`         | Directory to save media (stdout if omitted)                 | -              |
| `-c`, `--cookies [file]`             | Path to cookies file (for private content)                  | `cookies.json` |
| `-n`, `--num [number]`               | Maximum related pins to download                            | `100`          |
| `-r`, `--resolution [WxH]`           | Minimum image resolution                                    | -              |
| `--video`                            | Download video stream (if available)                        | -              |
| `--skip-remux` (**NEW**)             | Skip ffmpeg remux, output raw .ts file (no ffmpeg needed)   | -              |
| `--timeout [seconds]`                | Request timeout                                             | `10`           |
| `--delay [seconds]`                  | Delay between requests                                      | `0.2`          |
| `--cache [path]`                     | Save scraped URLs to JSON                                   | -              |
| `--caption [txt/json/metadata/none]` | Caption format                                              | `none`         |
| `--ensure-cap`                       | Require alt text on every image                             | -              |
| `--cap-from-title`                   | Use image title as caption                                  | -              |
| `--dump [PATH]` (**NEW**)            | Dump API requests/responses to PATH (default: `.dump`)      | -              |
| `--verbose`                          | Enable debug output                                         | -              |

---

### 4. One
Download exactly one Pinterest pin.

```bash
pinterest-dl one <pin_url> [options]

# Aliases:
pinterest-dl scrape_one <pin_url> [options]
pinterest-dl scrape-one <pin_url> [options]
```

| Options                              | Description                                               | Default        |
| ------------------------------------ | --------------------------------------------------------- | -------------- |
| `<pin_url>`                          | Pinterest pin URL                                         | -              |
| `-o`, `--output [directory]`         | Directory to save media (stdout if omitted)               | -              |
| `-c`, `--cookies [file]`             | Path to cookies file (for private content)                | `cookies.json` |
| `-r`, `--resolution [WxH]`           | Minimum image resolution                                  | -              |
| `--video`                            | Download video stream (if available)                      | -              |
| `--skip-remux` (**NEW**)             | Skip ffmpeg remux, output raw .ts file (no ffmpeg needed) | -              |
| `--timeout [seconds]`                | Request timeout                                           | `10`           |
| `--cache [path]`                     | Save scraped URLs to JSON                                 | -              |
| `--caption [txt/json/metadata/none]` | Caption format                                            | `none`         |
| `--ensure-cap`                       | Require alt text on the pin                               | -              |
| `--cap-from-title`                   | Use image title as caption                                | -              |
| `--dump [PATH]` (**NEW**)            | Dump API requests/responses to PATH (default: `.dump`)    | -              |
| `--verbose`                          | Enable debug output                                       | -              |

> [!TIP]
> `scrape` and `one` both fetch the requested pin itself. Use `related` when you want Pinterest recommendations around a pin.

---

### 5. Search  
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
| `--skip-remux` (**NEW**)             | Skip ffmpeg remux, output raw .ts file (no ffmpeg needed)   | -              |
| `--timeout [seconds]`                | Request timeout                                             | `10`           |
| `--delay [seconds]`                  | Delay between requests                                      | `0.2`          |
| `--cache [path]`                     | Save results to JSON                                        | -              |
| `--caption [txt/json/metadata/none]` | Caption format                                              | `none`         |
| `--ensure-cap`                       | Require alt text on every image                             | -              |
| `--cap-from-title`                   | Use image title as caption                                  | -              |
| `--dump [PATH]` (**NEW**)            | Dump API requests/responses to PATH (default: `.dump`)      | -              |
| `--verbose`                          | Enable debug output                                         | -              |

---

### 6. Download  
Fetch images from a previously saved cache file.

```bash
pinterest-dl download <cache.json> [options]
```
![download](images/pinterest-dl-download.gif)

| Options                              | Description                                               | Default             |
| ------------------------------------ | --------------------------------------------------------- | ------------------- |
| `-o`, `--output [dir]`               | Directory to save images                                  | `./<json_filename>` |
| `-r`, `--resolution [WxH]`           | Minimum image resolution                                  | -                   |
| `--video`                            | Download video stream (if available)                      | -                   |
| `--skip-remux` (**NEW**)             | Skip ffmpeg remux, output raw .ts file (no ffmpeg needed) | -                   |
| `--caption [txt/json/metadata/none]` | Caption format                                            | `none`              |
| `--ensure-cap`                       | Require alt text on every image                           | -                   |
| `--verbose`                          | Enable debug output                                       | -                   |
