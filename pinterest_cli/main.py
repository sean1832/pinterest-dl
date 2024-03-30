import requests

from pinterest_cli import cli_parser, downloader, io, scraper, utils


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
        downloaded_files = []
        for i in img_urls:
            try:
                downloaded_file = downloader.download(i, output, verbose=verbose)
            except requests.exceptions.HTTPError:
                # if original image is not available, try to download 736x version
                i = i.replace("originals", "736x")
                downloaded_file = downloader.download(i, output, verbose=verbose)

            if downloaded_file:
                downloaded_files.append(downloaded_file)
        # post download
        if min_resolution:
            for i in downloaded_files:
                utils.prune_by_resolution(i, min_resolution)
    else:
        for i in img_urls:
            print(i)
    print("Done.")


def run_download(url_list, output, verbose):
    img_urls = io.read_json(url_list)
    for i in img_urls:
        downloader.download(i, output, verbose=verbose)
    print("Done.")


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
    elif args.cmd == "download":
        run_download(args.url_list, args.output, args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
