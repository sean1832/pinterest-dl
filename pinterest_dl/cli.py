import argparse
from getpass import getpass
from pathlib import Path

from pinterest_dl import PinterestDL, __description__, __version__
from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.ops import io


def construct_json_output(output_dir: Path) -> Path:
    return Path(f"{Path(output_dir).absolute().name}.json")


def parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse resolution string to tuple of integers.

    Args:
        resolution (str): Resolution string in the format 'width x height'.

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
    login_cmd.add_argument("--firefox", action="store_true", help="Use Firefox browser")
    login_cmd.add_argument("--headful", action="store_true", help="Run in headful mode with browser window")
    login_cmd.add_argument("--incognito", action="store_true", help="Incognito mode")
    login_cmd.add_argument("--verbose", action="store_true", help="Print verbose output")

    # scrape command
    scrape_cmd = cmd.add_parser("scrape", help="Scrape images from Pinterest")
    scrape_cmd.add_argument("url", help="URL to scrape images from")
    scrape_cmd.add_argument("output", help="Output directory")
    scrape_cmd.add_argument("-c", "--cookies", type=str, help="Path to cookies file. Use this to scrape private boards.")
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


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    if args.cmd == "login":
        email = input("Enter Pinterest email: ")
        password = getpass("Enter Pinterest password: ")
        PinterestDL.with_browser(
            browser_type="firefox" if args.firefox else "chrome",
            headless=not args.headful,
            incognito=args.incognito,
            verbose=args.verbose,
        ).login(email, password).capture_cookies(after_sec=7, out_path=args.output)
        print("\nDone.")
    elif args.cmd == "scrape":
        PinterestDL.with_browser(
            browser_type="firefox" if args.firefox else "chrome",
            timeout=args.timeout,
            headless=not args.headful,
            incognito=args.incognito,
            verbose=args.verbose,
        ).with_cookies(args.cookies).scrape_and_download(
            args.url,
            args.output,
            args.limit,
            min_resolution=parse_resolution(args.resolution) if args.resolution else None,
            json_output=construct_json_output(args.output) if args.json else None,
            dry_run=args.dry_run,
            add_captions=True,
        )
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
        PinterestDL.add_captions(downloaded_imgs, pruned_idx, args.verbose)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
