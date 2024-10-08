"""Contains the Flask part of the project
    Import required Module/Lib
"""
import os
import random
# Import python standard lib
import sqlite3
from datetime import datetime, timedelta
from uuid import uuid4

import requests
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
# Third-party libraries
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import generate_password_hash, check_password_hash

# Internal imports
from api.db import init_db_command, get_db
from api.search import SearchModel
from api.searchCountry import CountryModel
from api.searchSocial import SocialModel
from api.user import User

# load env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth setup
oauth = OAuth(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    twitter = request.form.get('twitter')
    linkedin = request.form.get('linkedin')
    facebook = request.form.get('facebook')
    tiktok = request.form.get('tiktok')
    email = request.form.get('email', None)

    if not (twitter or linkedin or facebook or tiktok or email):
        return render_template('index.html', error="Please provide at least one social media handle or email.")

    social_results = {}

    if twitter:
        social_model = SocialModel(twitter)
        social_results['twitter'] = social_model.search_twitter()

        log_search_to_db('twitter', twitter, social_results['twitter'])

    if linkedin:
        social_model = SocialModel(linkedin)
        social_results['linkedin'] = social_model.search_linkedin()

        log_search_to_db('linkedin', linkedin, social_results['linkedin'])

    if facebook:
        social_model = SocialModel(facebook)
        social_results['facebook'] = social_model.search_facebook()

        log_search_to_db('facebook', facebook, social_results['facebook'])

    if tiktok:
        social_model = SocialModel(tiktok)
        social_results['tiktok'] = social_model.search_tiktok()

        log_search_to_db('tiktok', tiktok, social_results['tiktok'])

    # Return or display results
    return render_template('index.html', social_results=social_results)


# Helper function to log search results into the database
def log_search_to_db(platform, query, result):
    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO search_history (id, user_id, query, result) VALUES (?, ?, ?, ?)',
                    (str(uuid4()), user_id, f"{platform}: {query}", str(result)))
        conn.commit()


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


@app.route('/api/get-stock-data', methods=['GET'])
def get_stock_data():
    # Get current time and generate a time series with random stock price data
    now = datetime.now()
    time_format = '%Y-%m-%d %H:%M'

    # Generate timestamps for the last 3 updates (every hour)
    timestamps = [
                     (now.replace(minute=0, second=0) - timedelta(hours=i)).strftime(time_format)
                     for i in range(3)
                 ][::-1]  # Reverse so the latest is last

    # Generate random stock prices with some fluctuation
    stock_data = {
        'timestamps': timestamps,
        'eu': [random.randint(3500, 3550) for _ in range(3)],
        'wallstreet': [random.randint(15000, 15500) for _ in range(3)],
        'london': [random.randint(7000, 7100) for _ in range(3)],
        'china': [random.randint(5000, 5200) for _ in range(3)]
    }

    return jsonify(stock_data)


# Route to handle profile image upload
@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Check if a user is logged in and has user_id in session
    if 'user_id' not in session:
        flash('You must be logged in to upload a profile picture.')
        return redirect(url_for('user_login'))

        # Handle file upload
    if 'profile-img' not in request.files:
        flash('No file part in the request.')
        return redirect(request.referrer)

    file = request.files['profile-img']
    if file.filename == '':
        flash('No selected file.')
        return redirect(request.referrer)

    if file:  # conn.close()
        # Save the file with the user's user_id
        filename = f"{session['user_id']}.png"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Debugging
        if os.path.exists(file_path):
            print(f"File saved successfully at: {file_path}")
        else:
            print("Error: File was not saved.")

        # Update session with the new profile image path
        session['profile_img'] = f"/static/uploads/{filename}"
        # Save the new profile image path in the database
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Update the user's profile picture in the database
            cursor.execute("UPDATE user SET profile_pic = ? WHERE id = ?", (session['profile_img'], session['user_id']))
            conn.commit()

            flash('Profile picture updated successfully.')
        except Exception as e:
            flash(f'Error updating profile picture: {str(e)}')
        finally:
            conn.close()

    return redirect(request.referrer)


# Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('profile_pic', None)
    session.clear()
    return redirect(url_for('index'))


#
if __name__ == "__main__":
    app.run(debug=True)
