import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import requests
from tqdm import tqdm


def fetch(
    url: str, response_format: Literal["json", "text"] = "text"
) -> Union[Dict[str, Any], str]:
    if isinstance(url, str):
        req = requests.get(url)
        req.raise_for_status()
        if response_format == "json":
            return req.json()  # JSON response may contain more complex structures
        elif response_format == "text":
            return req.text
    else:
        raise ValueError("URL must be a string.")


def download(url: str, output_dir: Path, chunk_size: int = 2048) -> Path:
    if isinstance(url, str):
        req = requests.get(url)
        req.raise_for_status()

        filename = Path(url).name
        outfile = Path.joinpath(output_dir, filename)
        # create directory if not exist
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with open(outfile, "wb") as payload:
            for chunk in req.iter_content(chunk_size):
                payload.write(chunk)
        return outfile
    else:
        print("URL must be a string.")


def download_with_fallback(
    url: str, output_dir: Path, fallback_url: List[str], chunk_size: int = 2048
) -> Path:
    try:
        return download(url, output_dir, chunk_size)
    except requests.exceptions.HTTPError:
        for fallback in fallback_url:
            try:
                return download(fallback, output_dir, chunk_size)
            except requests.exceptions.HTTPError:
                continue

    raise requests.exceptions.HTTPError("All download attempts failed.")


def download_concurrent(
    urls: List[str], output_dir: Path, chunk_size: int = 2048, verbose: bool = False
) -> List[Path]:
    results: List[Optional[Path]] = [None] * len(
        urls
    )  # Initialize a list to hold the results in order
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(
        total=len(urls), desc="Downloading"
    ) as pbar:
        futures = {
            executor.submit(download, url, output_dir, chunk_size): idx
            for idx, url in enumerate(urls)
        }
        for future in concurrent.futures.as_completed(futures):
            result_index = futures[future]  # Get the original index for the result
            outfile = future.result()
            results[result_index] = outfile  # Place the result in the corresponding position
            pbar.update(1)
    # Filter out None values
    return [result for result in results if result is not None]


def download_concurrent_with_fallback(
    urls: List[str],
    output_dir: Path,
    fallback_urls: List[List[str]],
    chunk_size: int = 2048,
    verbose: bool = False,
) -> List[Path]:
    results: List[Optional[Path]] = [None] * len(
        urls
    )  # Initialize a list to hold the results in order
    with concurrent.futures.ThreadPoolExecutor() as executor, tqdm(
        total=len(urls), desc="Downloading", disable=verbose
    ) as pbar:
        futures = {
            executor.submit(download_with_fallback, url, output_dir, fallback_url, chunk_size): idx
            for idx, (url, fallback_url) in enumerate(zip(urls, fallback_urls))
        }
        for future in concurrent.futures.as_completed(futures):
            result_index = futures[future]  # Get the original index for the result
            outfile = future.result()
            results[result_index] = outfile  # Place the result in the corresponding position
            pbar.update(1)
    # Filter out None values
    return [result for result in results if result is not None]
