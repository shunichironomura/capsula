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

