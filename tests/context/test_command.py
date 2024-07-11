import subprocess
from pathlib import Path

import pytest

from capsula._context._command import CommandContext


@pytest.fixture
def command_context(tmp_path: Path) -> CommandContext:
    return CommandContext(
        command="echo hello",
        cwd=tmp_path,
        check=True,
        abort_on_error=True,
    )


def test_command_context_encapsulate(command_context: CommandContext, tmp_path: Path) -> None:
    data = command_context.encapsulate()
    assert data["command"] == "echo hello"
    assert data["cwd"] == tmp_path
    assert data["returncode"] == 0
    assert data["stdout"] == "hello\n", f"stdout: {data['stdout']!r}"
    assert data["stderr"] == "", f"stderr: {data['stderr']!r}"


def test_command_context_default_key(command_context: CommandContext) -> None:
    key = command_context.default_key()
    assert key == ("command", "echo hello")


@pytest.fixture
def command_context_fail(tmp_path: Path) -> CommandContext:
    return CommandContext(
        command="exit 1",
        cwd=tmp_path,
        check=True,
        abort_on_error=True,
    )


def test_command_context_encapsulate_fail(command_context_fail: CommandContext) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        command_context_fail.encapsulate()
