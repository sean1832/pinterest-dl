"""
Example: Using Debug Mode in Pinterest-DL
==========================================

This example demonstrates how to use the debug mode feature to dump
all API requests and responses to JSON files for debugging purposes.
"""

from pathlib import Path

from pinterest_dl import PinterestDL


def example_1_basic_debug():
    """Basic debug mode usage."""
    print("Example 1: Basic Debug Mode")
    print("-" * 50)

    # Create scraper with debug mode enabled
    scraper = PinterestDL.with_api(debug_mode=True)

    # All API calls will be logged to "debug/" directory
    url = "https://www.pinterest.com/pin/900438519273272242/"
    medias = scraper.scrape(url, num=3)

    print(f"✓ Scraped {len(medias)} items")
    print("✓ Debug files saved to: debug/")
    print()


def example_2_custom_debug_dir():
    """Using a custom debug directory."""
    print("Example 2: Custom Debug Directory")
    print("-" * 50)

    # Specify custom debug directory
    scraper = PinterestDL.with_api(debug_mode=True, debug_dir="my_custom_debug")

    url = "https://www.pinterest.com/pin/900438519273272242/"
    medias = scraper.scrape(url, num=2)

    print(f"✓ Scraped {len(medias)} items")
    print("✓ Debug files saved to: my_custom_debug/")

    # List debug files
    debug_dir = Path("my_custom_debug")
    if debug_dir.exists():
        files = list(debug_dir.glob("*.json"))
        print(f"✓ Found {len(files)} debug file(s):")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    print()


def example_3_with_cookies():
    """Debug mode with authentication (cookies)."""
    print("Example 3: Debug Mode with Cookies")
    print("-" * 50)

    # When using cookies, debug files will show authentication headers
    scraper = PinterestDL.with_api(debug_mode=True, debug_dir="auth_debug")

    # Load cookies if available (adjust path as needed)
    cookies_path = Path("cookies.json")
    if cookies_path.exists():
        scraper = scraper.with_cookies_path(cookies_path)
        print("✓ Cookies loaded")
    else:
        print("ℹ No cookies file found (using public access)")

    # Scraping will dump request headers including cookies
    url = "https://www.pinterest.com/pin/900438519273272242/"
    medias = scraper.scrape(url, num=2)

    print(f"✓ Scraped {len(medias)} items")
    print("✓ Debug files with auth info saved to: auth_debug/")
    print()


def example_4_error_debugging():
    """Demonstrating error debugging."""
    print("Example 4: Error Debugging")
    print("-" * 50)

    scraper = PinterestDL.with_api(debug_mode=True, debug_dir="error_debug")

    try:
        # Try scraping with an invalid URL (should fail)
        scraper.scrape("https://www.pinterest.com/pin/invalid/", num=2)
    except Exception as e:
        print(f"✗ Error occurred: {e}")
        print("✓ Error debug file saved to: error_debug/")

        # Check for error files
        debug_dir = Path("error_debug")
        if debug_dir.exists():
            error_files = list(debug_dir.glob("error_*.json"))
            print(f"✓ Found {len(error_files)} error debug file(s)")
    print()


def example_5_search_debugging():
    """Debug mode with search functionality."""
    print("Example 5: Search Debug Mode")
    print("-" * 50)

    scraper = PinterestDL.with_api(debug_mode=True, debug_dir="search_debug")

    # Search operations will be logged
    results = scraper.search("cats", num=5, min_resolution=(0, 0))

    print(f"✓ Found {len(results)} search results")
    print("✓ Search debug files saved to: search_debug/")

    # Debug files will be named like: get_search_cats.json
    debug_dir = Path("search_debug")
    if debug_dir.exists():
        search_files = list(debug_dir.glob("get_search_*.json"))
        print(f"✓ Found {len(search_files)} search debug file(s)")
    print()


def example_6_manual_debug_utils():
    """Using debug utilities directly."""
    print("Example 6: Manual Debug Utility Usage")
    print("-" * 50)

    import requests

    from pinterest_dl.common.debug import RequestDebugger

    # Create debugger instance
    debugger = RequestDebugger("manual_debug")

    # Make a custom request
    response = requests.get("https://httpbin.org/json")

    # Manually dump the request/response
    dump_path = debugger.dump_request_response(
        request_url=response.url,
        response=response,
        filename="my_custom_request",
        metadata={"custom_field": "test_value"},
    )

    print(f"✓ Manual debug file saved to: {dump_path}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Debug Mode Examples")
    print("=" * 50)
    print()

    # Run examples
    example_1_basic_debug()
    example_2_custom_debug_dir()
    example_3_with_cookies()
    # example_4_error_debugging()  # Uncomment to test error handling
    # example_5_search_debugging()  # Uncomment to test search
    # example_6_manual_debug_utils()  # Uncomment to test manual usage

    print("=" * 50)
    print("All examples completed!")
    print("Check the various debug directories for JSON files")
    print("=" * 50)
