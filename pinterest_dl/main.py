from pathlib import Path

from pinterest_dl import PinterestDL, cli_parser
from pinterest_dl.low_level.ops import io
from pinterest_dl.low_level.pinterest import PinterestImage


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


def main() -> None:
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        PinterestDL.with_browser(
            browser_type="firefox" if args.firefox else "chrome",
            timeout=args.timeout,
            headless=not args.headful,
            incognito=args.incognito,
            verbose=args.verbose,
        ).scrape_and_download(
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
