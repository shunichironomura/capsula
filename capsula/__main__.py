from pathlib import Path

import click


@click.group()
@click.option(
    "--directory",
    "-C",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
)
@click.pass_context
def main(ctx: click.Context, directory: Path) -> None:
    click.echo("main")
    ctx.ensure_object(dict)

    ctx.obj["directory"] = directory


@main.command()
@click.pass_context
def freeze(ctx: click.Context) -> None:
    """Freeze the environment into a file."""
    click.echo("freeze")
    click.echo(f"directory: {ctx.obj['directory']}")
