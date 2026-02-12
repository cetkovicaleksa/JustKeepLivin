from flask import Blueprint, request, Response
from flask import render_template

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html', content="Home works!")
