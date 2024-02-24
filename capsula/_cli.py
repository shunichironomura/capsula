from typing import NoReturn

import typer

app = typer.Typer()


@app.command()
def run() -> NoReturn:
    typer.echo("Running...")

    raise typer.Exit


@app.command()
def encapsulate() -> NoReturn:
    typer.echo("Encapsulating...")

    raise typer.Exit
