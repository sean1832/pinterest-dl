import concurrent.futures
from pathlib import Path

import requests
from tqdm import tqdm


def download(url: str, output_dir, chunk_size=2048):
    if isinstance(url, str):
        req = requests.get(url)
        req.raise_for_status()

        filename = Path(url).name
        outfile = Path.joinpath(Path(output_dir), filename)
        # create directory if not exist
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with open(outfile, "wb") as payload:
            for chunk in req.iter_content(chunk_size):
                payload.write(chunk)
        return outfile
    else:
        print("URL must be a string.")


def download_with_fallback(url: str, output_dir, fallback_url, chunk_size=2048):
    try:
        return download(url, output_dir, chunk_size)
    except requests.exceptions.HTTPError:
        return download(fallback_url, output_dir, chunk_size)


def download_concurrent(urls: list, output_dir, chunk_size=2048, verbose=False):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(
        total=len(urls), desc="Downloading"
    ) as pbar:
        futures = [executor.submit(download, url, output_dir, chunk_size, verbose) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            outfile = future.result()
            pbar.update(1)
            if verbose:
                print(f"Downloaded {outfile.name}")
            results.append(outfile)
    return results


def download_concurrent_with_fallback(
    urls: list, output_dir, fallback_urls, chunk_size=2048, verbose=False
):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(
        total=len(urls), desc="Downloading"
    ) as pbar:
        futures = [
            executor.submit(download_with_fallback, url, output_dir, fallback_url, chunk_size)
            for url, fallback_url in zip(urls, fallback_urls)
        ]
        for future in concurrent.futures.as_completed(futures):
            outfile = future.result()
            pbar.update(1)
            if verbose:
                print(f"Downloaded {outfile.name}")
            results.append(outfile)
    return results
