from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CaptureFileConfig(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"] | None = None
    copy_: bool = Field(default=False, alias="copy")
    move: bool = False

    @model_validator(mode="after")  # type: ignore
    def exclusive_copy_move(cls, model: CaptureFileConfig) -> CaptureFileConfig:  # noqa: N805
        if model.copy_ and model.move:
            msg = "Only one of copy or move can be true"
            raise ValueError(msg)
        return model
