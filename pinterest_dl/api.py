from pathlib import Path
from typing import List, Tuple

from pinterest_dl import downloader, io, scraper, utils


def run_download(
    img_urls: List[str | Path], output: str | Path, verbose: bool = False
) -> List[str | Path]:
    """download images concurrently with fallback urls

    Args:
        img_urls (List[str  |  Path]): list of image urls
        output (str | Path): output directory to save images
        verbose (bool, optional): print debug logs. Defaults to False.

    Returns:
        List[str  |  Path]: list of downloaded image paths
    """
    fallback_urls = [i.replace("/originals/", "/736x/") for i in img_urls]
    return downloader.download_concurrent_with_fallback(
        img_urls, output, fallback_urls, verbose=verbose
    )


def run_prune(local_images: List[str | Path], min_resolution: Tuple[int, int]):
    """prune images by resolution

    Args:
        local_images (List[str  |  Path]): list of image paths
        min_resolution (Tuple[int, int]): minimum resolution to keep
    """
    if min_resolution:
        for i in local_images:
            utils.prune_by_resolution(i, min_resolution)


def run_scrape(
    url: str,
    threshold: int,
    output: str | Path,
    persistence: int = 120,
    write: str | Path = None,
    firefox: bool = False,
    incognito: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    min_resolution: Tuple[int, int] = None,
):
    """extracts image urls from pinterest board and downloads them

    Args:
        url (str): input pinterest board url
        threshold (int): number of scroll to perform
        output (str | Path): output directory to save images
        persistence (int, optional): time to wait for page load. Defaults to 120.
        write (str | Path, optional): write image urls to json file. Defaults to None.
        firefox (bool, optional): use firefox browser. Defaults to False.
        incognito (bool, optional): use incognito mode. Defaults to False.
        dry_run (bool, optional): only print image urls. Defaults to False.
        verbose (bool, optional): print debug logs. Defaults to False.
        min_resolution (Tuple[int, int], optional): minimum resolution to keep. Defaults to None.
    """
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
