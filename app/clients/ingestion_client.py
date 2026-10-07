import os
from typing import Any

import httpx


class IngestionClientError(Exception):
    """
    Raised when forwarding collected data to
    the downstream ingestion API fails.
    """


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_float(
    name: str,
    default: float,
) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


class IngestionClient:
    """
    Forward normalized collector payloads to
    the downstream ingestion service.

    Default endpoint:
        http://localhost:3000/ingestion/json
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        timeout: float | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.url = (
            url
            or os.getenv(
                "INGESTION_URL",
                (
                    "http://localhost:3000/"
                    "ingestion/json"
                ),
            )
        )

        self.timeout = (
            timeout
            if timeout is not None
            else _env_float(
                "INGESTION_TIMEOUT",
                30.0,
            )
        )

        self.enabled = (
            enabled
            if enabled is not None
            else _env_bool(
                "INGESTION_ENABLED",
                True,
            )
        )

    async def send(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.post(
                    self.url,
                    json=payload,
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            body = (
                exc.response.text[:1000]
                if exc.response is not None
                else ""
            )

            raise IngestionClientError(
                (
                    "Ingestion API returned "
                    f"HTTP {exc.response.status_code}: "
                    f"{body}"
                )
            ) from exc

        except httpx.HTTPError as exc:
            raise IngestionClientError(
                (
                    "Failed to connect to "
                    f"ingestion API at {self.url}: "
                    f"{exc}"
                )
            ) from exc

        if not response.content:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        if isinstance(data, dict):
            return data

        return None
