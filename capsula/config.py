import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from capsula.file import CaptureFileConfig

if sys.version_info < (3, 11):
    from datetime import timezone as _timezone

    UTC = _timezone.utc

else:
    from datetime import UTC


class GitConfig(BaseModel):
    repositories: dict[str, Path] = Field(default_factory=dict)


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class CaptureConfig(BaseModel):
    """Configuration for the capture command."""

    model_config = ConfigDict(
        alias_generator=to_hyphen_case,
        populate_by_name=True,
        extra="forbid",
    )

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True

    include_cpu: bool = True

    pre_capture_commands: list[str] = Field(default_factory=list)

    environment_variables: list[str] = Field(default_factory=list)

    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)

    git: GitConfig = Field(default_factory=GitConfig)


class MonitorItemConfig(BaseModel):
    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)


class MonitorConfig(BaseModel):
    items: dict[str, MonitorItemConfig] = Field(default_factory=dict, alias="item")


class CapsulaConfig(BaseModel):
    vault_directory: Path
    capsule_template: str

    capture: CaptureConfig
    monitor: MonitorConfig

    _capsule_directory: Path | None = None
    _root_directory: Path | None = None

    @property
    def capsule(self) -> Path:
        if self._capsule_directory is None:
            self._capsule_directory = (
                self.root_directory
                / self.vault_directory
                / datetime.now(UTC)
                .astimezone()
                .strftime(
                    self.capsule_template,
                )
            )
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
