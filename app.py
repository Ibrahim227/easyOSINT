"""Contains the Flask part of the project
    Import required Module/Lib
"""
from flask import Flask, render_template, redirect, url_for, make_response, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
