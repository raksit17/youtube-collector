from enum import StrEnum


class CollectorType(StrEnum):
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    SEARCH = "search"
    UNKNOWN = "unknown"


class CollectorProvider(StrEnum):
    YOUTUBE = "youtube"


class CollectorEngine(StrEnum):
    YTDLP = "yt-dlp"