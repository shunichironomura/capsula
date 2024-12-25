from __future__ import annotations

import logging
import shlex
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from random import choices
from string import ascii_letters, digits
from typing import Annotated, Any, Literal, NoReturn, Optional

import typer
from rich.console import Console

import capsula

from ._config import load_config
from ._context import ContextBase
from ._run import (
    CapsuleParams,
    Run,
    RunDtoCommand,
    default_run_name_factory,
    get_default_vault_dir,
    get_project_root,
)
from ._utils import get_default_config_path, search_for_project_root

logger = logging.getLogger(__name__)

app = typer.Typer()
console = Console()
err_console = Console(stderr=True)


@app.command()
def run(
    command: Annotated[list[str], typer.Argument(help="Command to run", show_default=False)],
    run_name: Annotated[
        Optional[str],
        typer.Option(
            ...,
            help="Run name. Make sure it is unique. If not provided, it will be generated randomly.",
        ),
    ] = None,
    vault_dir: Annotated[
        Optional[Path],
        typer.Option(
            ...,
            help="Vault directory. If not provided, it will be set to the default value.",
        ),
    ] = None,
    ignore_config: Annotated[
        bool,
        typer.Option(
            ...,
            help="Ignore the configuration file and run the command directly.",
        ),
    ] = False,
    config_path: Annotated[
        Optional[Path],
        typer.Option(
            ...,
            help="Path to the Capsula configuration file.",
        ),
    ] = None,
) -> NoReturn:
    err_console.print(f"Running command '{shlex.join(command)}'...")
    run_dto = RunDtoCommand(
        run_name_factory=default_run_name_factory if run_name is None else lambda _x, _y, _z: run_name,
        vault_dir=vault_dir,
        command=tuple(command),
    )

    if not ignore_config:
        config = load_config(get_default_config_path() if config_path is None else config_path)
        for phase in ("pre", "in", "post"):
            phase_key = f"{phase}-run"
            if phase_key not in config:
                continue
            for context in reversed(config[phase_key].get("contexts", [])):  # type: ignore[literal-required]
                assert phase in {"pre", "post"}, f"Invalid phase for context: {phase}"
                run_dto.add_context(context, mode=phase, append_left=True)  # type: ignore[arg-type]
            for watcher in reversed(config[phase_key].get("watchers", [])):  # type: ignore[literal-required]
                assert phase == "in", "Watcher can only be added to the in-run phase."
                # No need to set append_left=True here, as watchers are added as the outermost context manager
                run_dto.add_watcher(watcher, append_left=False)
            for reporter in reversed(config[phase_key].get("reporters", [])):  # type: ignore[literal-required]
                assert phase in {"pre", "in", "post"}, f"Invalid phase for reporter: {phase}"
                run_dto.add_reporter(reporter, mode=phase, append_left=True)

        run_dto.vault_dir = config["vault-dir"] if run_dto.vault_dir is None else run_dto.vault_dir

    # Set the vault directory if it is not set by the config file
    if run_dto.vault_dir is None:
        project_root = search_for_project_root(Path.cwd())
        run_dto.vault_dir = project_root / "vault"

    run: Run[Any, Any] = Run(run_dto)
    result, params = run.exec_command()
    console.print(result.stdout, end="")
    err_console.print(result.stderr, end="")
    err_console.print(f"Run directory: {params.run_dir}")
    err_console.print(f"Command exited with code {result.returncode}")

    raise typer.Exit(result.returncode)


class _PhaseForEncapsulate(str, Enum):
    pre = "pre"
    post = "post"


@app.command()
def enc(
    phase: Annotated[
        _PhaseForEncapsulate,
        typer.Option(..., "--phase", "-p", help="Which phase in the configuration to use for the encapsulation."),
    ] = _PhaseForEncapsulate.pre,
) -> NoReturn:
    typer.echo("Encapsulating...")
    config = load_config(get_default_config_path())
    enc = capsula.Encapsulator()
    phase_key: Literal["pre-run", "post-run"] = f"{phase.value}-run"  # type: ignore[assignment]
    contexts = config[phase_key]["contexts"]
    reporters = config[phase_key]["reporters"]

    exec_info = None

    vault_dir = get_default_vault_dir(exec_info)

    run_name = default_run_name_factory(
        exec_info,
        "".join(choices(ascii_letters + digits, k=4)),
        datetime.now(timezone.utc),
    )

    run_dir = vault_dir / run_name
    run_dir.mkdir(exist_ok=True, parents=True)
    params = CapsuleParams(
        exec_info=exec_info,
        run_name=run_name,
        run_dir=run_dir,
        phase=phase.value,
        project_root=get_project_root(exec_info),
    )

    for context in contexts:
        enc.add_context(context if isinstance(context, ContextBase) else context(params))

    capsule = enc.encapsulate()
    for reporter in reporters:
        (reporter if isinstance(reporter, capsula.ReporterBase) else reporter(params)).report(capsule)

    raise typer.Exit
