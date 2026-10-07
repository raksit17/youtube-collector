from typing import Any


def normalize_json3_transcript(
    raw: dict[str, Any],
) -> list[dict[str, Any]]:

    result: list[dict[str, Any]] = []

    for event in raw.get(
        "events",
        [],
    ):
        if not isinstance(event, dict):
            continue

        segments = event.get("segs")

        if not isinstance(
            segments,
            list,
        ):
            continue

        event_start_ms = event.get(
            "tStartMs",
            0,
        )

        duration_ms = event.get(
            "dDurationMs",
            0,
        )

        text_parts: list[str] = []
        words: list[dict[str, Any]] = []

        for segment in segments:
            if not isinstance(
                segment,
                dict,
            ):
                continue

            text = segment.get("utf8")

            if (
                not text
                or not text.strip()
            ):
                continue

            offset_ms = segment.get(
                "tOffsetMs",
                0,
            )

            text_parts.append(text)

            words.append(
                {
                    "start": (
                        event_start_ms
                        + offset_ms
                    ) / 1000,
                    "text": text,
                }
            )

        text = "".join(
            text_parts
        ).strip()

        if not text:
            continue

        result.append(
            {
                "start": (
                    event_start_ms
                    / 1000
                ),

                "end": (
                    event_start_ms
                    + duration_ms
                ) / 1000,

                "duration": (
                    duration_ms
                    / 1000
                ),

                "text": text,

                "words": words,
            }
        )

    return result