from typing import Any

from app.normalizer.channel import (
    normalize_channel as normalize_channel_data,
)
from app.normalizer.playlist import (
    normalize_playlist as normalize_playlist_data,
)
from app.normalizer.video import normalize_video
from app.normalizer.common import (
    normalize_collection_entries,
)


class YoutubeNormalizer:
    """
    Normalize yt-dlp raw info_dict into
    application-defined structures.
    """

    def normalize(
        self,
        raw: dict[str, Any],
        *,
        include_formats: bool = False,
        include_subtitles: bool = True,
        transcript: dict[str, Any] | None = None,
        chat_replay: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_type = raw.get(
            "_type",
            "video",
        )

        if raw_type in {
            "playlist",
            "multi_video",
        }:
            return self.normalize_playlist(
                raw
            )

        return normalize_video(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
            transcript=transcript,
            chat_replay=chat_replay,
        )

    def normalize_playlist(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        return normalize_playlist_data(
            raw
        )

    def normalize_channel(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        return normalize_channel_data(
            raw
        )

    def normalize_search(
        self,
        raw: dict[str, Any],
        *,
        query: str,
    ) -> dict[str, Any]:
        entries = normalize_collection_entries(
            raw.get("entries")
        )

        return {
            "type": "search",
            "source": "youtube",
            "query": query,
            "count": len(entries),
            "entries": entries,
        }
