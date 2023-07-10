from __future__ import annotations

__all__ = ["SlackNotifier"]

import logging
import os.path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .base import NotifierBase

logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]


class SlackNotifier(NotifierBase):
    def __init__(self, *, channel: str, token: str = SLACK_BOT_TOKEN, thread: bool = False) -> None:
        self.channel = channel
        self.client = WebClient(token)
        self.thread_ts: str | None = None

    def notify(self, message: str):
        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=message,
            )
        except SlackApiError as e:
            logger.exception(f"Got an error: {e.response['error']}")


if __name__ == "__main__":
    # slack = SlackNotifier(channel="capsula-notification")
    # slack.notify("Hello, world!")
    from pathlib import Path
    from textwrap import dedent

    message = """\
    Initial comment: This is a file upload test.
    Is *markdown* _supported_?

    This is a new paragraph.

    This is a list:

    * Item 1
    * Item 2
    * Item 3
    """
    message = dedent(message)
    print(message)

    client = WebClient(SLACK_BOT_TOKEN)
    client.files_upload_v2(
        file=str(Path(__file__).parents[2] / "examples" / "pi_dec.png"),
        title="Title: This is a file upload test.",
        channel="CHANNEL_ID",
        initial_comment=message,
    )
