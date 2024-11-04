from pathlib import Path

from pinterest_dl import api, cli_parser, io, utils


def main():
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        api.run_scrape(
            args.url,
            args.limit,
            args.output,
            timeout=args.timeout,
            json=args.json,
            firefox=args.firefox,
            incognito=args.incognito,
            headful=args.headful,
            dry_run=args.dry_run,
            verbose=args.verbose,
            min_resolution=utils.parse_resolution(args.resolution) if args.resolution else None,
        )
        print("\nDone.")
    elif args.cmd == "download":
        # prepare image url data
        img_datas = io.read_json(args.input)
        srcs, alts, fallbacks, origins = [], [], [], []
        for img_data in img_datas:
            srcs.append(img_data["src"])
            alts.append(img_data["alt"])
            fallbacks.append(img_data["fallback"])
            origins.append(img_data["origin"])

        output_dir = args.output or str(Path(args.input).stem)

        # download images
        downloaded_files = api.run_download(srcs, fallbacks, output_dir, args.verbose)

        # post process
        pruned_idx = api.run_prune(downloaded_files, args.resolution)
        api.run_caption(downloaded_files, alts, origins, pruned_idx, verbose=args.verbose)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
