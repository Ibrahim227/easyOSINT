"""Contains the Flask part of the project
    Import required Module/Lib
"""
import os
# Import python standard lib
import sqlite3
from uuid import uuid4

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
# Third-party libraries
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

# Internal imports
from db import init_db_command, get_db
from user import User
from search import SearchModel

# load env variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

oauth = OAuth(app)

app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")
app.config['GITHUB_CLIENT_ID'] = os.getenv("GITHUB_CLIENT_ID")
app.config['GITHUB_CLIENT_SECRET'] = os.getenv("GITHUB_CLIENT_SECRET")

google = oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    # This is only needed if using openId to fetch user info
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
    claims_options={
        'iss': {'values': ['https://accounts.google.com']}
    },
)

github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
    verify=False,
)
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


# Google login route

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = google.authorize_access_token()
        id_token = token.get('id_token')
        resp = google.get('userinfo').json()
        if token['id_token']['iss'] != 'https://accounts.google.com':
            raise Exception('Invalid Issuer')

        print(f"\n{resp}\n")
        return "You are successfully signed in using google"
    except Exception as e:
        print(f"Error: {e}")
        return "Authorization failed. Please try again."


@app.route('/login/github')
def github_login():
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)


@app.route('/login/github/authorize')
def github_authorize():
    try:
        token = github.authorize_access_token()
        resp = github.get('user').json()
        print(f"\n{resp}\n")
        return "You are successfully signed in using github"
    except Exception as e:
        print(f"Error: {e}")
        return "Authorization failed. Please try again."


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


# search route
@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')  # Get the search query from the form
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    # Instantiate the search model and perform the search
    search_model = SearchModel(query)
    results = search_model.perform_search()

    if 'error' in results:
        return jsonify(results), 500

    # Return the search results as JSON
    return jsonify(results), 200


# Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('name', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
