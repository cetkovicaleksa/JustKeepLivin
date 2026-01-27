from flask import Flask

extensions = tuple()

def init_extensions(app: Flask):
    for ext in extensions:
        ext(app)
