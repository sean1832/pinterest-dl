"""
Example: Streaming and Progress Reporting
=========================================

This example demonstrates the lazy iterator API (iter_scrape / iter_search)
and the on_progress callback. These let library callers stream results, drive
their own progress bar, and stop early - without the scraper forcing a progress
bar on them.
"""

import itertools

from tqdm import tqdm

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these to your actual Pinterest links / queries
# ============================================================================
BOARD_URL = "https://www.pinterest.com/username/board-name/"
PIN_URL = "https://www.pinterest.com/pin/12345678/"
SEARCH_QUERY = "mountain landscapes"


def example_1_stream_with_tqdm():
    """Wrap iter_scrape with your own tqdm bar.

    iter_scrape yields PinterestMedia lazily and never creates a progress bar
    itself, so the caller decides how progress is shown. itertools.islice caps
    how many items are pulled from the otherwise open-ended stream.
    """
    print("Example 1: Stream with your own tqdm bar")
    print("-" * 50)

    scraper = PinterestDL.with_api()
    num = 30

    medias = list(
        tqdm(
            itertools.islice(scraper.iter_scrape(BOARD_URL), num),
            total=num,
            desc="Scraping",
        )
    )

    print(f"> Streamed {len(medias)} items")
    print()


def example_2_process_while_streaming():
    """Act on each item as it arrives instead of collecting a list.

    Because iteration is lazy, results can be handled before the whole board is
    scraped, and iteration can stop as soon as enough have been collected. No
    further requests are made after the loop breaks.
    """
    print("Example 2: Process while streaming")
    print("-" * 50)

    scraper = PinterestDL.with_api()

    for i, media in enumerate(scraper.iter_scrape(BOARD_URL), start=1):
        print(f"  [{i}] {media.src}")
        if i >= 5:
            break

    print()


def example_3_on_progress_callback():
    """Use the on_progress callback with the eager scrape() API.

    scrape() returns the full list, but on_progress fires once per scraped item
    so a bar can be driven without switching to iter_scrape.
    """
    print("Example 3: on_progress callback")
    print("-" * 50)

    scraper = PinterestDL.with_api()
    num = 20

    with tqdm(total=num, desc="Scraping") as pbar:

        def advance(_media):
            pbar.update(1)

        medias = scraper.scrape(url=BOARD_URL, num=num, on_progress=advance)

    print(f"> Scraped {len(medias)} items")
    print()


def example_4_stream_search():
    """Stream search results lazily with iter_search."""
    print("Example 4: Stream search results")
    print("-" * 50)

    scraper = PinterestDL.with_api()
    num = 15

    medias = list(
        tqdm(
            itertools.islice(scraper.iter_search(SEARCH_QUERY), num),
            total=num,
            desc="Searching",
        )
    )

    print(f"> Streamed {len(medias)} search results")
    print()


def example_5_custom_progress_sink():
    """Route progress somewhere other than a terminal bar.

    on_progress receives each PinterestMedia, so the callback can push to a
    queue, a websocket, a GUI, or a counter - anything the consumer wants.
    """
    print("Example 5: Custom progress sink")
    print("-" * 50)

    scraper = PinterestDL.with_api()
    seen = []

    def on_progress(media):
        seen.append(media.src)
        print(f"  scraped {len(seen)}: {media.src}")

    medias = scraper.scrape(url=PIN_URL, num=5, on_progress=on_progress)

    print(f"> Scraped {len(medias)} items, tracked {len(seen)} in the sink")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Streaming and Progress Examples")
    print("=" * 50)
    print()

    # Run examples (comment out the ones you don't need)
    example_1_stream_with_tqdm()
    example_2_process_while_streaming()
    example_3_on_progress_callback()
    example_4_stream_search()
    example_5_custom_progress_sink()

    print("=" * 50)
    print("All streaming examples completed!")
    print("=" * 50)
