import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from capsula.file import CaptureFileConfig
from capsula.globalvars import set_capsule_dir, set_capsule_name

if sys.version_info < (3, 11):
    from datetime import timezone as _timezone

    UTC = _timezone.utc

else:
    from datetime import UTC


def _to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class GitConfig(BaseModel):
    repositories: Dict[str, Path] = Field(default_factory=dict)


class CaptureConfig(BaseModel):
    """Configuration for the capture command."""

    model_config = ConfigDict(
        alias_generator=_to_hyphen_case,
        populate_by_name=True,
        extra="forbid",
    )

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True

    include_cpu: bool = True

    pre_capture_commands: List[str] = Field(default_factory=list)

    environment_variables: List[str] = Field(default_factory=list)

    files: Dict[Path, CaptureFileConfig] = Field(default_factory=dict)

    git: GitConfig = Field(default_factory=GitConfig)


class MonitorItemConfig(BaseModel):
    files: Dict[Path, CaptureFileConfig] = Field(default_factory=dict)


class MonitorConfig(BaseModel):
    capture: bool = True
    items: Dict[str, MonitorItemConfig] = Field(default_factory=dict, alias="item")


class CapsulaConfig(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_hyphen_case,
        populate_by_name=True,
        extra="forbid",
    )

    vault_directory: Path
    capsule_template: str

    capture: CaptureConfig
    monitor: MonitorConfig

    _capsule_directory: Optional[Path] = None
    _root_directory: Optional[Path] = None

    @property
    def capsule(self) -> Path:
        if self._capsule_directory is None:
            capsule_name = (
                datetime.now(UTC)
                .astimezone()
                .strftime(
                    self.capsule_template,
                )
            )
            self._capsule_directory = self.root_directory / self.vault_directory / capsule_name
            if self._capsule_directory.exists():
                msg = f"Directory {self._capsule_directory} already exists"
                raise ValueError(msg)
            set_capsule_dir(self._capsule_directory)
            set_capsule_name(capsule_name)

        return self._capsule_directory

    @property
    def root_directory(self) -> Path:
        if self._root_directory is None:
            msg = "Project root is not set"
            raise ValueError(msg)
        return self._root_directory

    @root_directory.setter
    def root_directory(self, value: Path) -> None:
        self._root_directory = value

    def ensure_capsule_directory_exists(self) -> None:
        self.capsule.mkdir(parents=True, exist_ok=True)
