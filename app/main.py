from fastapi import FastAPI

from app.api.youtube import router as youtube_router


app = FastAPI(
    title="YouTube Collector API",
    description="YouTube data collector using yt-dlp",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "name": "YouTube Collector API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


app.include_router(
    youtube_router,
    prefix="/api/v1/youtube",
    tags=["YouTube"],
)