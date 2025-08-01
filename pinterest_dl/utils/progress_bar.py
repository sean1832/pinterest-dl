from tqdm import tqdm


class TqdmProgressBarCallback:
    """A callback class for tqdm progress bar to track download progress."""

    def __init__(self, description: str = "Downloading", unit: str = "it"):
        self._pbar = tqdm(total=0, desc=description, unit=unit)
        self._last_total = 0

    def __call__(self, downloaded_segments: int, total_segments: int):
        # If total changed (first call or updated), adjust bar.
        if total_segments != self._last_total:
            self._pbar.total = total_segments
            self._last_total = total_segments

        delta = downloaded_segments - self._pbar.n
        if delta > 0:
            self._pbar.update(delta)

        if downloaded_segments >= total_segments:
            self._pbar.close()
