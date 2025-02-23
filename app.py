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

def get_spotify_client():
    """
    Retrieves the Spotify client using the stored token info.

    If the token info is not available, or if the token is expired,
    attempts to refresh the token and store it in the session.

    Returns:
        spotipy.Spotify: The Spotify client
    """
    token_info = session.get("token_info")
    if not token_info:
        return None

    # Check if the token has expired
    if sp_oauth.is_token_expired(token_info):
        try:
            # Attempt to refresh the token
            token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
            # Store the refreshed token in the session
            session["token_info"] = token_info
        except Exception as e:
            # Log the error if the token cannot be refreshed
            logging.error(f"Error refreshing access token: {e}")
            return None

    # Create the Spotify client with the access token
    return spotipy.Spotify(auth=token_info["access_token"])

def fetch_profile_data(sp):
    """
    Fetches the current user's profile data, including the number of playlists,
    top tracks, top artists, and top genres.

    Args:
        sp (spotipy.Spotify): The Spotify client

    Returns:
        tuple: A tuple containing profile data, number of playlists, top genres,
               top artists, and top tracks
    """
    # Get the user's profile data
    profile_data = sp.current_user()

    # Get the total number of playlists
    num_playlists = sp.current_user_playlists()["total"]

    # Get the user's top tracks, limited to 5
    top_tracks = sp.current_user_top_tracks(limit=5)

    # Get the user's top artists, limited to 5
    top_artists = sp.current_user_top_artists(limit=5)
    
    top_genres = []

    # Collect genres from top artists
    for artist in top_artists["items"]:
        top_genres.extend(artist["genres"])

    # Deduplicate and limit the top genres to 3
    top_genres = list(set(top_genres[:3]))

    # Capitalize each genre
    top_genres = [genre.title() for genre in top_genres]

    return profile_data, num_playlists, top_tracks, top_artists, top_genres


@app.route("/")
def home():
    """
    Handles requests to the root URL by rendering the home template.
    
    Returns:
        A rendered HTML template for the home page.
    """
    return render_template("home.html")

@app.route("/logout")
def logout():
    """
    Logs out the user by clearing the session.

    Returns:
        A redirect to the home page.
    """
    # Clear the session
    session.clear()
    # Redirect to the home page
    return redirect(url_for("home"))

@app.route("/login")
def login():
    """
    Redirects the user to the Spotify authorization URL.

    Redirects the user to the Spotify authorization URL to log in and
    authorize the application to access their data.

    Returns:
        A redirect to the Spotify authorization URL.
    """
    # Get the authorization URL
    auth_url = sp_oauth.get_authorize_url()
    # Redirect the user to the authorization URL
    return redirect(auth_url)

@app.route("/callback")
def callback():
    """
    Handles the authorization callback from Spotify.

    The authorization code is retrieved from the query string, and the access
    token is fetched using the Spotify client. The access token is stored in the
    session for later use.

    Returns:
        A redirect to the profile page if the authorization is successful.
        A JSON response with an error message if the authorization fails.
    """
    # Get the authorization code from the query string
    code = request.args.get("code")
    if not code:
        # If the code is missing, return an error response
        return jsonify({"error": "Missing code parameter"}), 400
    try:
        # Get the access token using the authorization code
        token_info = sp_oauth.get_access_token(code)
        # Store the access token in the session
        session["token_info"] = token_info
    except Exception as e:
        # If an error occurs, log it and return an error response
        logging.error(f"Error getting access token: {e}")
        return jsonify({"error" : str(e)}), 400

    # Redirect to the profile page if the authorization is successful
    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    """
    Renders the user profile page.

    The user profile page is rendered with data fetched from the Spotify API,
    including the user's profile data, the number of playlists, top genres,
    top artists, and top tracks.

    If the access token is invalid or missing, the user is redirected to the
    login page.

    Returns:
        A rendered template for the profile page.
    """
    # Retrieve the Spotify client
    sp = get_spotify_client()

    # Redirect to login if Spotify client is not available
    if not sp:
        return redirect(url_for("login"))

    try:
        # Fetch the user profile data, number of playlists, top genres,
        # top artists, and top tracks from the Spotify API
        profile_data, num_playlists, top_genres, top_artists, top_tracks = fetch_profile_data(sp)
    except spotipy.exceptions.SpotifyException as e:
        # Log any Spotify API errors and return a JSON error response
        logging.error(f"Spotify API error: {e}")
        return jsonify({"error": str(e)}), 400

    # Render the profile page with the fetched data
    return render_template(
        "profile.html",
        profile=profile_data,
        num_playlists=num_playlists,
        top_genres=top_genres,
        top_artists=top_artists,
        top_tracks=top_tracks,
    )
