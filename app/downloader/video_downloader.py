from pathlib import Path
from typing import Any, Callable

import yt_dlp
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from yt_dlp.utils import DownloadError

from app.extractor.options import build_options


class VideoDownloadSettings(BaseSettings):
    enabled: bool = True
    directory: str = (
        r"D:\GitPoom\youtube-highlight-api"
        r"\storage\sources"
    )
    format: str = (
        "bv*[ext=mp4]+ba[ext=m4a]/"
        "b[ext=mp4]"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="VIDEO_DOWNLOAD_",
        case_sensitive=False,
        extra="ignore",
    )


class VideoDownloadError(Exception):
    pass


class YoutubeVideoDownloader:
    """
    Download a YouTube video to the local source
    directory using its external_id as filename.

    Example:
        L5yPy0tvG4U.mp4

    Rules:
    - external_id missing -> skip
    - target already exists -> skip
    - otherwise download -> external_id.mp4
    """

    def __init__(
        self,
        settings: VideoDownloadSettings | None = None,
        ydl_factory: Callable[
            [dict[str, Any]],
            Any,
        ] | None = None,
    ) -> None:
        self.settings = (
            settings
            or VideoDownloadSettings()
        )

        self.ydl_factory = (
            ydl_factory
            or yt_dlp.YoutubeDL
        )

    def ensure_downloaded(
        self,
        *,
        url: str,
        external_id: str | None,
    ) -> Path | None:
        if not self.settings.enabled:
            return None

        if not external_id:
            return None

        output_dir = Path(
            self.settings.directory
        )
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        target = (
            output_dir
            / f"{external_id}.mp4"
        )

        if (
            target.is_file()
            and target.stat().st_size > 0
        ):
            print(
                "[VideoDownloader] "
                f"Already exists: {target}"
            )
            return target

        options = build_options(
            include_comments=False,
            flat=False,
        )

        options.update(
            {
                "skip_download": False,
                "noplaylist": True,
                "format": (
                    self.settings.format
                ),
                "merge_output_format": "mp4",
                "outtmpl": str(target),
                "overwrites": False,
                "continuedl": True,
            }
        )

        try:
            print(
                "[VideoDownloader] "
                f"Downloading {external_id} "
                f"to {target}"
            )

            with self.ydl_factory(
                options
            ) as ydl:
                ydl.download([url])

        except DownloadError as exc:
            raise VideoDownloadError(
                (
                    "Failed to download video "
                    f"{external_id}: {exc}"
                )
            ) from exc

        except Exception as exc:
            raise VideoDownloadError(
                (
                    "Failed to download video "
                    f"{external_id}: {exc}"
                )
            ) from exc

        if not target.is_file():
            raise VideoDownloadError(
                (
                    "yt-dlp completed but target "
                    f"file was not found: {target}"
                )
            )

        print(
            "[VideoDownloader] "
            f"Saved: {target}"
        )

        return target
