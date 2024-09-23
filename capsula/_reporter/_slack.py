from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, ClassVar, Literal

from slack_sdk import WebClient

from ._base import ReporterBase

if TYPE_CHECKING:
    from capsula._capsule import Capsule
    from capsula._run import CapsuleParams

logger = logging.getLogger(__name__)


class SlackReporter(ReporterBase):
    """Reporter to send a message to a Slack channel."""

    _run_name_to_thread_ts: ClassVar[dict[str, str]] = {}

    @classmethod
    def builder(
        cls,
        *,
        channel: str,
        token: str,
    ) -> Callable[[CapsuleParams], SlackReporter]:
        def build(params: CapsuleParams) -> SlackReporter:
            return cls(phase=params.phase, channel=channel, token=token, run_name=params.run_name)

        return build

    def __init__(self, *, phase: Literal["pre", "in", "post"], channel: str, token: str, run_name: str) -> None:
        self._phase = phase
        self._channel = channel
        self._token = token
        self._run_name = run_name

    def report(self, capsule: Capsule) -> None:  # noqa: ARG002
        client = WebClient(token=self._token)
        thread_ts = SlackReporter._run_name_to_thread_ts.get(self._run_name)
        if self._phase == "pre":
            message = f"Capsule run `{self._run_name}` started"
            response = client.chat_postMessage(channel=self._channel, text=message, thread_ts=thread_ts)
            SlackReporter._run_name_to_thread_ts[self._run_name] = response["ts"]
        elif self._phase == "in":
            pass  # Do nothing for now
        elif self._phase == "post":
            message = f"Capsule run `{self._run_name}` completed"
            response = client.chat_postMessage(
                channel=self._channel,
                text=message,
                thread_ts=thread_ts,
            )
            SlackReporter._run_name_to_thread_ts[self._run_name] = response["ts"]
