from pinterest_dl import api, cli_parser, io, utils

def main():
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        api.run_scrape(
            args.url,
            args.threshold,
            args.output,
            persistence=args.persistence,
            write=args.write,
            firefox=args.firefox,
            incognito=args.incognito,
            dry_run=args.dry_run,
            verbose=args.verbose,
            min_resolution=utils.parse_resolution(args.resolution) if args.resolution else None,
        )
        print("\nDone.")
    elif args.cmd == "download":
        img_list = io.read_json(args.url_list)
        downloaded_files = api.run_download(img_list, args.output, args.verbose)
        api.run_prune(downloaded_files, args.resolution)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
