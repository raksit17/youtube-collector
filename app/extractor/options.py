import os
from typing import Any


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def build_options(
    *,
    include_comments: bool | None = None,
    flat: bool | None = None,
) -> dict[str, Any]:
    """
    Build yt-dlp options for metadata extraction.

    This collector does not download video/audio files.
    """

    default_include_comments = _env_bool(
        "YTDLP_INCLUDE_COMMENTS",
        False,
    )

    default_flat = _env_bool(
        "YTDLP_DEFAULT_FLAT",
        False,
    )

    options: dict[str, Any] = {
        # Collector only
        "skip_download": True,

        # Logging
        "quiet": _env_bool(
            "YTDLP_QUIET",
            True,
        ),
        "no_warnings": _env_bool(
            "YTDLP_NO_WARNINGS",
            True,
        ),

        # Extraction
        "extract_flat": (
            default_flat
            if flat is None
            else flat
        ),

        "getcomments": (
            default_include_comments
            if include_comments is None
            else include_comments
        ),

        # Network
        "retries": _env_int(
            "YTDLP_RETRIES",
            3,
        ),
        "fragment_retries": _env_int(
            "YTDLP_FRAGMENT_RETRIES",
            3,
        ),
        "socket_timeout": _env_int(
            "YTDLP_SOCKET_TIMEOUT",
            20,
        ),

        # We want errors to propagate to our application
        "ignoreerrors": False,

        # Do not write anything to disk
        "writeinfojson": False,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }

    proxy = os.getenv("YTDLP_PROXY")

    if proxy:
        options["proxy"] = proxy

    cookie_file = os.getenv(
        "YTDLP_COOKIE_FILE"
    )

    if cookie_file:
        options["cookiefile"] = cookie_file

    return options