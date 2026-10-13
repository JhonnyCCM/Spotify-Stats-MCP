"""
Spotify Stats & Activity MCP Server
Servidor MCP con autenticación permanente para consultar estadísticas y actividad de Spotify.
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from mcp.server.fastmcp import FastMCP

# Cargar variables de entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
CACHE_PATH = str(Path(__file__).parent / ".cache")

SCOPE = "user-top-read user-read-recently-played playlist-read-private user-read-currently-playing user-read-playback-state"

mcp = FastMCP("spotify-stats")


def get_spotify_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH,
        open_browser=False,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def ms_to_time(ms: int) -> str:
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    return f"{minutes}:{seconds:02d}"


@mcp.tool()
def get_user_profile() -> dict:
    """
    Obtiene los datos del perfil de usuario de Spotify (nombre de usuario, ID, seguidores, enlace de perfil y foto).
    """
    sp = get_spotify_client()
    user = sp.current_user()
    images = user.get("images", [])
    image_url = images[0].get("url") if images else None

    return {
        "display_name": user.get("display_name"),
        "id": user.get("id"),
        "followers": user.get("followers", {}).get("total", 0),
        "profile_url": user.get("external_urls", {}).get("spotify"),
        "avatar_url": image_url,
    }


@mcp.tool()
def get_currently_playing() -> dict:
    """
    Obtiene la canción que el usuario está escuchando en este momento en Spotify.
    """
    sp = get_spotify_client()
    try:
        playback = sp.current_playback()
    except Exception as e:
        return {"is_playing": False, "error": str(e)}

    if not playback or not playback.get("item"):
        return {
            "is_playing": False,
            "message": "No hay ninguna canción reproduciéndose ahora mismo."
        }

    item = playback["item"]
    artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
    album_info = item.get("album", {})
    album_images = album_info.get("images", [])
    cover_url = album_images[0].get("url") if album_images else None

    progress_ms = playback.get("progress_ms", 0)
    duration_ms = item.get("duration_ms", 0)

    return {
        "is_playing": playback.get("is_playing", False),
        "cancion": item.get("name"),
        "artistas": artists,
        "album": album_info.get("name"),
        "progreso": ms_to_time(progress_ms),
        "duracion": ms_to_time(duration_ms),
        "progress_ms": progress_ms,
        "duration_ms": duration_ms,
        "cover_url": cover_url,
        "spotify_url": item.get("external_urls", {}).get("spotify"),
        "dispositivo": playback.get("device", {}).get("name"),
    }


@mcp.tool()
def get_top_tracks(
    time_range: Literal["short_term", "medium_term", "long_term"] = "medium_term",
    limit: int = 10,
) -> list[dict]:
    """
    Obtiene las canciones más escuchadas del usuario en Spotify.

    Args:
        time_range: Rango de tiempo:
            - 'short_term': Últimas 4 semanas (~mensual / reciente)
            - 'medium_term': Últimos 6 meses
            - 'long_term': Varios años / histórico de por vida (all-time)
        limit: Cantidad de canciones a devolver (entre 1 y 50). Por defecto 10.
    """
    limit = max(1, min(limit, 50))
    sp = get_spotify_client()
    data = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    results = []
    for rank, item in enumerate(data.get("items", []), start=1):
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        album_info = item.get("album", {})
        album_images = album_info.get("images", [])
        cover_url = album_images[0].get("url") if album_images else None
        results.append(
            {
                "puesto": rank,
                "cancion": item.get("name"),
                "artistas": artists,
                "album": album_info.get("name"),
                "fecha_lanzamiento": album_info.get("release_date"),
                "duracion": ms_to_time(item.get("duration_ms", 0)),
                "spotify_url": item.get("external_urls", {}).get("spotify"),
                "cover_url": cover_url,
            }
        )
    return results


@mcp.tool()
def get_top_artists(
    time_range: Literal["short_term", "medium_term", "long_term"] = "medium_term",
    limit: int = 10,
) -> list[dict]:
    """
    Obtiene los artistas más escuchados del usuario en Spotify.

    Args:
        time_range: Rango de tiempo:
            - 'short_term': Últimas 4 semanas (~mensual / reciente)
            - 'medium_term': Últimos 6 meses
            - 'long_term': Varios años / histórico de por vida (all-time)
        limit: Cantidad de artistas a devolver (entre 1 y 50). Por defecto 10.
    """
    limit = max(1, min(limit, 50))
    sp = get_spotify_client()
    data = sp.current_user_top_artists(limit=limit, time_range=time_range)

    results = []
    for rank, item in enumerate(data.get("items", []), start=1):
        images = item.get("images", [])
        image_url = images[0].get("url") if images else None
        results.append(
            {
                "puesto": rank,
                "artista": item.get("name"),
                "spotify_url": item.get("external_urls", {}).get("spotify"),
                "foto_url": image_url,
            }
        )
    return results


@mcp.tool()
def get_recently_played(limit: int = 10) -> list[dict]:
    """
    Obtiene las últimas canciones reproducidas por el usuario en Spotify con fecha y hora.

    Args:
        limit: Cantidad de canciones recientes a devolver (1 a 50). Por defecto 10.
    """
    limit = max(1, min(limit, 50))
    sp = get_spotify_client()
    data = sp.current_user_recently_played(limit=limit)

    results = []
    for item in data.get("items", []):
        track = item.get("track", {})
        artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
        album_info = track.get("album", {})
        album_images = album_info.get("images", [])
        cover_url = album_images[0].get("url") if album_images else None
        results.append(
            {
                "cancion": track.get("name"),
                "artistas": artists,
                "album": album_info.get("name"),
                "reproducido_el": item.get("played_at"),
                "spotify_url": track.get("external_urls", {}).get("spotify"),
                "cover_url": cover_url,
            }
        )
    return results


@mcp.tool()
def get_user_playlists(limit: int = 10) -> list[dict]:
    """
    Obtiene las playlists del usuario en Spotify.

    Args:
        limit: Cantidad de playlists a consultar (1 a 50). Por defecto 10.
    """
    limit = max(1, min(limit, 50))
    sp = get_spotify_client()
    data = sp.current_user_playlists(limit=limit)

    results = []
    for pl in data.get("items", []):
        images = pl.get("images", [])
        cover_url = images[0].get("url") if images else None
        results.append(
            {
                "nombre": pl.get("name"),
                "total_canciones": pl.get("tracks", {}).get("total", 0),
                "publica": pl.get("public"),
                "spotify_url": pl.get("external_urls", {}).get("spotify"),
                "cover_url": cover_url,
            }
        )
    return results


@mcp.tool()
def get_music_profile_summary() -> dict:
    """
    Obtiene un resumen completo de los gustos musicales del usuario comparando
    el corto plazo (últimas 4 semanas), mediano plazo (6 meses) y largo plazo (histórico all-time).
    """
    ranges = [
        ("short_term", "Últimas 4 semanas (Mensual)"),
        ("medium_term", "Últimos 6 meses"),
        ("long_term", "Histórico (De por vida)"),
    ]

    summary = {
        "usuario": get_user_profile(),
        "periodos": {},
    }

    for tr_key, tr_name in ranges:
        tracks = get_top_tracks(time_range=tr_key, limit=5)
        artists = get_top_artists(time_range=tr_key, limit=5)
        summary["periodos"][tr_name] = {
            "top_canciones": [f"{t['puesto']}. {t['cancion']} - {t['artistas']}" for t in tracks],
            "top_artistas": [f"{a['puesto']}. {a['artista']}" for a in artists],
        }

    return summary


if __name__ == "__main__":
    mcp.run()
