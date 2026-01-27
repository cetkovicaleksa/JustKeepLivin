import click
from .app import create_app

# NOTE: Probably should have a single command with options

@click.group()
def main():
    pass

@main.command()
@click.option('-h-', '--host', default = "0.0.0.0")
@click.option('-p', '--port', default = 5000)
def debug(host: str, port: int):
    app = create_app()
    app.run(debug=True, host=host, port=port)
