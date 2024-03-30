from pathlib import Path

import requests


def download(url: str, output_dir, chunk_size=2048, verbose=False):
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
        if verbose:
            print(f"Downloaded {filename}")
        return outfile
    else:
        print("URL must be a string.")
