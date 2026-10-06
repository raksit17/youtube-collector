from typing import Any

from app.normalizer.common import (
    normalize_collection_entries,
)


def normalize_channel(
    raw: dict[str, Any],
) -> dict[str, Any]:
    entries = normalize_collection_entries(
        raw.get("entries")
    )

    channel_id = (
        raw.get("channel_id")
        or raw.get("uploader_id")
        or raw.get("id")
    )

    channel_name = (
        raw.get("channel")
        or raw.get("uploader")
        or raw.get("title")
    )

    channel_url = (
        raw.get("channel_url")
        or raw.get("uploader_url")
        or raw.get("webpage_url")
        or raw.get("original_url")
    )

    return {
        "type": "channel",
        "source": "youtube",

        "external_id": channel_id,

        "name": channel_name,

        "description": raw.get("description"),

        "url": channel_url,

        "followers": raw.get(
            "channel_follower_count"
        ),

        "entries": entries,
    }