from typing import Any

from app.extractor.chat_replay_extractor import (
    ChatReplayExtractor,
)
from app.extractor.subtitle_extractor import (
    SubtitleExtractor,
)
from app.extractor.youtube_extractor import (
    YoutubeExtractor,
)
from app.normalizer.chat import (
    normalize_chat_replay,
)
from app.normalizer.normalizer import (
    YoutubeNormalizer,
)
from app.normalizer.subtitle import (
    normalize_json3_transcript,
)


class YoutubeCollector:
    """
    YouTube collector.

    Responsibilities:
    - Call yt-dlp extractor
    - Extract subtitle/transcript when requested
    - Extract finished-live chat replay when requested
    - Send raw data to normalizers
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
        chat_replay_extractor: (
            ChatReplayExtractor
            | None
        ) = None,
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

        self.chat_replay_extractor = (
            chat_replay_extractor
            or ChatReplayExtractor()
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
        include_chat_replay: bool = False,
        flat: bool = False,
    ) -> dict[str, Any]:
        """
        Collect data from a supported YouTube URL.

        Chat replay is only fetched for:
        - a single video
        - a finished livestream
        - include_chat_replay=True
        - non-flat extraction
        """

        raw = self.extractor.extract(
            url,
            include_comments=include_comments,
            flat=flat,
        )

        transcript = None
        chat_replay = None

        if (
            include_subtitles
            and not flat
            and self._is_video(raw)
        ):
            transcript = self._extract_transcript(
                raw
            )

        if (
            include_chat_replay
            and not flat
            and self._is_video(raw)
        ):
            chat_replay = (
                self._extract_chat_replay(
                    raw
                )
            )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
            transcript=transcript,
            chat_replay=chat_replay,
        )

    def collect_video(
        self,
        url: str,
        *,
        include_comments: bool = False,
        include_formats: bool = False,
        include_subtitles: bool = True,
        include_chat_replay: bool = False,
    ) -> dict[str, Any]:
        """
        Full extraction for one video.

        Chat replay is downloaded only when
        include_chat_replay=True and the video
        is a finished livestream with replay
        available.
        """

        raw = self.extractor.extract(
            url,
            include_comments=include_comments,
            flat=False,
        )

        transcript = None
        chat_replay = None

        if include_subtitles:
            transcript = self._extract_transcript(
                raw
            )

        if include_chat_replay:
            chat_replay = (
                self._extract_chat_replay(
                    raw
                )
            )

        return self.normalizer.normalize(
            raw,
            include_formats=include_formats,
            include_subtitles=include_subtitles,
            transcript=transcript,
            chat_replay=chat_replay,
        )

    def collect_flat(
        self,
        url: str,
    ) -> dict[str, Any]:
        raw = self.extractor.extract_flat(
            url
        )

        return self.normalizer.normalize(
            raw,
            include_formats=False,
            include_subtitles=False,
            transcript=None,
            chat_replay=None,
        )

    def collect_channel(
        self,
        url: str,
    ) -> dict[str, Any]:
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
        automatic_captions = (
            raw.get("automatic_captions")
            or {}
        )

        if not automatic_captions:
            return None

        language = (
            self._find_original_caption_language(
                automatic_captions,
                raw.get("language"),
            )
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
            self.subtitle_extractor
            .extract_json3(
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

    def _extract_chat_replay(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Download and normalize YouTube live chat replay.

        Only finished livestreams are supported.
        A replay must be exposed by yt-dlp under:
            raw["subtitles"]["live_chat"]
        """

        if not self._is_finished_live(
            raw
        ):
            return None

        if not self._has_chat_replay(
            raw
        ):
            return None

        video_url = (
            raw.get("webpage_url")
            or raw.get("original_url")
        )

        if not isinstance(
            video_url,
            str,
        ):
            return None

        records = (
            self.chat_replay_extractor
            .extract(
                video_url
            )
        )

        messages = (
            normalize_chat_replay(
                records
            )
        )

        return {
            "count": len(messages),
            "messages": messages,
        }

    @staticmethod
    def _has_chat_replay(
        raw: dict[str, Any],
    ) -> bool:
        subtitles = (
            raw.get("subtitles")
            or {}
        )

        if not isinstance(
            subtitles,
            dict,
        ):
            return False

        tracks = subtitles.get(
            "live_chat"
        )

        return (
            isinstance(tracks, list)
            and len(tracks) > 0
        )

    @staticmethod
    def _is_finished_live(
        raw: dict[str, Any],
    ) -> bool:
        return bool(
            raw.get("was_live")
            or raw.get("live_status")
            == "was_live"
        )

    @staticmethod
    def _find_original_caption_language(
        automatic_captions: dict[str, Any],
        video_language: str | None,
    ) -> str | None:
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
        for track in tracks:
            if not isinstance(
                track,
                dict,
            ):
                continue

            if (
                track.get("ext")
                == "json3"
            ):
                return track

        return None

    @staticmethod
    def _is_video(
        raw: dict[str, Any],
    ) -> bool:
        raw_type = raw.get("_type")

        if raw_type in {
            "playlist",
            "multi_video",
        }:
            return False

        return bool(raw.get("id"))
