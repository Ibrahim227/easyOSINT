"""Contains the Flask part of the project
    Import required Module/Lib
"""
# Import python standard lib
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, render_template, redirect, url_for
from flask import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests


app = Flask(__name__)
app.secret_key = "supersekrit"


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/login", methods=["GET"])
def login():
    return render_template('login.html')


@app.route("/signup", methods=["GET"])
def signup():
    return render_template('signup.html')


@app.route("/home", methods=["GET"])
def home():
    return render_template('index.html')


# @app.route("/google_login")
# def google_login():
#     if not google.authorized:
#         return redirect(url_for("google.login"))
#     resp = google.get("/plus/v1/people/me")
#     assert resp.ok, resp.text
#     user_info = resp.json()
#     user = User(user_info["id"])
#     login_user(user)
#     return redirect(url_for("index"))


# GitHub OAuth blueprint
blueprint = make_github_blueprint(
    client_id="my-key-here",  # Replace with your GitHub client ID
    client_secret="my-secret-here",  # Replace with your GitHub client secret
)
app.register_blueprint(blueprint, url_prefix="/login")


@app.route("/github_login")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok, resp.text
    return "You are @{login} on GitHub".format(login=resp.json()["login"])


@app.route('/history', methods=["GET"])
def history():
    return render_template('history.html')


@app.route("/success", methods=["GET"])
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
