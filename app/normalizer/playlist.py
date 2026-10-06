from typing import Any

from app.normalizer.common import (
    normalize_channel_data,
    normalize_collection_entries,
)


def normalize_playlist(
    raw: dict[str, Any],
) -> dict[str, Any]:
    entries = normalize_collection_entries(
        raw.get("entries")
    )

    return {
        "type": "playlist",
        "source": "youtube",

        "external_id": raw.get("id"),

        "title": raw.get("title"),
        "description": raw.get("description"),

        "url": (
            raw.get("webpage_url")
            or raw.get("original_url")
        ),

        "channel": normalize_channel_data(raw),

        "count": (
            raw.get("playlist_count")
            or len(entries)
        ),

        "entries": entries,
    }