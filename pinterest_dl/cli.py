import argparse
from getpass import getpass
from pathlib import Path
from traceback import print_exc

from pinterest_dl import PinterestDL, __description__, __version__
from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.ops import io


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
    scrape_cmd.add_argument("url", help="URL to scrape images from")
    scrape_cmd.add_argument("-o", "--output",type=str, help="Output directory")
    scrape_cmd.add_argument("-c", "--cookies", type=str, help="Path to cookies file. Use this to scrape private boards.")
    scrape_cmd.add_argument("-n", "--num", type=int, default=100, help="Max number of image to scrape (default: 100)")
    scrape_cmd.add_argument("-r", "--resolution", type=str, help="Minimum resolution to keep (e.g. 512x512).")
    scrape_cmd.add_argument("--timeout", type=int, default=10, help="Timeout in seconds for requests (default: 10)")
    scrape_cmd.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds (default: 0.2)")
    scrape_cmd.add_argument("--cache", type=str, help="path to cache URLs into json file for reuse")
    scrape_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    scrape_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")

    scrape_cmd.add_argument("--client", default="api", choices=["api", "chrome", "firefox"], help="Client to use for scraping. Chrome/Firefox is slower but more reliable.")
    scrape_cmd.add_argument("--incognito", action="store_true", help="Incognito mode (only for chrome/firefox)")
    scrape_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window (only for chrome/firefox)")

    # search command
    search_cmd = cmd.add_parser("search", help="Search images from Pinterest")
    search_cmd.add_argument("query", help="Search query")
    search_cmd.add_argument("-o", "--output",type=str, help="Output directory")
    search_cmd.add_argument("-c", "--cookies", type=str, help="Path to cookies file. Use this to scrape private boards.")
    search_cmd.add_argument("-n", "--num", type=int, default=100, help="Max number of image to scrape (default: 100)")
    search_cmd.add_argument("-r", "--resolution", type=str, help="Minimum resolution to keep (e.g. 512x512).")
    search_cmd.add_argument("--timeout", type=int, default=10, help="Timeout in seconds for requests (default: 10)")
    search_cmd.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds (default: 0.2)")
    search_cmd.add_argument("--cache", type=str, help="path to cache URLs into json file for reuse")
    search_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    search_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")

    search_cmd.add_argument("--client", default="api", choices=["api", "chrome", "firefox"], help="Client to use for scraping. Chrome/Firefox is slower but more reliable.")
    search_cmd.add_argument("--incognito", action="store_true", help="Incognito mode (only for chrome/firefox)")
    search_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window (only for chrome/firefox)")

    # download command
    download_cmd = cmd.add_parser("download", help="Download images")
    download_cmd.add_argument("input", help="Input json file containing image urls")
    download_cmd.add_argument("-o", "--output", help="Output directory (default: ./<json_filename>)")
    download_cmd.add_argument("-r", "--resolution", type=str, help="minimum resolution to keep (e.g. 512x512).")
    download_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")
    download_cmd.add_argument("--caption", type=str, default="none", choices=["txt", "json", "metadata", "none"], help="Caption format for downloaded images: 'txt' for alt text in separate files, 'json' for full image data in seperate file, 'metadata' embeds in image files, 'none' skips captions (default)")


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
            if args.client in ["chrome", "firefox"]:
                imgs = (
                    PinterestDL.with_browser(
                        browser_type=args.client,  # type: ignore
                        timeout=args.timeout,
                        headless=not args.headful,
                        incognito=args.incognito,
                        verbose=args.verbose,
                    )
                    .with_cookies_path(args.cookies)
                    .scrape_and_download(
                        args.url,
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
                    print(f"Warning: Only ({len(imgs)}) images were scraped from {args.url}.")
            else:
                if args.incognito or args.headful:
                    print(
                        "Warning: Incognito and headful mode is only available for Chrome/Firefox."
                    )

                imgs = (
                    PinterestDL.with_api(timeout=args.timeout, verbose=args.verbose)
                    .with_cookies_path(args.cookies)
                    .scrape_and_download(
                        args.url,
                        args.output,
                        args.num,
                        min_resolution=parse_resolution(args.resolution)
                        if args.resolution
                        else (0, 0),
                        cache_path=args.cache,
                        caption=args.caption,
                        delay=args.delay,
                    )
                )
                if imgs and len(imgs) != args.num:
                    print(f"Warning: Only ({len(imgs)}) images were scraped from {args.url}.")

            print("\nDone.")
        elif args.cmd == "search":
            if args.client in ["chrome", "firefox"]:
                raise NotImplementedError("Search is currently not available for browser clients.")
            else:
                if args.incognito or args.headful:
                    print(
                        "Warning: Incognito and headful mode is only available for Chrome/Firefox."
                    )

                imgs = (
                    PinterestDL.with_api(timeout=args.timeout, verbose=args.verbose)
                    .with_cookies_path(args.cookies)
                    .search_and_download(
                        args.query,
                        args.output,
                        args.num,
                        min_resolution=parse_resolution(args.resolution)
                        if args.resolution
                        else (0, 0),
                        cache_path=args.cache,
                        caption=args.caption,
                        delay=args.delay,
                    )
                )
                if imgs and len(imgs) != args.num:
                    print(f"Warning: Only ({len(imgs)}) images were scraped from {args.query}.")
            print("\nDone.")
        elif args.cmd == "download":
            # prepare image url data
            img_datas = io.read_json(args.input)
            images = []
            for img_data in img_datas if isinstance(img_datas, list) else [img_datas]:
                images.append(PinterestImage.from_dict(img_data))

            # download images
            output_dir = args.output or str(Path(args.input).stem)
            downloaded_imgs = PinterestDL.download_images(images, output_dir, args.verbose)

            # post process
            pruned_idx = PinterestDL.prune_images(downloaded_imgs, args.resolution, args.verbose)
            if args.caption == "txt" or args.caption == "json":
                PinterestDL.add_captions_to_file(
                    downloaded_imgs, output_dir, args.caption, args.verbose
                )
            elif args.caption == "metadata":
                PinterestDL.add_captions_to_meta(downloaded_imgs, pruned_idx, args.verbose)
            elif args.caption != "none":
                raise ValueError("Invalid caption mode. Use 'txt', 'json', 'metadata', or 'none'.")
            print("\nDone.")
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            print_exc()


if __name__ == "__main__":
    main()
