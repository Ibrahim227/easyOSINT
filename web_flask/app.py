"""Contains the Flask part of the project
    Import required Module/Lib
"""
# Import python standard lib
import json
import os
import sqlite3
from uuid import uuid4

# Third-party libraries
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Internal imports
from db import init_db_command, get_db
from user import User

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/history', methods=["GET", "POST"])
def history():
    if request.method == "GET":
        return render_template('history.html')


# Database functions
def get_db():
    conn = sqlite3.connect('sqlite_db')
    conn.row_factory = sqlite3.Row
    return conn


# Route to display signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')

        # Ensure all required fields are present
        if not email or not password or not first_name or not last_name:
            return "Please fill out all fields", 400

        # Hash the password only if it exists
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        name = f'{first_name} {last_name}'

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute('INSERT INTO user (id, name, email, password, profile_pic) VALUES (?, ?, ?, ?, ?)',
                        (str(uuid4()), name, email, hashed_password, 'default_profile_pic.png'))
            conn.commit()
            # Log in the user immediately after successful signup
            session['logged_in'] = True
            session['name'] = name

            return redirect(url_for('index'))  # redirect to homepage

        except sqlite3.IntegrityError:
            return "User already exists"

    return render_template('signup.html')


def get_user_from_db(email):
    db = get_db()
    return db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()


# Route to display login page and handle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve data from the form (request.form)
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate if email and password were submitted
        if not email or not password:
            flash('Please fill out both fields')
            return render_template('login.html')

        # Retrieve user from database
        user = get_user_from_db(email)

        # Check if the user exists and the password is correct
        if user and check_password_hash(user['password'], password):
            # Store user info in session after successful login
            session['logged_in'] = True
            session['name'] = user['name']
            # Handle successful login, store user session
            session['user_id'] = user['id']  # Store user id in session
            return redirect(url_for('index'))  # Redirect to the homepage
        else:
            flash('Invalid email or password!')

    # If GET request or failed login, render the login page again
    return render_template('login.html')


# Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('name', None)
    return redirect(url_for('index'))


load_dotenv()

# GitHub OAuth blueprint setup
github_blueprint = make_github_blueprint(
    client_id=os.getenv("CLIENT_ID"),  # Use environment variables for security
    client_secret=os.getenv("CLIENT_SECRET"),
)
app.register_blueprint(github_blueprint, url_prefix="/github_login")


if __name__ == "__main__":
    app.run(debug=True)
