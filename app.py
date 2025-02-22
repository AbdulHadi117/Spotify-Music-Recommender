# Import necessay modules
from flask import Flask, redirect, request, session, url_for, render_template, jsonify
import spotipy, os,  logging
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve Spotify API credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = Flask(__name__)

# Set the secret key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_COOKIE_NAME"] = "Spotify Music Recommender"

# Initialize Spotify OAuth client
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=(
        "user-read-email user-read-private user-library-modify "
        "user-library-read user-read-recently-played user-top-read "
        "playlist-read-private playlist-modify-private playlist-modify-public"
    )
)

# Configue logging
logging.basicConfig(level=logging.INFO)