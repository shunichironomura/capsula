from typing import Literal

from pydantic import BaseModel, Field


class CaptureFileConfig(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"] = "sha256"
    copy_: bool = Field(default=True, alias="copy")
