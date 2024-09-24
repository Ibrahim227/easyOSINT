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
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import generate_password_hash, check_password_hash
import requests
# Internal imports
from db import init_db_command, get_db
from user import User
from search import SearchModel
from searchSocial import SocialModel
from searchCountry import CountryModel

# load env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth setup
oauth = OAuth(app)

# Register Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # Fetch metadata
    claims_options={
        'iss': {'values': ['https://accounts.google.com']},  # Validate the 'iss' claim
    },
)
# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("CLIENT_ID")  # Replace with your GitHub Client ID
GITHUB_CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # Replace with your GitHub Client Secret
GITHUB_AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"

# OAuth 2 client setup
client = WebApplicationClient(GITHUB_CLIENT_ID)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass


def get_user_from_db(email):
    db = get_db()
    return db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/login/google')
def google_login():
    # Redirect to Google for authorization
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/login/google/callback')
def google_callback():
    token = google.authorize_access_token()
    userinfo = google.get('userinfo').json()

    # Fetch user info from Google and store it in session
    session['logged_in'] = True
    session['name'] = userinfo['name']
    session['email'] = userinfo['email']
    session['profile_pic'] = userinfo['picture']

    # Optionally: Save the user to the database if needed
    # Example logic: Check if user exists, if not, create one.
    email = userinfo['email']
    user = get_user_from_db(email)

    if not user:
        # Save new user to DB
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO user (id, name, email, profile_pic) VALUES (?, ?, ?, ?)',
                    (str(uuid4()), userinfo['name'], userinfo['email'], userinfo['picture']))
        conn.commit()

    # Redirect to homepage
    return redirect(url_for('index'))


@app.route('/login')
def login():
    # Redirect to GitHub for authorization
    return client.prepare_request_uri(GITHUB_AUTHORIZATION_BASE_URL,
                                      redirect_uri=request.base_url + "/callback")
    # return redirect(authorization_url)


@app.route('/login/callback')
def callback():
    # Get authorization code GitHub sent back to us
    code = request.args.get("code")

    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        GITHUB_TOKEN_URL,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    # Send token request
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET),
    )

    # Parse the token response
    client.parse_request_body_response(token_response.text)

    # Fetch user information from GitHub
    uri, headers, body = client.add_token(GITHUB_USER_API_URL)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Store user info in session
    user_info = userinfo_response.json()
    # session['github_user'] = user_info

    # Extract the necessary fields from user_info
    github_user_id = str(user_info.get('id'))
    name = user_info.get('name') or user_info.get('login')
    email = user_info.get('email')

    if not email:
        # GitHub doesn't always provide an email, handle cases where email is not provided
        flash("GitHub account does not have a public email. Please use another method.")
        return redirect(url_for('index'))

        # Check if user already exists in the database
    user = get_user_from_db(email)

    if not user:
        # If a user does not exist, insert the new user into the database
        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute('INSERT INTO user (id, name, email, profile_pic) VALUES (?, ?, ?, ?)',
                        (github_user_id, name, email, user_info.get('avatar_url')))
            conn.commit()
        except sqlite3.IntegrityError:
            # Handle any integrity errors (like unique constraints) if needed
            flash("A user with this email already exists.")
            return redirect(url_for('index'))

        # Log the user in by storing their info in the session
    session['logged_in'] = True
    session['github_user'] = user_info
    session['user_id'] = github_user_id
    session['name'] = name
    session['email'] = email

    # Redirect to homepage after successful login
    return redirect(url_for('index'))


@app.route('/history', methods=["GET"])
def history():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Please log in to see your search history.')
        return redirect(url_for('user_login'))

    # Fetch search history for the logged-in user
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM search_history WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    search_history = cur.fetchall()

    return render_template('history.html', search_history=search_history)


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

            return redirect(url_for('user_login'))  # redirect to homepage

        except sqlite3.IntegrityError:
            return "User already exists"

    return render_template('signup.html')


# Route to display login page and handle login
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
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
        return jsonify([])

    # Instantiate the search model and perform the search
    search_model = SearchModel(query)
    default_results = search_model.perform_search()

    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO search_history (id, user_id, query, result) VALUES (?, ?, ?, ?)',
                    (str(uuid4()), user_id, query, str(default_results)))
        conn.commit()

    # Return the search results as JSON
    return jsonify(default_results)


# Search Social Route
@app.route('/searchSocial', methods=["POST"])
def searchSocial():
    name = request.form.get('first-name')
    email = request.form.get('email', None)

    if not name:
        return

    else:
        # Create a SocialModel instance
        social_model = SocialModel(name, email)

        # Perform the search
        social_results = social_model.search_on_social_media()

        if 'logged_in' in session and session['logged_in']:
            user_id = session.get('user_id')
            conn = get_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO search_history (id, user_id, query, result) VALUES (?, ?, ?, ?)',
                        (str(uuid4()), user_id, name, str(social_results)))
            conn.commit()

        # Return or display results
        return render_template('index.html', social_results=social_results)


# Search country route
@app.route("/searchCountry", methods=["POST"])
def searchCountry():
    query = request.form.get('query')

    # Create an instance of CountryModel and perform the search
    country_model = CountryModel(query)
    country_results = country_model.perform_search()

    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO search_history (id, user_id, query, result) VALUES (?, ?, ?, ?)',
                    (str(uuid4()), user_id, query, str(country_results)))
        conn.commit()

    return render_template('index.html', country_results=country_results)


# Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('profile_pic', None)
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
