from pathlib import Path
from typing import List, Tuple

from tqdm import tqdm

from pinterest_dl import downloader, io, scraper, utils


def run_download(
    urls: List[str], fallbacks: List[str], output: str | Path, verbose: bool = False
) -> List[str | Path]:
    """download images concurrently with fallback urls

    Args:
        img_urls (List[str]): list of image urls
        fallbacks (List[str]): list of fallback urls
        output (str | Path): output directory to save images
        verbose (bool, optional): print debug logs. Defaults to False.

    Returns:
        List[str  |  Path]: list of downloaded image paths
    """
    return downloader.download_concurrent_with_fallback(urls, output, fallbacks, verbose=verbose)


def run_caption(files: List[str | Path], captions: List[str], verbose: bool = False):
    """write captions to image files

    Args:
        files (List[str  |  Path]): list of image paths
        captions (List[str]): list of captions
        verbose (bool, optional): print debug logs. Defaults to False.
    """
    for file, caption in zip(files, captions):
        try:
            utils.write_img_caption(file, caption)
            if verbose:
                print(f"{file} -> {caption}")
        except Exception as e:
            print(f"Error captioning {file}: {e}")


def run_prune(
    local_images: List[str | Path], min_resolution: Tuple[int, int], verbose: bool = False
):
    """prune images by resolution

    Args:
        local_images (List[str  |  Path]): list of image paths
        min_resolution (Tuple[int, int]): minimum resolution to keep
    """
    new_imgs = []
    if min_resolution:
        for i in tqdm(local_images, desc="Pruning"):
            if not utils.prune_by_resolution(i, min_resolution, verbose=verbose):
                new_imgs.append(i)
    else:
        new_imgs = local_images
    print(f"Pruned {len(local_images) - len(new_imgs)} images.")
    return new_imgs


def run_scrape(
    url: str,
    limit: int,
    output: str | Path,
    timeout: int = 3,
    json: bool = False,
    firefox: bool = False,
    incognito: bool = False,
    headful: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    min_resolution: Tuple[int, int] = None,
    caption: bool = True,
):
    """extracts image urls from pinterest board and downloads them

    Args:
        url (str): input pinterest board url
        limit (int): max number of image to scrape
        output (str | Path): output directory to save images
        persistence (int, optional): time to wait for page load. Defaults to 120.
        json (str | Path, optional): write image urls to json file. Defaults to None.
        firefox (bool, optional): use firefox browser. Defaults to False.
        incognito (bool, optional): use incognito mode. Defaults to False.
        headful (bool, optional): run in headful mode with browser window. Defaults to True.
        dry_run (bool, optional): only print image urls. Defaults to False.
        verbose (bool, optional): print debug logs. Defaults to False.
        min_resolution (Tuple[int, int], optional): minimum resolution to keep. Defaults to None.
        caption (bool, optional): write image caption as metadata. Defaults to True.
    """
    if firefox:
        browser = scraper.Browser().Firefox(incognito=incognito, headful=headful)
    else:
        browser = scraper.Browser().Chrome(
            exe_path=utils.get_appdata_dir("chromedriver.exe"),
            incognito=incognito,
            headful=headful,
        )

    try:
        pin_scraper = scraper.Pinterest(browser)
        imgs = pin_scraper.scrape(
            url,
            limit=limit,
            timeout=timeout,
            verbose=verbose,
        )
        srcs, alts, fallbacks = [], [], []
        for i in imgs:
            srcs.append(i["src"])
            alts.append(i["alt"])
            fallbacks.append(i["fallback"])
    finally:
        browser.close()

    if json:
        io.write_json(imgs, str(Path(output).absolute().name) + ".json", indent=4)
    if not dry_run:
        downloaded_files = run_download(srcs, fallbacks, output, verbose)
        # post download
        downloaded_files = run_prune(downloaded_files, min_resolution)
        if caption:
            run_caption(downloaded_files, alts, verbose=verbose)
    else:
        for i in imgs:
            print(i)
