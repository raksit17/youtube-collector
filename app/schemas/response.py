from typing import Any, Literal

from pydantic import BaseModel, Field


class ChannelData(BaseModel):
    external_id: str | None = None
    name: str | None = None
    url: str | None = None
    followers: int | None = None


class PublishedData(BaseModel):
    upload_date: str | None = None
    timestamp: int | float | None = None
    release_timestamp: int | float | None = None


class StatsData(BaseModel):
    views: int | None = None
    likes: int | None = None
    comments: int | None = None


class MediaData(BaseModel):
    duration: float | None = None
    duration_string: str | None = None

    thumbnail: str | None = None

    width: int | None = None
    height: int | None = None
    fps: float | None = None


class LiveData(BaseModel):
    status: str | None = None

    is_live: bool | None = None
    was_live: bool | None = None

    concurrent_viewers: int | None = None


class MetadataData(BaseModel):
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)

    language: str | None = None
    availability: str | None = None

    age_limit: int | None = None


class ChapterData(BaseModel):
    title: str | None = None

    start_time: float | None = None
    end_time: float | None = None


class FormatData(BaseModel):
    id: str | None = None

    ext: str | None = None

    width: int | None = None
    height: int | None = None
    fps: float | None = None

    vcodec: str | None = None
    acodec: str | None = None

    tbr: float | None = None
    vbr: float | None = None
    abr: float | None = None

    filesize: int | None = None

    protocol: str | None = None


class SubtitleFormatData(BaseModel):
    ext: str | None = None
    url: str | None = None

    name: str | None = None


class SubtitleData(BaseModel):
    manual: dict[str, list[SubtitleFormatData]] = Field(
        default_factory=dict
    )

    automatic: dict[str, list[SubtitleFormatData]] = Field(
        default_factory=dict
    )


class VideoData(BaseModel):
    type: Literal["video"] = "video"
    source: Literal["youtube"] = "youtube"

    external_id: str

    url: str | None = None

    title: str | None = None
    description: str | None = None

    channel: ChannelData = Field(
        default_factory=ChannelData
    )

    published: PublishedData = Field(
        default_factory=PublishedData
    )

    stats: StatsData = Field(
        default_factory=StatsData
    )

    media: MediaData = Field(
        default_factory=MediaData
    )

    live: LiveData = Field(
        default_factory=LiveData
    )

    metadata: MetadataData = Field(
        default_factory=MetadataData
    )

    chapters: list[ChapterData] = Field(
        default_factory=list
    )

    subtitles: SubtitleData | None = None

    formats: list[FormatData] | None = None
class PlaylistEntryData(BaseModel):
    external_id: str | None = None

    title: str | None = None
    url: str | None = None

    duration: float | None = None

    view_count: int | None = None

    live_status: str | None = None


class PlaylistData(BaseModel):
    type: Literal["playlist"] = "playlist"
    source: Literal["youtube"] = "youtube"

    external_id: str | None = None

    title: str | None = None
    description: str | None = None

    url: str | None = None

    channel: ChannelData = Field(
        default_factory=ChannelData
    )

    count: int = 0

    entries: list[PlaylistEntryData] = Field(
        default_factory=list
    )
class ChannelResponseData(BaseModel):
    type: Literal["channel"] = "channel"
    source: Literal["youtube"] = "youtube"

    external_id: str | None = None

    name: str | None = None
    description: str | None = None

    url: str | None = None

    followers: int | None = None

    entries: list[PlaylistEntryData] = Field(
        default_factory=list
    )
CollectorData = (
    VideoData
    | PlaylistData
    | ChannelResponseData
)


class CollectResponse(BaseModel):
    success: bool = True

    provider: Literal["youtube"] = "youtube"
    collector: Literal["yt-dlp"] = "yt-dlp"

    type: Literal[
        "video",
        "playlist",
        "channel",
    ]

    data: CollectorData
class ErrorDetail(BaseModel):
    code: str
    message: str

    details: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False

    provider: Literal["youtube"] = "youtube"
    collector: Literal["yt-dlp"] = "yt-dlp"

    error: ErrorDetail
