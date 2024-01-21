__all__ = ["CaptureFileConfig"]
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class CaptureFileConfig(BaseModel):
    hash_algorithm: Optional[str] = Field(
        default=None,
        alias="hash",
    )
    copy_: bool = Field(default=False, alias="copy")
    move: bool = False

    @model_validator(mode="after")  # type: ignore
    @classmethod
    def exclusive_copy_move(cls, model: "CaptureFileConfig") -> "CaptureFileConfig":
        if model.copy_ and model.move:
            msg = "Only one of `copy` or `move` can be set"
            raise ValueError(msg)
        return model
