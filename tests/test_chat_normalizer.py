from app.normalizer.chat import (
    normalize_chat_replay,
)


def test_normalize_text_message():
    records = [
        {
            "replayChatItemAction": {
                "videoOffsetTimeMsec": "420310",
                "actions": [
                    {
                        "addChatItemAction": {
                            "item": {
                                "liveChatTextMessageRenderer": {
                                    "id": "msg-1",
                                    "authorName": {
                                        "simpleText": "Viewer A"
                                    },
                                    "authorExternalChannelId": "UC_A",
                                    "timestampUsec": "123456789",
                                    "message": {
                                        "runs": [
                                            {
                                                "text": "LET'S "
                                            },
                                            {
                                                "text": "GOOOO"
                                            },
                                        ]
                                    },
                                }
                            }
                        }
                    }
                ],
            }
        }
    ]

    messages = normalize_chat_replay(
        records
    )

    assert len(messages) == 1

    message = messages[0]

    assert message["id"] == "msg-1"
    assert message["timestamp"] == 420.31
    assert (
        message["timestamp_usec"]
        == 123456789
    )
    assert message["author"] == "Viewer A"
    assert message["author_id"] == "UC_A"
    assert message["message"] == "LET'S GOOOO"
    assert message["type"] == "text"


def test_normalize_superchat_and_badges():
    records = [
        {
            "replayChatItemAction": {
                "videoOffsetTimeMsec": "5000",
                "actions": [
                    {
                        "addChatItemAction": {
                            "item": {
                                "liveChatPaidMessageRenderer": {
                                    "id": "paid-1",
                                    "authorName": {
                                        "simpleText": "Supporter"
                                    },
                                    "message": {
                                        "runs": [
                                            {
                                                "text": "Congrats!"
                                            }
                                        ]
                                    },
                                    "purchaseAmountText": {
                                        "simpleText": "$10.00"
                                    },
                                    "authorBadges": [
                                        {
                                            "liveChatAuthorBadgeRenderer": {
                                                "tooltip": "Member"
                                            }
                                        },
                                        {
                                            "liveChatAuthorBadgeRenderer": {
                                                "tooltip": "Moderator",
                                                "icon": {
                                                    "iconType": "MODERATOR"
                                                },
                                            }
                                        },
                                    ],
                                }
                            }
                        }
                    }
                ],
            }
        }
    ]

    messages = normalize_chat_replay(
        records
    )

    assert len(messages) == 1

    message = messages[0]

    assert message["type"] == "superchat"
    assert message["amount"] == "$10.00"
    assert message["is_member"] is True
    assert message["is_moderator"] is True
