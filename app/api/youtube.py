from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from fastapi.concurrency import (
    run_in_threadpool,
)

from app.clients.ingestion_client import (
    IngestionClient,
    IngestionClientError,
)
from app.collector.collector import (
    YoutubeCollector,
)
from app.collector.types import (
    CollectorEngine,
    CollectorProvider,
)
from app.downloader.video_downloader import (
    VideoDownloadError,
    YoutubeVideoDownloader,
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
video_downloader = YoutubeVideoDownloader()
ingestion_client = IngestionClient()


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


async def build_and_forward_response(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the collector envelope, forward it to
    the downstream ingestion API, then return the
    same payload to the original caller.
    """

    payload = build_response(data)

    try:
        await ingestion_client.send(
            payload
        )

    except IngestionClientError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": (
                    "INGESTION_FORWARD_ERROR"
                ),
                "message": str(exc),
            },
        ) from exc

    return payload


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

        return await build_and_forward_response(
            data
        )

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

        try:
            await run_in_threadpool(
                video_downloader.ensure_downloaded,
                url=str(request.url),
                external_id=data.get(
                    "external_id"
                ),
            )
        except VideoDownloadError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": (
                        "VIDEO_DOWNLOAD_ERROR"
                    ),
                    "message": str(exc),
                },
            ) from exc

        return await build_and_forward_response(
            data
        )

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

        return await build_and_forward_response(
            data
        )

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

        return await build_and_forward_response(
            data
        )

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

        return await build_and_forward_response(
            data
        )

    except YoutubeExtractorError as exc:
        handle_extractor_error(exc)
        raise
