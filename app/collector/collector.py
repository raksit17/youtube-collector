from enum import StrEnum


class CollectorType(StrEnum):
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    SEARCH = "search"


class CollectorProvider(StrEnum):
    YOUTUBE = "youtube"


class CollectorEngine(StrEnum):
    YTDLP = "yt-dlp"

from typing import Any

from app.extractor.youtube_extractor import YoutubeExtractor
from app.normalizer.normalizer import YoutubeNormalizer


class YoutubeCollector:
    """
    YouTube collector.

    Responsibilities:
    - Call yt-dlp extractor
    - Send raw yt-dlp data to normalizer
    - Return normalized data

    Does NOT:
    - Save data
    - Access database
    - Download video/audio
    """

    def __init__(
        self,
        extractor: YoutubeExtractor | None = None,
        normalizer: YoutubeNormalizer | None = None,
    ) -> None:
        self.extractor = (
            extractor
            or YoutubeExtractor()
        )

        self.normalizer = (
            normalizer
            or YoutubeNormalizer()
        )

    def collect(
        self,
        url: str,
        *,
        include_comments: bool = False,
        include_formats: bool = False,
        include_subtitles: bool = True,
        flat: bool = False,
    ) -> dict[str, Any]:
        """
        Collect data from any supported YouTube URL.

        Supports:
        - Video
        - Shorts
        - Live
        - Playlist
        - Channel
        """

        raw = self.extractor.extract(
            url,
            include_comments=include_comments,
            flat=flat,
        )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
        )

    def collect_video(
        self,
        url: str,
        *,
        include_comments: bool = False,
        include_formats: bool = False,
        include_subtitles: bool = True,
    ) -> dict[str, Any]:
        """
        Full extraction for one video.
        """

        raw = self.extractor.extract(
            url,
            include_comments=include_comments,
            flat=False,
        )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
        )

    def collect_flat(
        self,
        url: str,
    ) -> dict[str, Any]:
        """
        Fast collection for large playlists/channels.

        yt-dlp will not fully extract every video.
        """

        raw = self.extractor.extract_flat(
            url
        )

        return self.normalizer.normalize(
            raw,
            include_formats=False,
            include_subtitles=False,
        )

    def collect_channel(
        self,
        url: str,
    ) -> dict[str, Any]:
        """
        Collect channel video list using flat extraction.

        Recommended for large channels.
        """

        raw = self.extractor.extract_flat(
            url
        )

        return self.normalizer.normalize_channel(
            raw
        )

    def collect_playlist(
        self,
        url: str,
        *,
        flat: bool = True,
    ) -> dict[str, Any]:
        """
        Collect playlist metadata and entries.
        """

        raw = self.extractor.extract(
            url,
            include_comments=False,
            flat=flat,
        )

        return self.normalizer.normalize_playlist(
            raw
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search YouTube using yt-dlp.

        Example:
            ytsearch20:hololive
        """

        raw = self.extractor.search(
            query,
            limit=limit,
        )

        return self.normalizer.normalize_search(
            raw,
            query=query,
        )