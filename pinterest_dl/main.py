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
            persistence=args.persistence,
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
        img_datas = io.read_json(args.input)
        srcs, alts, fallbacks = [], [], []
        for img_data in img_datas:
            srcs.append(img_data["src"])
            alts.append(img_data["alt"])
            fallbacks.append(img_data["fallback"])
        output_dir = args.output or str(Path(args.input).stem)
        downloaded_files = api.run_download(srcs, fallbacks, output_dir, args.verbose)
        downloaded_files = api.run_prune(downloaded_files, args.resolution)
        api.run_caption(downloaded_files, alts)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
