import argparse
import logging
import sys
from contextlib import nullcontext
from getpass import getpass
from pathlib import Path
from traceback import print_exc
from typing import List

from pinterest_dl import PinterestDL, __description__, __version__
from pinterest_dl.data_model.pinterest_media import PinterestMedia
from pinterest_dl.utils import io

logger = logging.getLogger(__name__)


def parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse resolution string to tuple of integers.

    Args:
        resolution (str): Resolution string in the format '`width` x `height`'. (e.g. `'512x512'`)

    Returns:
        tuple[int, int]: Tuple of integers representing the resolution.
    """
    try:
        width, height = map(int, resolution.split("x"))
        return width, height
    except ValueError:
        raise ValueError("Invalid resolution format. Use 'width x height'.")


def combine_inputs(positionals: List[str], files: List[str] | None) -> List[str]:
    """Combine positional inputs and file-based inputs into a single list."""
    combined: List[str] = []

    for path in files or []:
        # Use nullcontext for stdin so __exit__ is a no-op
        ctx = nullcontext(sys.stdin) if path == "-" else open(path, "r", encoding="utf-8")
        with ctx as handle:
            for line in handle:
                url = line.strip()
                if url:
                    combined.append(url)

    combined.extend(positionals or [])
    return combined


def sanitize_url(url: str) -> str:
    """Add trailing slash to URL if not present."""
    return url if url.endswith("/") else url + "/"


# fmt: off
def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__description__ + " v" + __version__)
    parser.add_argument("-v", "--version", action="version", version="v"+__version__)

    cmd = parser.add_subparsers(dest="cmd", help="Command to run")

    # login command
    login_cmd = cmd.add_parser("login", help="Login to Pinterest and capture cookies")
    login_cmd.add_argument("-o", "--output", default="cookies.json", help="Output path for cookies")
    login_cmd.add_argument("--client", default="chrome", choices=["chrome", "firefox"], help="Browser client to login")
    login_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window")
    login_cmd.add_argument("--incognito", action="store_true", help="Incognito mode")
    login_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")

    # scrape command
    scrape_cmd = cmd.add_parser("scrape", help="Scrape images from Pinterest")
    scrape_cmd.add_argument("urls", nargs="*", help="One or more URLs to scrape")
    scrape_cmd.add_argument("-f", "--file", action="append", help="Path to file with URLs (one per line), use '-' for stdin")
    scrape_cmd.add_argument("-o", "--output", type=str, help="Output directory")
    scrape_cmd.add_argument("-c", "--cookies", type=str, help="Path to cookies file. Use this to scrape private boards.")
    scrape_cmd.add_argument("-n", "--num", type=int, default=100, help="Max number of image to scrape (default: 100)")
    scrape_cmd.add_argument("-r", "--resolution", type=str, help="Minimum resolution to keep (e.g. 512x512).")
    scrape_cmd.add_argument("--video", action="store_true", help="Download video streams if available")
    scrape_cmd.add_argument("--timeout", type=int, default=10, help="Timeout in seconds for requests (default: 10)")
    scrape_cmd.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds (default: 0.2)")
    scrape_cmd.add_argument("--cache", type=str, help="path to cache URLs into json file for reuse")
    scrape_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    scrape_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")
    scrape_cmd.add_argument("--ensure-cap", action="store_true", help="Ensure every image has alt text")
    scrape_cmd.add_argument("--cap-from-title", action="store_true", help="Use the image title as the caption")

    scrape_cmd.add_argument("--client", default="api", choices=["api", "chrome", "firefox"], help="Client to use for scraping. Chrome/Firefox is slower but more reliable.")
    scrape_cmd.add_argument("--incognito", action="store_true", help="Incognito mode (only for chrome/firefox)")
    scrape_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window (only for chrome/firefox)")

    # search command
    search_cmd = cmd.add_parser("search", help="Search images from Pinterest")
    search_cmd.add_argument("querys", nargs="*", help="Search query")
    search_cmd.add_argument("-f", "--file", action="append", help="Path to file with queries (one per line), use '-' for stdin")
    search_cmd.add_argument("-o", "--output", type=str, help="Output directory")
    search_cmd.add_argument("-c", "--cookies", type=str, help="Path to cookies file. Use this to scrape private boards.")
    search_cmd.add_argument("-n", "--num", type=int, default=100, help="Max number of image to scrape (default: 100)")
    search_cmd.add_argument("-r", "--resolution", type=str, help="Minimum resolution to keep (e.g. 512x512).")
    search_cmd.add_argument("--video", action="store_true", help="Download video streams if available")
    search_cmd.add_argument("--timeout", type=int, default=10, help="Timeout in seconds for requests (default: 10)")
    search_cmd.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds (default: 0.2)")
    search_cmd.add_argument("--cache", type=str, help="path to cache URLs into json file for reuse")
    search_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    search_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")
    search_cmd.add_argument("--ensure-cap", action="store_true", help="Ensure every image has alt text")
    search_cmd.add_argument("--cap-from-title", action="store_true", help="Use the image title as the caption")

    search_cmd.add_argument("--client", default="api", choices=["api", "chrome", "firefox"], help="Client to use for scraping. Chrome/Firefox is slower but more reliable.")
    search_cmd.add_argument("--incognito", action="store_true", help="Incognito mode (only for chrome/firefox)")
    search_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window (only for chrome/firefox)")

    # download command
    download_cmd = cmd.add_parser("download", help="Download images")
    download_cmd.add_argument("input", help="Input json file containing image urls")
    download_cmd.add_argument("-o", "--output", help="Output directory (default: ./<json_filename>)")
    download_cmd.add_argument("-r", "--resolution", type=str, help="minimum resolution to keep (e.g. 512x512).")
    download_cmd.add_argument("--video", action="store_true", help="Download video streams if available")
    download_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    download_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")
    download_cmd.add_argument("--ensure-cap", action="store_true", help="Ensure every image has alt text")

    return parser
# fmt: on


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    try:
        if args.cmd == "login":
            email = input("Enter Pinterest email: ")
            password = getpass("Enter Pinterest password: ")
            cookies = (
                PinterestDL.with_browser(
                    browser_type=args.client,
                    headless=not args.headful,
                    incognito=args.incognito,
                    verbose=args.verbose,
                )
                .login(email, password)
                .get_cookies(after_sec=7)
            )

            # save cookies
            io.write_json(cookies, args.output, 4)
            print(f"Cookies saved to '{args.output}'")

            # print instructions
            print("\nNote:")
            print("Please keep your cookies file safe and do not share it with anyone.")
            print(
                "You can use these cookies to scrape private boards. Use the '--cookies [file]' option."
            )
            print("Example:")
            print(
                r'    pinterest-dl scrape "https://www.pinterest.com/username/your-board/" "output/pin" -n 10 --cookies .\cookies.json'
            )
            print("\nDone.")
        elif args.cmd == "scrape":
            urls = combine_inputs(args.urls, args.file)
            if not urls:
                print("No URLs provided. Please provide at least one URL.")
                return
            for url in urls:
                url = sanitize_url(url)
                print(f"Scraping {url}...")
                if args.client in ["chrome", "firefox"]:
                    imgs = (
                        PinterestDL.with_browser(
                            browser_type=args.client,
                            timeout=args.timeout,
                            headless=not args.headful,
                            incognito=args.incognito,
                            verbose=args.verbose,
                            ensure_alt=args.ensure_cap,
                        )
                        .with_cookies_path(args.cookies)
                        .scrape_and_download(
                            url,
                            args.output,
                            args.num,
                            min_resolution=parse_resolution(args.resolution)
                            if args.resolution
                            else None,
                            cache_path=args.cache,
                            caption=args.caption,
                        )
                    )
                    if imgs and len(imgs) != args.num:
                        print(f"Warning: Only ({len(imgs)}) images were scraped from {url}.")
                else:
                    if args.incognito or args.headful:
                        print(
                            "Warning: Incognito and headful mode is only available for Chrome/Firefox."
                        )

                    imgs = (
                        PinterestDL.with_api(
                            timeout=args.timeout, verbose=args.verbose, ensure_alt=args.ensure_cap
                        )
                        .with_cookies_path(args.cookies)
                        .scrape_and_download(
                            url,
                            args.output,
                            args.num,
                            download_streams=args.video,
                            min_resolution=parse_resolution(args.resolution)
                            if args.resolution
                            else (0, 0),
                            cache_path=args.cache,
                            caption=args.caption,
                            delay=args.delay,
                            caption_from_title=args.cap_from_title,
                        )
                    )
                    if imgs and len(imgs) != args.num:
                        print(f"Warning: Only ({len(imgs)}) images were scraped from {url}.")

            print("\nDone.")
        elif args.cmd == "search":
            querys = combine_inputs(args.querys, args.file)
            if not querys:
                print("No queries provided. Please provide at least one query.")
                return
            for query in querys:
                print(f"Searching {query}...")
                if args.client in ["chrome", "firefox"]:
                    raise NotImplementedError(
                        "Search is currently not available for browser clients."
                    )
                else:
                    if args.incognito or args.headful:
                        print(
                            "Warning: Incognito and headful mode is only available for Chrome/Firefox."
                        )

                    imgs = (
                        PinterestDL.with_api(
                            timeout=args.timeout, verbose=args.verbose, ensure_alt=args.ensure_cap
                        )
                        .with_cookies_path(args.cookies)
                        .search_and_download(
                            query,
                            args.output,
                            args.num,
                            download_streams=args.video,
                            min_resolution=parse_resolution(args.resolution)
                            if args.resolution
                            else (0, 0),
                            cache_path=args.cache,
                            caption=args.caption,
                            delay=args.delay,
                            caption_from_title=args.cap_from_title,
                        )
                    )
                    if imgs and len(imgs) != args.num:
                        print(f"Warning: Only ({len(imgs)}) images were scraped from {query}.")
            print("\nDone.")
        elif args.cmd == "download":
            # prepare image url data
            img_datas = io.read_json(args.input)
            images: List[PinterestMedia] = []
            for img_data in img_datas if isinstance(img_datas, list) else [img_datas]:
                img = PinterestMedia.from_dict(img_data)
                if args.ensure_cap:
                    if img.alt and img.alt.strip():
                        images.append(img)
                else:
                    images.append(img)

            # download images
            output_dir = args.output or str(Path(args.input).stem)
            downloaded_imgs = PinterestDL.download_media(images, output_dir, args.video)

            # post process
            kept = PinterestDL.prune_images(downloaded_imgs, args.resolution, args.verbose)
            if args.caption == "txt" or args.caption == "json":
                PinterestDL.add_captions_to_file(
                    kept,
                    output_dir,
                    args.caption,
                    args.verbose,
                )
            elif args.caption == "metadata":
                PinterestDL.add_captions_to_meta(kept, args.verbose)
            elif args.caption != "none":
                raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")
            print("\nDone.")
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        # Log with full traceback, show user-friendly message
        logger.error(f"An error occurred: {e}", exc_info=True)
        if args.verbose:
            print("\nFull traceback:")
            print_exc()
        else:
            print(f"\nError: {e}")
            print("\nRun with --verbose for full traceback.")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging - only WARNING and above to avoid noise
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s [%(name)s]: %(message)s")
    main()
