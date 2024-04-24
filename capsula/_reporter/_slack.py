from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

import orjson
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ._utils import capsule_to_nested_dict, create_default_encoder

if TYPE_CHECKING:
    from capsula._capsule import Capsule
    from capsula._run import CapsuleParams

from ._base import ReporterBase

logger = logging.getLogger(__name__)


class SlackReporter(ReporterBase):
    def __init__(
        self,
        slack_token: str,
        channel: str,
        *,
        default: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.slack_client = WebClient(token=slack_token)
        self.channel = channel
        self.default_for_encoder = create_default_encoder(default)

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Sending capsule to Slack channel: {self.channel}")

        nested_data = capsule_to_nested_dict(capsule)
        json_str = orjson.dumps(nested_data, default=self.default_for_encoder).decode()

        message_color = "good" if not capsule.fails else "danger"

        try:
            self.slack_client.chat_postMessage(
                channel=self.channel,
                attachments=[
                    {
                        "color": message_color,
                        "text": f"Capsule Report:\n```{json_str}```",
                    },
                ],
            )
        except SlackApiError:
            logger.exception("Error posting message to Slack")

    @classmethod
    def default(
        cls,
        slack_token: str,
        channel: str,
    ) -> Callable[[CapsuleParams], SlackReporter]:
        def callback(params: CapsuleParams) -> SlackReporter:
            return cls(
                slack_token=slack_token,
                channel=channel,
            )

        return callback
