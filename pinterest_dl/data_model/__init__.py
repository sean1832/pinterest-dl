"""Deprecated: This module has been reorganized. Use domain, parsers, or storage instead.

The data_model module has been split into more specific modules:
- pinterest_dl.domain.media for PinterestMedia
- pinterest_dl.parsers.response for ResponseParser
- pinterest_dl.storage.media for media file operations

This backward compatibility module will be removed in version 1.1.0.
"""

import warnings


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for old module structure."""
    if name == "PinterestMedia":
        warnings.warn(
            "Importing from pinterest_dl.data_model is deprecated and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.domain.media import PinterestMedia",
            DeprecationWarning,
            stacklevel=2,
        )
        from pinterest_dl.domain.media import PinterestMedia

        return PinterestMedia

    if name == "VideoStreamInfo":
        warnings.warn(
            "Importing from pinterest_dl.data_model is deprecated and will be removed in version 1.1.0. "
            "Use: from pinterest_dl.domain.media import VideoStreamInfo",
            DeprecationWarning,
            stacklevel=2,
        )
        from pinterest_dl.domain.media import VideoStreamInfo

        return VideoStreamInfo

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
