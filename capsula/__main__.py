import tomllib
from pathlib import Path

import click

from capsula.freeze import FreezeConfig


@click.group()
@click.option(
    "--directory",
    "-C",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
    help="The working directory to use. Defaults to the current directory.",
)
@click.pass_context
def main(ctx: click.Context, directory: Path) -> None:
    click.echo("main")
    ctx.ensure_object(dict)

    ctx.obj["directory"] = directory
    capsula_config_path: Path = ctx.obj["directory"] / "capsula.toml"
    with capsula_config_path.open("rb") as capsula_config_file:
        capsula_config = tomllib.load(capsula_config_file)

    ctx.obj["capsula_config"] = capsula_config


@main.command()
@click.pass_context
def freeze(ctx: click.Context) -> None:
    """Freeze the environment into a file."""
    click.echo("freeze")
    click.echo(f"directory: {ctx.obj['directory']}")

    capsula_freeze_config = FreezeConfig(**ctx.obj["capsula_config"]["freeze"])
    click.echo(f"capsula_freeze_config: {capsula_freeze_config}")
