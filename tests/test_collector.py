from app.collector.collector import YoutubeCollector


class FakeYoutubeExtractor:
    def extract(
        self,
        url: str,
        *,
        include_comments: bool = False,
        flat: bool = False,
    ):
        return {
            "id": "video123",
            "webpage_url": url,
            "title": "Replay test",
            "was_live": True,
            "live_status": "was_live",
            "subtitles": {
                "live_chat": [
                    {
                        "ext": "json",
                        "url": url,
                    }
                ]
            },
            "automatic_captions": {},
        }


class FakeSubtitleExtractor:
    def extract_json3(self, url: str):
        return {}


class FakeChatReplayExtractor:
    def __init__(self):
        self.called = False

    def extract(self, url: str):
        self.called = True

        return [
            {
                "replayChatItemAction": {
                    "videoOffsetTimeMsec": "123400",
                    "actions": [
                        {
                            "addChatItemAction": {
                                "item": {
                                    "liveChatTextMessageRenderer": {
                                        "id": "chat1",
                                        "authorName": {
                                            "simpleText": "Viewer"
                                        },
                                        "authorExternalChannelId": "UC123",
                                        "timestampUsec": "1000000",
                                        "message": {
                                            "runs": [
                                                {
                                                    "text": "Hello"
                                                }
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


def test_collect_video_includes_chat_replay():
    chat_extractor = (
        FakeChatReplayExtractor()
    )

    collector = YoutubeCollector(
        extractor=FakeYoutubeExtractor(),
        subtitle_extractor=(
            FakeSubtitleExtractor()
        ),
        chat_replay_extractor=(
            chat_extractor
        ),
    )

    data = collector.collect_video(
        "https://www.youtube.com/watch?v=video123",
        include_subtitles=False,
        include_chat_replay=True,
    )

    assert chat_extractor.called is True

    assert data["chat_replay"][
        "count"
    ] == 1

    message = data[
        "chat_replay"
    ]["messages"][0]

    assert message["id"] == "chat1"
    assert message["timestamp"] == 123.4
    assert message["author"] == "Viewer"
    assert message["message"] == "Hello"


def test_collect_video_skips_chat_replay_by_default():
    chat_extractor = (
        FakeChatReplayExtractor()
    )

    collector = YoutubeCollector(
        extractor=FakeYoutubeExtractor(),
        subtitle_extractor=(
            FakeSubtitleExtractor()
        ),
        chat_replay_extractor=(
            chat_extractor
        ),
    )

    data = collector.collect_video(
        "https://www.youtube.com/watch?v=video123",
        include_subtitles=False,
    )

    assert chat_extractor.called is False
    assert data["chat_replay"] is None
