
# Pinterest Media Downloader (pinterest-dl)

[![PyPI - Version](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://pypi.org/project/pinterest-dl/)
[![PyPI - License](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

**English | [中文](https://github.com/sean1832/pinterest-dl/blob/main/README_CN.md)**

CLI to download images and videos from any Pinterest board, pin, or search query.

![scrape demo](https://raw.githubusercontent.com/sean1832/pinterest-dl/main/doc/images/pinterest-dl-scrape.gif)

## Features

- Scrape and download images and videos from any board, pin, section, or search query.
- API-first and fast: scrapes through Pinterest's API by default, with optional Playwright browser automation.
- Download videos as MP4 (with ffmpeg) or as raw .ts streams (no ffmpeg required).
- Reach private boards and pins by authenticating with browser cookies.
- Scrape multiple URLs or queries at once, or batch them from a file.
- Download asynchronously, and save scraped URLs to JSON to re-download later.
- Embed alt text as an EXIF comment for searchability, or save it as a sidecar text file.

## Installation

Requires Python 3.10 or newer.

```bash
pip install pinterest-dl
```

Optional extras add image and metadata features:

| Command | Adds |
| --- | --- |
| `pip install pinterest-dl[browser]` | Browser automation for `--client chromium/firefox` and `login` (Playwright) |
| `pip install pinterest-dl[image]` | Image resolution detection and pruning (Pillow) |
| `pip install pinterest-dl[exif]` | Embed alt text as EXIF metadata (pyexiv2) |
| `pip install pinterest-dl[metadata]` | Both of the above |

Some features need extra tools on your system:

- Browser backends: install the extra with `pip install pinterest-dl[browser]`, then run `playwright install chromium` (or `firefox`) before using `--client chromium/firefox`. The API client (default) needs neither. To capture cookies from an already-installed browser without Playwright, use `pinterest-dl login --from-browser`.
- Video to MP4: install [ffmpeg](https://ffmpeg.org/). Without it, use `--skip-remux` to keep the raw .ts file.

See [Optional Dependencies](https://github.com/sean1832/pinterest-dl/blob/main/doc/OPTIONAL_DEPENDENCIES.md) for the full matrix.

<details>
<summary>Install from source</summary>

```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .          # or: pip install .[all]
```
</details>

## Quick Start

### Command line

```bash
# Download a single pin (pin URLs return the pin itself)
pinterest-dl scrape "<pin_url>" -o ./output

# Download a pin plus related pins (pin + 49 related)
pinterest-dl scrape "<pin_url>" -o ./output -n 50

# Search and download 30 pins
pinterest-dl search "nature photography" -o ./output -n 30

# Download a pin's video as MP4 (needs ffmpeg)
pinterest-dl scrape "<pin_url>" --video -o ./output

# Reach a private board: log in once, then pass the cookies
pinterest-dl login -o cookies.json
pinterest-dl scrape "<private_board_url>" -c cookies.json -o ./output

# Machine-readable output: emit JSON to stdout (no -o means metadata only)
pinterest-dl scrape "<pin_url>" -n 10 --json | jq '.results[0].items[].src'
```

Read the full [CLI guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI.md) for every command and option.

### Python

```python
from pinterest_dl import PinterestDL

# Scrape a board and download the images
images = PinterestDL.with_api().scrape_and_download(
    url="https://www.pinterest.com/username/board-name/",
    output_dir="images/art",
    num=30,
)

# Search and download
images = PinterestDL.with_api().search_and_download(
    query="landscape art",
    output_dir="images/landscapes",
    num=50,
)
```

Read the full [API guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/API.md) or browse [runnable examples](https://github.com/sean1832/pinterest-dl/blob/main/examples/).

## Documentation

- [CLI guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI.md) - every command and option
- [Python API guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/API.md) - programmatic usage and patterns
- [Optional dependencies](https://github.com/sean1832/pinterest-dl/blob/main/doc/OPTIONAL_DEPENDENCIES.md) - the full extras matrix
- [Testing guide](https://github.com/sean1832/pinterest-dl/blob/main/doc/TESTING.md) - offline-by-default tests and live integration tests
- [Contributing](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md) - how to contribute

## Disclaimer

> [!WARNING]
> This project is independent and not affiliated with Pinterest. It is intended for educational use only. Automated scraping may conflict with Pinterest's [Terms of Service](https://developers.pinterest.com/terms/). The author disclaims any liability for misuse. Use it responsibly and at your own legal risk.

## Related

- [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui) - a graphical interface built on this library.
- Inspired by [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md) for the code of conduct, commit conventions, and pull request process.

## License

Licensed under the Apache 2.0 License. See [LICENSE](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE).

## Support

If this tool saved you time, you can [buy me a coffee](https://www.buymeacoffee.com/zekezhang).

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

---

Made by [sean1832](https://github.com/sean1832). Not affiliated with Pinterest; all trademarks are property of their respective owners.
