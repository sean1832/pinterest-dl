from pathlib import Path

from pinterest_dl import PinterestDL, cli_parser, io, utils


def construct_json_output(output_dir: Path) -> Path:
    return Path(f"{Path(output_dir).absolute().name}.json")


def main():
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        pdl = PinterestDL.with_browser(
            args.output,
            browser_type="firefox" if args.firefox else "chrome",
            timout=args.timeout,
            headless=not args.headful,
            incognito=args.incognito,
            verbose=args.verbose,
        )
        pdl.scrape_pins(
            args.url,
            args.limit,
            min_resolution=utils.parse_resolution(args.resolution) if args.resolution else None,
            json_output=construct_json_output(args.output) if args.json else None,
            dry_run=args.dry_run,
            add_captions=True,
        )
        print("\nDone.")
    elif args.cmd == "download":
        output_dir = args.output or str(Path(args.input).stem)
        pdl = PinterestDL(output_dir, verbose=args.verbose, timeout=args.timeout)

        # prepare image url data
        img_datas = io.read_json(args.input)
        srcs, alts, fallbacks, origins = [], [], [], []
        for img_data in img_datas if isinstance(img_datas, list) else [img_datas]:
            srcs.append(img_data["src"])
            alts.append(img_data["alt"])
            fallbacks.append(img_data["fallback"])
            origins.append(img_data["origin"])

        pdl.output_dir = Path(output_dir)  # update output directory

        # download images
        downloaded_files = pdl.download_images(srcs, fallbacks)

        # post process
        pruned_idx = pdl.prune_images(downloaded_files, args.resolution)
        pdl.add_captions(downloaded_files, alts, origins, pruned_idx)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
