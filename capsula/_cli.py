from enum import Enum
from typing import Literal, NoReturn

import typer

import capsula

from ._backport import Annotated
from ._config import load_config
from ._context import ContextBase
from ._run import CapsuleParams, generate_default_run_dir, get_project_root
from ._utils import get_default_config_path

app = typer.Typer()


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
    config = load_config(get_default_config_path())
    enc = capsula.Encapsulator()
    phase_key: Literal["pre-run", "post-run"] = f"{phase.value}-run"  # type: ignore[assignment]
    contexts = config[phase_key]["contexts"]
    reporters = config[phase_key]["reporters"]

    exec_info = None
    run_dir = generate_default_run_dir(exec_info=exec_info)
    run_dir.mkdir(exist_ok=True, parents=True)
    params = CapsuleParams(
        exec_info=exec_info,
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
