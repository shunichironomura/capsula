import click


@click.group()
def main() -> None:
    click.echo("main")


@main.command()
def freeze() -> None:
    click.echo("freeze")
