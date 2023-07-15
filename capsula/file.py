from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CaptureFileConfig(BaseModel):
    hash_algorithm: Optional[Literal["md5", "sha1", "sha256", "sha3"]] = Field(
        default=None,
        alias="hash",
    )
    copy_: bool = Field(default=False, alias="copy")
    move: bool = False

    @model_validator(mode="after")  # type: ignore
    def exclusive_copy_move(cls, model: "CaptureFileConfig") -> "CaptureFileConfig":
        if model.copy_ and model.move:
            msg = "Only one of copy or move can be true"
            raise ValueError(msg)
        return model
