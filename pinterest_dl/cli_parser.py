import argparse

from pinterest_dl import __description__, __version__


# fmt: off
def get_parser():
    parser = argparse.ArgumentParser(description=__description__ + " v" + __version__)
    parser.add_argument("-v", "--version", action="version", version="v"+__version__)

    cmd = parser.add_subparsers(dest="cmd", help="Command to run")

    # scrape command
    scrape_cmd = cmd.add_parser("scrape", help="Scrape images from Pinterest")
    scrape_cmd.add_argument("url", help="URL to scrape images from")
    scrape_cmd.add_argument("output", help="Output directory")
    scrape_cmd.add_argument("-l", "--limit", type=int, default=100, help="Max number of image to scrape (default: 100)")
    scrape_cmd.add_argument("-r", "--resolution", type=str, help="Minimum resolution to keep (e.g. 512x512).")
    scrape_cmd.add_argument("--timeout", type=int, default=3, help="Timeout in seconds for requests (default: 3)")
    scrape_cmd.add_argument("--incognito", action="store_true", help="Incognito mode")
    scrape_cmd.add_argument("--json", action="store_true", help="Write urls to json file")
    scrape_cmd.add_argument("--dry-run", action="store_true", help="Run without download")
    scrape_cmd.add_argument("--firefox", action="store_true", help="Use Firefox browser")
    scrape_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window")
    scrape_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")

    # download command
    download_cmd = cmd.add_parser("download", help="Download images")
    download_cmd.add_argument("input", help="Input json file containing image urls")
    download_cmd.add_argument("-o", "--output", help="Output directory (default: ./<json_filename>)")
    download_cmd.add_argument("-r", "--resolution", type=str, help="minimum resolution to keep (e.g. 512x512).")
    download_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")

    return parser
# fmt: on
