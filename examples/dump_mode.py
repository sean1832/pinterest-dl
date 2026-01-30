"""
Example: Using Dump Mode in Pinterest-DL
=========================================

This example demonstrates how to use the dump mode feature to dump
all API requests and responses to JSON files for debugging purposes.
"""

from pathlib import Path

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these URLs/queries to your actual Pinterest links
# ============================================================================
PIN_URL = "https://www.pinterest.com/pin/12345678/"
INVALID_URL = "https://www.pinterest.com/pin/invalid/"
SEARCH_QUERY = "cats"


def example_1_basic_dump():
    """Basic dump mode usage."""
    print("Example 1: Basic Dump Mode")
    print("-" * 50)

    # Create scraper with dump mode enabled (uses .dump directory)
    scraper = PinterestDL.with_api(dump=".dump")

    # All API calls will be logged to ".dump/" directory
    medias = scraper.scrape(PIN_URL, num=3)

    print(f"> Scraped {len(medias)} items")
    print("> Dump files saved to: .dump/")
    print()


def example_2_custom_dump_dir():
    """Using a custom dump directory."""
    print("Example 2: Custom Dump Directory")
    print("-" * 50)

    # Specify custom dump directory
    scraper = PinterestDL.with_api(dump="my_custom_dump")

    medias = scraper.scrape(PIN_URL, num=2)

    print(f"> Scraped {len(medias)} items")
    print("> Dump files saved to: my_custom_dump/")

    # List dump files
    dump_dir = Path("my_custom_dump")
    if dump_dir.exists():
        files = list(dump_dir.glob("*.json"))
        print(f"> Found {len(files)} dump file(s):")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    print()


def example_3_with_cookies():
    """Dump mode with authentication (cookies)."""
    print("Example 3: Dump Mode with Cookies")
    print("-" * 50)

    # When using cookies, dump files will show authentication headers
    scraper = PinterestDL.with_api(dump="auth_dump")

    # Load cookies if available (adjust path as needed)
    cookies_path = Path("cookies.json")
    if cookies_path.exists():
        scraper = scraper.with_cookies_path(cookies_path)
        print("> Cookies loaded")
    else:
        print("Note: No cookies file found (using public access)")

    # Scraping will dump request headers including cookies
    medias = scraper.scrape(PIN_URL, num=2)

    print(f"> Scraped {len(medias)} items")
    print("> Dump files with auth info saved to: auth_dump/")
    print()


def example_4_error_debugging():
    """Demonstrating error debugging."""
    print("Example 4: Error Debugging")
    print("-" * 50)

    scraper = PinterestDL.with_api(dump="error_dump")

    try:
        # Try scraping with an invalid URL (should fail)
        scraper.scrape(INVALID_URL, num=2)
    except Exception as e:
        print(f"x Error occurred: {e}")
        print("> Error dump file saved to: error_dump/")

        # Check for error files
        dump_dir = Path("error_dump")
        if dump_dir.exists():
            error_files = list(dump_dir.glob("error_*.json"))
            print(f"> Found {len(error_files)} error dump file(s)")
    print()


def example_5_search_debugging():
    """Dump mode with search functionality."""
    print("Example 5: Search Dump Mode")
    print("-" * 50)

    scraper = PinterestDL.with_api(dump="search_dump")

    # Search operations will be logged
    results = scraper.search(SEARCH_QUERY, num=5, min_resolution=(0, 0))

    print(f"> Found {len(results)} search results")
    print("> Search dump files saved to: search_dump/")

    # Dump files will be named like: get_search_cats.json
    dump_dir = Path("search_dump")
    if dump_dir.exists():
        search_files = list(dump_dir.glob("get_search_*.json"))
        print(f"> Found {len(search_files)} search dump file(s)")
    print()


def example_6_manual_dump_utils():
    """Using dump utilities directly."""
    print("Example 6: Manual Dump Utility Usage")
    print("-" * 50)

    import requests

    from pinterest_dl.common.dump import RequestDumper

    # Create dumper instance
    dumper = RequestDumper("manual_dump")

    # Make a custom request
    response = requests.get("https://httpbin.org/json")

    # Manually dump the request/response
    dump_path = dumper.dump_request_response(
        request_url=response.url,
        response=response,
        filename="my_custom_request",
        metadata={"custom_field": "test_value"},
    )

    print(f"> Manual dump file saved to: {dump_path}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Dump Mode Examples")
    print("=" * 50)
    print()

    # Run examples
    example_1_basic_dump()
    example_2_custom_dump_dir()
    example_3_with_cookies()
    # example_4_error_debugging()  # Uncomment to test error handling
    # example_5_search_debugging()  # Uncomment to test search
    # example_6_manual_dump_utils()  # Uncomment to test manual usage

    print("=" * 50)
    print("All examples completed!")
    print("Check the various dump directories for JSON files")
    print("=" * 50)
