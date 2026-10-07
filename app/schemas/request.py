from pydantic import BaseModel, Field, HttpUrl


class CollectRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="YouTube video, playlist, or channel URL",
    )

    include_comments: bool = Field(
        default=False,
        description="Include comments when supported by yt-dlp",
    )

    include_formats: bool = Field(
        default=False,
        description="Include available video/audio formats",
    )

    include_subtitles: bool = Field(
        default=True,
        description="Include manual and automatic subtitles",
    )

    include_chat_replay: bool = Field(
        default=False,
        description=(
            "Include live chat replay for a finished "
            "YouTube livestream when available"
        ),
    )

    flat: bool = Field(
        default=False,
        description=(
            "Use flat extraction. Recommended for "
            "channels and large playlists."
        ),
    )
