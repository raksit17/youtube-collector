from typing import Any


RENDERER_TYPES = {
    "liveChatTextMessageRenderer": "text",
    "liveChatPaidMessageRenderer": "superchat",
    "liveChatMembershipItemRenderer": "membership",
    "liveChatPaidStickerRenderer": "sticker",
}


def normalize_chat_replay(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert yt-dlp live chat replay JSON Lines
    into application-defined chat messages.

    The yt-dlp downloader writes one YouTube
    action per line. Replay messages are usually
    wrapped in replayChatItemAction, which carries
    videoOffsetTimeMsec.
    """

    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for record in records:
        if not isinstance(record, dict):
            continue

        _walk_action(
            record,
            video_offset_ms=None,
            result=result,
            seen=seen,
        )

    result.sort(
        key=lambda item: (
            item.get("timestamp")
            if item.get("timestamp")
            is not None
            else float("inf")
        )
    )

    return result


def _walk_action(
    node: Any,
    *,
    video_offset_ms: int | None,
    result: list[dict[str, Any]],
    seen: set[tuple[Any, ...]],
) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_action(
                item,
                video_offset_ms=video_offset_ms,
                result=result,
                seen=seen,
            )

        return

    if not isinstance(node, dict):
        return

    replay = node.get(
        "replayChatItemAction"
    )

    if isinstance(replay, dict):
        replay_offset = _to_int(
            replay.get(
                "videoOffsetTimeMsec"
            )
        )

        if replay_offset is None:
            replay_offset = (
                video_offset_ms
            )

        _walk_action(
            replay.get("actions") or [],
            video_offset_ms=replay_offset,
            result=result,
            seen=seen,
        )

        return

    for (
        renderer_name,
        message_type,
    ) in RENDERER_TYPES.items():
        renderer = node.get(
            renderer_name
        )

        if not isinstance(
            renderer,
            dict,
        ):
            continue

        message = _normalize_renderer(
            renderer,
            message_type=message_type,
            video_offset_ms=(
                video_offset_ms
            ),
        )

        if message is None:
            return

        dedupe_key = _dedupe_key(
            message
        )

        if dedupe_key in seen:
            return

        seen.add(dedupe_key)
        result.append(message)

        return

    for value in node.values():
        _walk_action(
            value,
            video_offset_ms=video_offset_ms,
            result=result,
            seen=seen,
        )


def _normalize_renderer(
    renderer: dict[str, Any],
    *,
    message_type: str,
    video_offset_ms: int | None,
) -> dict[str, Any] | None:
    message_id = renderer.get("id")

    author = _text_value(
        renderer.get("authorName")
    )

    author_id = renderer.get(
        "authorExternalChannelId"
    )

    timestamp_usec = _to_int(
        renderer.get("timestampUsec")
    )

    message = _first_text(
        renderer.get("message"),
        renderer.get("headerSubtext"),
        renderer.get("primaryText"),
        renderer.get("subtext"),
    )

    if (
        not message
        and message_type == "sticker"
    ):
        message = _sticker_text(
            renderer.get("sticker")
        )

    amount = _text_value(
        renderer.get(
            "purchaseAmountText"
        )
    )

    badges = _badge_flags(
        renderer.get("authorBadges")
    )

    timestamp = None

    if video_offset_ms is not None:
        timestamp = (
            video_offset_ms / 1000
        )

    if (
        message is None
        and amount is None
        and author is None
    ):
        return None

    return {
        "id": (
            str(message_id)
            if message_id is not None
            else None
        ),
        "timestamp": timestamp,
        "timestamp_usec": timestamp_usec,
        "author": author,
        "author_id": (
            str(author_id)
            if author_id is not None
            else None
        ),
        "message": message,
        "type": message_type,
        "amount": amount,
        "is_member": (
            badges["is_member"]
            or message_type
            == "membership"
        ),
        "is_moderator": badges[
            "is_moderator"
        ],
        "is_owner": badges[
            "is_owner"
        ],
    }


def _first_text(
    *values: Any,
) -> str | None:
    for value in values:
        text = _text_value(value)

        if text:
            return text

    return None


def _text_value(
    value: Any,
) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None

    if not isinstance(value, dict):
        return None

    simple_text = value.get(
        "simpleText"
    )

    if isinstance(simple_text, str):
        text = simple_text.strip()

        if text:
            return text

    runs = value.get("runs")

    if not isinstance(runs, list):
        return None

    parts: list[str] = []

    for run in runs:
        if not isinstance(run, dict):
            continue

        text = run.get("text")

        if isinstance(text, str):
            parts.append(text)
            continue

        emoji = run.get("emoji")

        if not isinstance(
            emoji,
            dict,
        ):
            continue

        shortcuts = emoji.get(
            "shortcuts"
        )

        if (
            isinstance(shortcuts, list)
            and shortcuts
            and isinstance(
                shortcuts[0],
                str,
            )
        ):
            parts.append(
                shortcuts[0]
            )
            continue

        accessibility = (
            emoji.get("image", {})
            .get(
                "accessibility",
                {},
            )
            .get(
                "accessibilityData",
                {},
            )
            .get("label")
        )

        if isinstance(
            accessibility,
            str,
        ):
            parts.append(
                accessibility
            )

    text = "".join(parts).strip()

    return text or None


def _sticker_text(
    sticker: Any,
) -> str | None:
    if not isinstance(sticker, dict):
        return None

    label = (
        sticker.get(
            "accessibility",
            {},
        )
        .get(
            "accessibilityData",
            {},
        )
        .get("label")
    )

    if not isinstance(label, str):
        return None

    label = label.strip()

    return label or None


def _badge_flags(
    badges: Any,
) -> dict[str, bool]:
    result = {
        "is_member": False,
        "is_moderator": False,
        "is_owner": False,
    }

    if not isinstance(badges, list):
        return result

    for badge in badges:
        if not isinstance(
            badge,
            dict,
        ):
            continue

        renderer = badge.get(
            "liveChatAuthorBadgeRenderer"
        )

        if not isinstance(
            renderer,
            dict,
        ):
            continue

        tooltip = str(
            renderer.get(
                "tooltip",
                "",
            )
        ).lower()

        icon_type = str(
            renderer.get(
                "icon",
                {},
            ).get(
                "iconType",
                "",
            )
        ).upper()

        if (
            "member" in tooltip
            or icon_type == "MEMBER"
        ):
            result[
                "is_member"
            ] = True

        if (
            "moderator" in tooltip
            or icon_type
            == "MODERATOR"
        ):
            result[
                "is_moderator"
            ] = True

        if (
            "owner" in tooltip
            or icon_type == "OWNER"
        ):
            result[
                "is_owner"
            ] = True

    return result


def _dedupe_key(
    message: dict[str, Any],
) -> tuple[Any, ...]:
    message_id = message.get("id")

    if message_id:
        return (
            "id",
            message_id,
        )

    return (
        message.get("timestamp"),
        message.get(
            "timestamp_usec"
        ),
        message.get("author_id"),
        message.get("type"),
        message.get("message"),
        message.get("amount"),
    )


def _to_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None
