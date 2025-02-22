# Import necessay modules
from flask import Flask, redirect, request, session, url_for, render_template, jsonify
import spotipy, os,  logging
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)