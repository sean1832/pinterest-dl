class Endpoint:
    _BASE = "https://www.pinterest.com"

    GET_RELATED_MODULES = f"{_BASE}/resource/RelatedModulesResource/get/"
    """Get related images. This can be used to get images similar to a pin."""

    GET_MAIN_IMAGE = f"{_BASE}/resource/ApiResource/get/"
    """Get main image. This can be used to get the main image of a pin."""

    GET_BOARD_RESOURCE = f"{_BASE}/resource/BoardResource/get/"
    """Get boards metadata. This can be used to get `board_id`."""

    GET_BOARD_FEED_RESOURCE = f"{_BASE}/resource/BoardFeedResource/get/"
    """Get board feed. This can be used to get board images. Requires `board_id`."""

    GET_SEARCH_RESOURCE = f"{_BASE}/resource/BaseSearchResource/get/"
    """Get search results. This can be used to search images based text queries."""

