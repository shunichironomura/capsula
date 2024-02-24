from pathlib import Path
from typing import Annotated, Literal, NoReturn

import typer

import capsula

from ._config import load_config
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


@app.command()
def enc(
    phase: Annotated[
        Literal["pre", "post"],
        typer.Option(..., "--phase", "-p", help="The phase to encapsulate."),
    ] = "pre",
) -> NoReturn:
    typer.echo("Encapsulating...")
    config = load_config(_get_default_config_path())
    enc = capsula.Encapsulator()
    phase_key: Literal["pre-run", "post-run"] = f"{phase}-run"  # type: ignore[assignment]
    contexts = config[phase_key]["context"]
    reporters = config[phase_key]["reporter"]

    for context in contexts:
        enc.add_context(context)

    raise typer.Exit
