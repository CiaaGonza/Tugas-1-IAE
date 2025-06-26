import os
import requests
from flask import Flask, redirect, request, session, url_for, render_template
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = 'random_secret_key'  # Ganti dengan secret key yang aman

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

SCOPE = "user-read-private user-read-email"

def get_token():
    if 'access_token' in session:
        return session['access_token']
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    auth_query = {
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "client_id": CLIENT_ID
    }
    url_args = urlencode(auth_query)
    auth_url = f"{SPOTIFY_AUTH_URL}/?{url_args}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:3000/callback",
        "client_id": "c27a12505db24797a96338b8890bb247",
        "client_secret": "3db75b28aa1b41b3b57091c728c21021"
    }
    response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)
    response_data = response.json()
    access_token = response_data.get("access_token")
    session['access_token'] = access_token
    return redirect(url_for('home'))

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    access_token = get_token()
    if not access_token:
        return redirect(url_for('login'))
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": 10
    }
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)
    results = response.json()
    tracks = results.get('tracks', {}).get('items', [])
    return render_template('results.html', tracks=tracks, query=query)

@app.route('/api/search')
def api_search():
    query = request.args.get('query')
    access_token = get_token()
    if not access_token:
        return {"error": "Unauthorized. Please login first."}, 401
    if not query:
        return {"error": "Query parameter is required."}, 400
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": 10
    }
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch from Spotify API."}, response.status_code
    results = response.json()
    tracks = results.get('tracks', {}).get('items', [])
    # Format hasil agar lebih ringkas
    formatted_tracks = []
    for track in tracks:
        formatted_tracks.append({
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'spotify_url': track['external_urls']['spotify'],
            'preview_url': track['preview_url']
        })
    return {"tracks": formatted_tracks}
@app.route('/profile')
def profile():
    access_token = session.get('access_token')
    if not access_token:
        return "Belum login atau session habis. Silakan login ulang.", 401
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers)
    if response.status_code != 200:
        return "Token tidak valid atau expired. Silakan login ulang.", 401
    profile_data = response.json()
    return profile_data  # atau bisa juga: return jsonify(profile_data)

if __name__ == '__main__':
    app.run(port=3000, debug=True)