from pathlib import Path

from pinterest_dl import PinterestDL, cli_parser, io, utils
from pinterest_dl.scraper import PinterestImage


def construct_json_output(output_dir: Path) -> Path:
    return Path(f"{Path(output_dir).absolute().name}.json")


def main():
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
            min_resolution=utils.parse_resolution(args.resolution) if args.resolution else None,
            json_output=construct_json_output(args.output) if args.json else None,
            dry_run=args.dry_run,
            add_captions=True,
        )
        print("\nDone.")
    elif args.cmd == "download":
        # prepare image url data
        img_datas = io.read_json(args.input)
        # srcs, alts, fallbacks, origins = [], [], [], []
        images = []
        for img_data in img_datas if isinstance(img_datas, list) else [img_datas]:
            images.append(PinterestImage.from_dict(img_data))

        # download images
        output_dir = args.output or str(Path(args.input).stem)
        downloaded_files = PinterestDL.download_images(images, output_dir, args.verbose)

        # post process
        alts = [img.alt for img in images]
        origins = [img.origin for img in images]
        pruned_idx = PinterestDL.prune_images(downloaded_files, args.resolution, args.verbose)
        PinterestDL.add_captions(downloaded_files, alts, origins, pruned_idx, args.verbose)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
