from typing import Any


PREFERRED_SUBTITLE_FORMATS = (
    "json3",
    "vtt",
    "srt",
)


def normalize_channel_data(
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "external_id": raw.get("channel_id"),
        "name": (
            raw.get("channel")
            or raw.get("uploader")
        ),
        "url": (
            raw.get("channel_url")
            or raw.get("uploader_url")
        ),
        "followers": raw.get(
            "channel_follower_count"
        ),
    }


def normalize_format(
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": raw.get("format_id"),
        "ext": raw.get("ext"),

        "width": raw.get("width"),
        "height": raw.get("height"),
        "fps": raw.get("fps"),

        "vcodec": raw.get("vcodec"),
        "acodec": raw.get("acodec"),

        "tbr": raw.get("tbr"),
        "vbr": raw.get("vbr"),
        "abr": raw.get("abr"),

        "filesize": (
            raw.get("filesize")
            or raw.get("filesize_approx")
        ),

        "protocol": raw.get("protocol"),
    }


def normalize_formats(
    raw_formats: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not raw_formats:
        return []

    return [
        normalize_format(item)
        for item in raw_formats
        if isinstance(item, dict)
    ]


def normalize_chapter(
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "title": raw.get("title"),
        "start_time": raw.get("start_time"),
        "end_time": raw.get("end_time"),
    }


def normalize_chapters(
    raw_chapters: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not raw_chapters:
        return []

    return [
        normalize_chapter(item)
        for item in raw_chapters
        if isinstance(item, dict)
    ]


def normalize_subtitle_item(
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ext": raw.get("ext"),
        "url": raw.get("url"),
        "name": raw.get("name"),
    }


def select_subtitle_format(
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Select one preferred subtitle format.

    Priority:
    json3 -> vtt -> srt
    """

    for preferred in PREFERRED_SUBTITLE_FORMATS:
        for item in items:
            if item.get("ext") == preferred:
                return normalize_subtitle_item(
                    item
                )

    if items:
        return normalize_subtitle_item(
            items[0]
        )

    return None


def normalize_subtitle_map(
    raw_subtitles: dict[str, Any] | None,
    *,
    languages: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Normalize subtitle map.

    Example language filters:
        ["en-orig"]
        ["ja"]
        ["th"]

    live_chat is ignored.
    """

    if not raw_subtitles:
        return {}

    result: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    for language, items in raw_subtitles.items():

        # live chat replay is not subtitle data
        if language == "live_chat":
            continue

        # Optional language filtering
        if (
            languages is not None
            and language not in languages
        ):
            continue

        if not isinstance(items, list):
            continue

        valid_items = [
            item
            for item in items
            if isinstance(item, dict)
        ]

        selected = select_subtitle_format(
            valid_items
        )

        if selected:
            result[language] = [
                selected
            ]

    return result


def normalize_entry_url(
    raw: dict[str, Any],
) -> str | None:
    url = (
        raw.get("webpage_url")
        or raw.get("url")
    )

    video_id = raw.get("id")

    if (
        isinstance(url, str)
        and url.startswith(
            ("http://", "https://")
        )
    ):
        return url

    if video_id:
        return (
            "https://www.youtube.com/"
            f"watch?v={video_id}"
        )

    return None


def normalize_collection_entry(
    raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "external_id": raw.get("id"),
        "title": raw.get("title"),

        "url": normalize_entry_url(raw),

        "duration": raw.get("duration"),

        "view_count": raw.get(
            "view_count"
        ),

        "live_status": raw.get(
            "live_status"
        ),
    }


def normalize_collection_entries(
    entries: list[Any] | None,
) -> list[dict[str, Any]]:
    if not entries:
        return []

    result: list[dict[str, Any]] = []

    for item in entries:
        if not isinstance(item, dict):
            continue

        result.append(
            normalize_collection_entry(
                item
            )
        )

    return result