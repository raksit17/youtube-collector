from typing import Any
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.utils import DownloadError

from app.extractor.exceptions import (
    InvalidYoutubeUrlError,
    YoutubeExtractorError,
    YoutubeLoginRequiredError,
    YoutubePrivateVideoError,
    YoutubeRateLimitError,
    YoutubeVideoUnavailableError,
)
from app.extractor.options import build_options


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


class YoutubeExtractor:
    """
    Extract public YouTube metadata using yt-dlp.

    Responsibilities:
    - Accept YouTube URL / search query
    - Call yt-dlp
    - Sanitize yt-dlp info_dict
    - Return raw dictionary

    This class does NOT:
    - Normalize data
    - Save to database
    - Download video/audio
    """

    def extract(
        self,
        url: str,
        *,
        include_comments: bool = False,
        flat: bool = False,
    ) -> dict[str, Any]:
        self._validate_youtube_url(url)

        options = build_options(
            include_comments=include_comments,
            flat=flat,
        )

        return self._extract(
            target=url,
            options=options,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            raise YoutubeExtractorError(
                "Search query cannot be empty",
                code="EMPTY_SEARCH_QUERY",
            )

        if limit < 1:
            raise YoutubeExtractorError(
                "Search limit must be greater than 0",
                code="INVALID_SEARCH_LIMIT",
            )

        # Prevent accidental huge searches
        limit = min(limit, 100)

        options = build_options(
            include_comments=False,
            flat=True,
        )

        target = f"ytsearch{limit}:{query}"

        return self._extract(
            target=target,
            options=options,
        )

    def extract_flat(
        self,
        url: str,
    ) -> dict[str, Any]:
        """
        Fast extraction for playlist/channel.

        Useful for discovering video IDs without
        fully extracting every video.
        """

        return self.extract(
            url,
            include_comments=False,
            flat=True,
        )

    def _extract(
        self,
        *,
        target: str,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL(
                options
            ) as ydl:
                info = ydl.extract_info(
                    target,
                    download=False,
                )

                if info is None:
                    raise YoutubeExtractorError(
                        "yt-dlp returned no data",
                        code="NO_DATA",
                    )

                return ydl.sanitize_info(
                    info
                )

        except DownloadError as exc:
            raise self._map_download_error(
                exc
            ) from exc

        except YoutubeExtractorError:
            raise

        except Exception as exc:
            raise YoutubeExtractorError(
                str(exc),
            ) from exc

    @staticmethod
    def _validate_youtube_url(
        url: str,
    ) -> None:
        try:
            parsed = urlparse(url)

            host = (
                parsed.hostname or ""
            ).lower()

        except ValueError as exc:
            raise InvalidYoutubeUrlError(
                str(exc)
            ) from exc

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise InvalidYoutubeUrlError(
                "URL must use http or https"
            )

        if host not in YOUTUBE_HOSTS:
            raise InvalidYoutubeUrlError(
                f"Unsupported YouTube host: {host}"
            )

    @staticmethod
    def _map_download_error(
        exc: DownloadError,
    ) -> YoutubeExtractorError:
        message = str(exc)

        lowered = message.lower()

        if "private video" in lowered:
            return YoutubePrivateVideoError(
                message
            )

        if (
            "sign in" in lowered
            or "login required" in lowered
            or "confirm your age" in lowered
        ):
            return YoutubeLoginRequiredError(
                message
            )

        if (
            "too many requests" in lowered
            or "429" in lowered
            or "not a bot" in lowered
            or "confirm you're not a bot"
            in lowered
        ):
            return YoutubeRateLimitError(
                message
            )

        if (
            "video unavailable" in lowered
            or "this video is unavailable"
            in lowered
        ):
            return (
                YoutubeVideoUnavailableError(
                    message
                )
            )

        return YoutubeExtractorError(
            message,
            code="YTDLP_DOWNLOAD_ERROR",
        )