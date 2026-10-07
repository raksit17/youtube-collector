from typing import Any

import httpx


class SubtitleExtractor:
    """
    Download subtitle JSON from a URL
    discovered by yt-dlp.
    """

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        self.timeout = timeout

    def extract_json3(
        self,
        url: str,
    ) -> dict[str, Any]:

        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
        ) as client:

            response = client.get(url)

            response.raise_for_status()

            return response.json()