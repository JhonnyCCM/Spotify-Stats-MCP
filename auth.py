"""
Script de autorización única para Spotify
Abre el navegador para que autorices la aplicación en tu cuenta de Spotify.
Guarda los tokens renovables en .cache
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
CACHE_PATH = str(Path(__file__).parent / ".cache")

SCOPE = "user-top-read user-read-recently-played playlist-read-private user-read-currently-playing user-read-playback-state"

print("Iniciando flujo de autorización de Spotify...")
auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH,
    open_browser=True,
)

token_info = auth_manager.get_access_token(as_dict=True)
if token_info:
    sp = spotipy.Spotify(auth_manager=auth_manager)
    user = sp.current_user()
    print(f"¡Éxito! Autenticado correctamente como: {user.get('display_name')}")
else:
    print("No se pudo obtener el token.")
