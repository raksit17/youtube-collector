import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError

from app.extractor.exceptions import (
    YoutubeChatReplayError,
)
from app.extractor.options import build_options


class ChatReplayExtractor:
    """
    Download a finished YouTube live chat replay
    using yt-dlp's live_chat subtitle downloader.

    This does not download video or audio.

    yt-dlp stores replay actions as JSON Lines:
    one YouTube chat action per line.
    """

    def extract(
        self,
        url: str,
    ) -> list[dict[str, Any]]:
        try:
            with TemporaryDirectory(
                prefix="youtube-chat-replay-"
            ) as temp_dir:
                output_dir = Path(temp_dir)

                options = build_options(
                    include_comments=False,
                    flat=False,
                )

                options.update(
                    {
                        "skip_download": True,
                        "writesubtitles": True,
                        "writeautomaticsub": False,
                        "subtitleslangs": [
                            "live_chat"
                        ],
                        "subtitlesformat": "json",
                        "outtmpl": str(
                            output_dir
                            / "%(id)s.%(ext)s"
                        ),
                        "ignoreerrors": False,
                    }
                )

                with yt_dlp.YoutubeDL(
                    options
                ) as ydl:
                    info = ydl.extract_info(
                        url,
                        download=True,
                    )

                    if info is None:
                        raise YoutubeChatReplayError(
                            "yt-dlp returned no data "
                            "while extracting chat replay"
                        )

                replay_file = (
                    self._find_replay_file(
                        output_dir
                    )
                )

                if replay_file is None:
                    return []

                return self._read_json_lines(
                    replay_file
                )

        except YoutubeChatReplayError:
            raise

        except DownloadError as exc:
            raise YoutubeChatReplayError(
                str(exc)
            ) from exc

        except Exception as exc:
            raise YoutubeChatReplayError(
                str(exc)
            ) from exc

    @staticmethod
    def _find_replay_file(
        output_dir: Path,
    ) -> Path | None:
        candidates = [
            path
            for path in output_dir.rglob("*")
            if (
                path.is_file()
                and ".live_chat." in path.name
                and not path.name.endswith(
                    ".part"
                )
            )
        ]

        if not candidates:
            return None

        json_candidates = [
            path
            for path in candidates
            if path.suffix.lower() == ".json"
        ]

        if json_candidates:
            return json_candidates[0]

        return candidates[0]

    @staticmethod
    def _read_json_lines(
        path: Path,
    ) -> list[dict[str, Any]]:
        records: list[
            dict[str, Any]
        ] = []

        with path.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    value = json.loads(
                        line
                    )
                except json.JSONDecodeError:
                    continue

                if isinstance(value, dict):
                    records.append(value)

        return records
