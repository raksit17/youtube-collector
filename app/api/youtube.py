from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from fastapi.concurrency import (
    run_in_threadpool,
)

from app.collector.collector import (
    YoutubeCollector,
)
from app.collector.types import (
    CollectorEngine,
    CollectorProvider,
)
from app.extractor.exceptions import (
    InvalidYoutubeUrlError,
    YoutubeExtractorError,
    YoutubeLoginRequiredError,
    YoutubePrivateVideoError,
    YoutubeRateLimitError,
    YoutubeVideoUnavailableError,
)
from app.schemas.request import (
    CollectRequest,
)
from app.schemas.response import (
    CollectResponse,
)


router = APIRouter()

collector = YoutubeCollector()


def build_response(
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "success": True,
        "provider": CollectorProvider.YOUTUBE,
        "collector": CollectorEngine.YTDLP,
        "type": data.get(
            "type",
            "video",
        ),
        "data": data,
    }


def handle_extractor_error(
    exc: YoutubeExtractorError,
) -> None:
    if isinstance(
        exc,
        InvalidYoutubeUrlError,
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    if isinstance(
        exc,
        YoutubeVideoUnavailableError,
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    if isinstance(
        exc,
        (
            YoutubePrivateVideoError,
            YoutubeLoginRequiredError,
        ),
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    if isinstance(
        exc,
        YoutubeRateLimitError,
    ):
        raise HTTPException(
            status_code=429,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    raise HTTPException(
        status_code=502,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    ) from exc


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": "youtube",
        "collector": "yt-dlp",
    }


@router.post(
    "/collect",
    response_model=CollectResponse,
)
async def collect(
    request: CollectRequest,
) -> dict[str, Any]:
    try:
        data = await run_in_threadpool(
            collector.collect,
            str(request.url),
            include_comments=(
                request.include_comments
            ),
            include_formats=(
                request.include_formats
            ),
            include_subtitles=(
                request.include_subtitles
            ),
            include_chat_replay=(
                request.include_chat_replay
            ),
            flat=request.flat,
        )

        return build_response(data)

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise


@router.post(
    "/video",
    response_model=CollectResponse,
)
async def collect_video(
    request: CollectRequest,
) -> dict[str, Any]:
    try:
        data = await run_in_threadpool(
            collector.collect_video,
            str(request.url),
            include_comments=(
                request.include_comments
            ),
            include_formats=(
                request.include_formats
            ),
            include_subtitles=(
                request.include_subtitles
            ),
            include_chat_replay=(
                request.include_chat_replay
            ),
        )

        return build_response(data)

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise


@router.post(
    "/channel",
    response_model=CollectResponse,
)
async def collect_channel(
    request: CollectRequest,
) -> dict[str, Any]:
    try:
        data = await run_in_threadpool(
            collector.collect_channel,
            str(request.url),
        )

        return build_response(data)

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise


@router.post(
    "/playlist",
    response_model=CollectResponse,
)
async def collect_playlist(
    request: CollectRequest,
) -> dict[str, Any]:
    try:
        data = await run_in_threadpool(
            collector.collect_playlist,
            str(request.url),
            flat=request.flat,
        )

        return build_response(data)

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise


@router.get(
    "/search",
    response_model=CollectResponse,
)
async def search(
    query: str = Query(
        ...,
        min_length=1,
        description="YouTube search query",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of results"
        ),
    ),
) -> dict[str, Any]:
    try:
        data = await run_in_threadpool(
            collector.search,
            query,
            limit=limit,
        )

        return build_response(data)

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise
