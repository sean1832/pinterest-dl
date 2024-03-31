from pinterest_dl import downloader, io, scraper, utils


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
        exe_path=utils.get_appdata_dir("chromedriver.exe"),
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
