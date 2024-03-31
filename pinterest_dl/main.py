from pinterest_dl import api, cli_parser, io


def main():
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        api.run_scrape(
            args.url,
            args.threshold,
            args.firefox,
            args.output,
            args.write,
            args.persistence,
            args.incognito,
            args.dry_run,
            args.verbose,
            args.resolution,
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
