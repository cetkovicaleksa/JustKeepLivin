from flask.cli import FlaskGroup
import click
from .app import create_app

@click.group(cls=FlaskGroup, create_app=create_app)
def main():
    pass
