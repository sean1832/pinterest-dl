from pinterest_cli import cli_parser, downloader, io, scraper, utils


def run_download(img_urls, output, verbose):
    fallback_urls = [i.replace("/originals/", "/736x/") for i in img_urls]
    return downloader.download_concurrent_with_fallback(
        img_urls, output, fallback_urls, verbose=verbose
    )


def run_prune(local_images, min_resolution):
    if min_resolution:
        for i in local_images:
            utils.prune_by_resolution(i, min_resolution)


def run_scrape(
    url,
    threshold,
    firefox,
    output,
    write,
    persistence,
    incognito,
    dry_run,
    verbose,
    min_resolution,
):
    browser = scraper.Browser().Chrome(
        exe_path=utils.get_root().joinpath("bin", "chromedriver.exe"),
        incognito=incognito,
    )
    if firefox:
        browser = scraper.Browser().Firefox()
    try:
        pin_scraper = scraper.Pinterest(browser)
        img_urls = pin_scraper.scrape(
            url,
            threshold=threshold,
            presistence=persistence,
            verbose=verbose,
        )
    finally:
        browser.close()

    print(f"Found {len(img_urls)} urls")
    if write:
        io.write_json(img_urls, write, indent=4)
    if not dry_run:
        downloaded_files = run_download(img_urls, output, verbose)

        # post download
        run_prune(downloaded_files, min_resolution)
    else:
        for i in img_urls:
            print(i)


def main():
    parser = cli_parser.get_parser()
    args = parser.parse_args()

    if args.cmd == "scrape":
        run_scrape(
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
        downloaded_files = run_download(img_list, args.output, args.verbose)
        run_prune(downloaded_files, args.resolution)
        print("\nDone.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
