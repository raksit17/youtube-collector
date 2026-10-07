class YoutubeExtractorError(Exception):
    """
    Base exception for YouTube extraction errors.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "YOUTUBE_EXTRACTOR_ERROR",
    ):
        super().__init__(message)

        self.message = message
        self.code = code


class InvalidYoutubeUrlError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = "Invalid YouTube URL",
    ):
        super().__init__(
            message,
            code="INVALID_YOUTUBE_URL",
        )


class YoutubeVideoUnavailableError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = "YouTube video is unavailable",
    ):
        super().__init__(
            message,
            code="VIDEO_UNAVAILABLE",
        )


class YoutubePrivateVideoError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = "YouTube video is private",
    ):
        super().__init__(
            message,
            code="PRIVATE_VIDEO",
        )


class YoutubeLoginRequiredError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = "YouTube login is required",
    ):
        super().__init__(
            message,
            code="LOGIN_REQUIRED",
        )


class YoutubeRateLimitError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = (
            "YouTube rate limit or bot detection"
        ),
    ):
        super().__init__(
            message,
            code="RATE_LIMITED",
        )


class YoutubeChatReplayError(
    YoutubeExtractorError
):
    def __init__(
        self,
        message: str = (
            "Failed to extract YouTube live chat replay"
        ),
    ):
        super().__init__(
            message,
            code="CHAT_REPLAY_EXTRACTION_ERROR",
        )
