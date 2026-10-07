from typing import Any

from app.extractor.subtitle_extractor import SubtitleExtractor
from app.extractor.youtube_extractor import YoutubeExtractor
from app.normalizer.normalizer import YoutubeNormalizer
from app.normalizer.subtitle import normalize_json3_transcript


class YoutubeCollector:
    """
    YouTube collector.

    Responsibilities:
    - Call yt-dlp extractor
    - Extract subtitle/transcript when requested
    - Send raw data to normalizer
    - Return normalized data

    Does NOT:
    - Save data
    - Access database
    - Download video/audio
    """

    def __init__(
        self,
        extractor: YoutubeExtractor | None = None,
        subtitle_extractor: SubtitleExtractor | None = None,
        normalizer: YoutubeNormalizer | None = None,
    ) -> None:
        self.extractor = (
            extractor
            or YoutubeExtractor()
        )

        self.subtitle_extractor = (
            subtitle_extractor
            or SubtitleExtractor()
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
        Generic collection from a YouTube URL.

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

        transcript = None

        if (
            include_subtitles
            and not flat
            and self._is_video(raw)
        ):
            transcript = self._extract_transcript(
                raw
            )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
            transcript=transcript,
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
        Fully extract one video.

        When include_subtitles=True:
        - discover original captions through yt-dlp
        - download JSON3 subtitle
        - normalize transcript
        """

        raw = self.extractor.extract(
            url,
            include_comments=include_comments,
            flat=False,
        )

        transcript = None

        if include_subtitles:
            transcript = self._extract_transcript(
                raw
            )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
            transcript=transcript,
        )

    def collect_flat(
        self,
        url: str,
    ) -> dict[str, Any]:
        """
        Fast collection for large playlists/channels.

        Does not fetch transcript.
        """

        raw = self.extractor.extract_flat(
            url
        )

        return self.normalizer.normalize(
            raw,
            include_formats=False,
            include_subtitles=False,
            transcript=None,
        )

    def collect_channel(
        self,
        url: str,
    ) -> dict[str, Any]:
        """
        Collect channel video list using
        flat extraction.
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
        """

        raw = self.extractor.search(
            query,
            limit=limit,
        )

        return self.normalizer.normalize_search(
            raw,
            query=query,
        )

    def _extract_transcript(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Extract the original automatic caption.

        Flow:
            yt-dlp automatic_captions
                ↓
            find original language
                ↓
            select json3
                ↓
            download timedtext
                ↓
            normalize transcript
        """

        automatic_captions = (
            raw.get("automatic_captions")
            or {}
        )

        if not automatic_captions:
            return None

        language = self._find_original_caption_language(
            automatic_captions,
            raw.get("language"),
        )

        if language is None:
            return None

        subtitle_formats = (
            automatic_captions.get(
                language
            )
            or []
        )

        json3_track = self._find_json3_track(
            subtitle_formats
        )

        if json3_track is None:
            return None

        subtitle_url = json3_track.get(
            "url"
        )

        if not subtitle_url:
            return None

        raw_transcript = (
            self.subtitle_extractor.extract_json3(
                subtitle_url
            )
        )

        segments = (
            normalize_json3_transcript(
                raw_transcript
            )
        )

        return {
            "language": language,
            "source": "youtube_auto",
            "format": "json3",
            "segments": segments,
        }

    @staticmethod
    def _find_original_caption_language(
        automatic_captions: dict[str, Any],
        video_language: str | None,
    ) -> str | None:
        """
        Example:

            video_language = "en"

            priority:
                en-orig
                ↓
                en
                ↓
                any *-orig
        """

        if video_language:
            original_key = (
                f"{video_language}-orig"
            )

            if (
                original_key
                in automatic_captions
            ):
                return original_key

            if (
                video_language
                in automatic_captions
            ):
                return video_language

        for language in automatic_captions:
            if language.endswith("-orig"):
                return language

        return None

    @staticmethod
    def _find_json3_track(
        tracks: list[Any],
    ) -> dict[str, Any] | None:
        """
        Find JSON3 subtitle track.
        """

        for track in tracks:
            if not isinstance(
                track,
                dict,
            ):
                continue

            if track.get("ext") == "json3":
                return track

        return None

    @staticmethod
    def _is_video(
        raw: dict[str, Any],
    ) -> bool:
        """
        Detect a single video response.

        yt-dlp may omit _type for normal videos.
        """

        raw_type = raw.get("_type")

        if raw_type in {
            "playlist",
            "multi_video",
        }:
            return False

        return bool(raw.get("id"))