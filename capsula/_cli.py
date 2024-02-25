from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, NoReturn

import typer

import capsula

from ._config import load_config
from ._context import ContextBase
from ._run import CapsuleParams, generate_default_run_dir
from .utils import search_for_project_root

app = typer.Typer()


def _get_default_config_path() -> Path:
    config_path = search_for_project_root(Path.cwd()) / "capsula.toml"
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)
    return config_path


@app.command()
def run() -> NoReturn:
    typer.echo("Running...")

    raise typer.Exit


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
    config = load_config(_get_default_config_path())
    enc = capsula.Encapsulator()
    phase_key: Literal["pre-run", "post-run"] = f"{phase.value}-run"  # type: ignore[assignment]
    contexts = config[phase_key]["context"]
    reporters = config[phase_key]["reporter"]

    exec_info = None
    run_dir = generate_default_run_dir(exec_info=exec_info)
    run_dir.mkdir(exist_ok=True, parents=True)
    params = CapsuleParams(exec_info=exec_info, run_dir=run_dir, phase=phase.value)

    for context in contexts:
        enc.add_context(context if isinstance(context, ContextBase) else context(params))

    capsule = enc.encapsulate()
    for reporter in reporters:
        (reporter if isinstance(reporter, capsula.ReporterBase) else reporter(params)).report(capsule)

    raise typer.Exit
