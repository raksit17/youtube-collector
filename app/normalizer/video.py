from typing import Any

from app.normalizer.common import (
    normalize_channel_data,
    normalize_chapters,
    normalize_formats,
    normalize_subtitle_map,
)


def normalize_video(
    raw: dict[str, Any],
    *,
    include_formats: bool = False,
    include_subtitles: bool = True,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "video",
        "source": "youtube",

        "external_id": raw.get("id"),

        "url": (
            raw.get("webpage_url")
            or raw.get("original_url")
        ),

        "title": raw.get("title"),
        "description": raw.get("description"),

        "channel": normalize_channel_data(raw),

        "published": {
            "upload_date": raw.get("upload_date"),
            "timestamp": raw.get("timestamp"),
            "release_timestamp": raw.get(
                "release_timestamp"
            ),
        },

        "stats": {
            "views": raw.get("view_count"),
            "likes": raw.get("like_count"),
            "comments": raw.get("comment_count"),
        },

        "media": {
            "duration": raw.get("duration"),
            "duration_string": raw.get(
                "duration_string"
            ),

            "thumbnail": raw.get("thumbnail"),

            "width": raw.get("width"),
            "height": raw.get("height"),
            "fps": raw.get("fps"),
        },

        "live": {
            "status": raw.get("live_status"),

            "is_live": raw.get("is_live"),
            "was_live": raw.get("was_live"),

            "concurrent_viewers": raw.get(
                "concurrent_view_count"
            ),
        },

        "metadata": {
            "tags": raw.get("tags") or [],
            "categories": (
                raw.get("categories") or []
            ),

            "language": raw.get("language"),

            "availability": raw.get(
                "availability"
            ),

            "age_limit": raw.get("age_limit"),
        },

        "chapters": normalize_chapters(
            raw.get("chapters")
        ),
    }

    if include_subtitles:
        result["subtitles"] = {
            "manual": normalize_subtitle_map(
                raw.get("subtitles")
            ),

            "automatic": normalize_subtitle_map(
                raw.get("automatic_captions")
            ),
        }
    else:
        result["subtitles"] = None

    if include_formats:
        result["formats"] = normalize_formats(
            raw.get("formats")
        )
    else:
        result["formats"] = None

    return result