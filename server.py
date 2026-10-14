"""
Spotify Stats & Activity MCP Server
Servidor MCP con autenticación permanente para consultar estadísticas y actividad de Spotify.
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
import requests
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

SCOPE = "user-top-read user-read-recently-played playlist-read-private user-read-currently-playing user-read-playback-state playlist-modify-public playlist-modify-private"

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


@mcp.tool()
def search_tracks(query: str, limit: int = 10) -> list[dict]:
    """
    Busca canciones en el catálogo de Spotify por nombre, artista o género.

    Args:
        query: Término de búsqueda (ej. 'Bad Bunny Moscow Mule' o 'Reggaeton 2026').
        limit: Cantidad de resultados a devolver (1 a 20).
    """
    limit = max(1, min(limit, 20))
    sp = get_spotify_client()
    res = sp.search(q=query, limit=limit, type="track")
    items = res.get("tracks", {}).get("items", [])

    results = []
    for item in items:
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        album_info = item.get("album", {})
        album_images = album_info.get("images", [])
        cover_url = album_images[0].get("url") if album_images else None
        results.append(
            {
                "uri": item.get("uri"),
                "id": item.get("id"),
                "cancion": item.get("name"),
                "artistas": artists,
                "album": album_info.get("name"),
                "duracion": ms_to_time(item.get("duration_ms", 0)),
                "cover_url": cover_url,
                "spotify_url": item.get("external_urls", {}).get("spotify"),
            }
        )
    return results


@mcp.tool()
def create_playlist(
    name: str,
    description: str = "Creada automáticamente con Spotify MCP",
    public: bool = False,
    track_items: list[str] = [],
) -> dict:
    """
    Crea una nueva playlist en la cuenta de Spotify del usuario y opcionalmente añade canciones.

    Args:
        name: Nombre de la playlist.
        description: Descripción de la playlist.
        public: Si la playlist será pública (True) o privada (False). Por defecto False.
        track_items: Lista de canciones a añadir. Pueden ser URIs de Spotify (spotify:track:...)
                     o nombres de canciones con artistas (ej. ['Bad Bunny - Dákiti', 'Blessd - Medallo']).
    """
    sp = get_spotify_client()
    auth_mgr = sp.auth_manager
    token = auth_mgr.get_access_token(as_dict=False)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Crear playlist usando /v1/me/playlists
    res = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json={"name": name, "public": public, "description": description},
        timeout=10,
    )
    if not res.ok:
        raise RuntimeError(f"Error creando playlist ({res.status_code}): {res.text}")

    new_pl = res.json()
    pl_id = new_pl["id"]
    pl_url = new_pl["external_urls"]["spotify"]

    added_tracks = []
    uris_to_add = []

    # 2. Resolver URIs de canciones
    for item in track_items:
        item = item.strip()
        if not item:
            continue
        if item.startswith("spotify:track:"):
            uris_to_add.append(item)
            added_tracks.append({"uri": item, "query": item})
        elif len(item) == 22 and item.isalnum():
            uri = f"spotify:track:{item}"
            uris_to_add.append(uri)
            added_tracks.append({"uri": uri, "query": item})
        else:
            try:
                search_res = sp.search(q=item, limit=1, type="track")
                tracks = search_res.get("tracks", {}).get("items", [])
                if tracks:
                    found = tracks[0]
                    uris_to_add.append(found["uri"])
                    artists = ", ".join(a.get("name", "") for a in found.get("artists", []))
                    added_tracks.append(
                        {
                            "cancion": found["name"],
                            "artistas": artists,
                            "uri": found["uri"],
                            "url": found["external_urls"]["spotify"],
                        }
                    )
            except Exception as e:
                print(f"Error resolviendo track '{item}':", e)

    # 3. Añadir a la playlist por lotes
    if uris_to_add:
        for i in range(0, len(uris_to_add), 100):
            batch = uris_to_add[i : i + 100]
            requests.post(
                f"https://api.spotify.com/v1/playlists/{pl_id}/items",
                headers=headers,
                json={"uris": batch},
                timeout=10,
            )

    return {
        "status": "success",
        "playlist_id": pl_id,
        "playlist_name": name,
        "playlist_url": pl_url,
        "total_canciones_agregadas": len(uris_to_add),
        "canciones": added_tracks,
    }


@mcp.tool()
def create_smart_playlist(
    name: str,
    mode: Literal["top_tracks", "top_artists_mix", "artist_spotlight"] = "top_tracks",
    time_range: Literal["short_term", "medium_term", "long_term"] = "short_term",
    track_count: int = 20,
    seed_artists: list[str] = [],
    description: str = "",
) -> dict:
    """
    Crea una playlist inteligente automatizada basada en tus gustos musicales reales.

    Args:
        name: Nombre de la nueva playlist.
        mode:
            - 'top_tracks': Añade tus canciones más escuchadas del período seleccionado.
            - 'top_artists_mix': Crea un mix combinando las mejores canciones de tus artistas favoritos.
            - 'artist_spotlight': Crea una selección de los artistas específicos indicados en 'seed_artists'.
        time_range: 'short_term' (~últimas 4 semanas), 'medium_term' (~6 meses), 'long_term' (histórico).
        track_count: Cantidad total de canciones a incluir (1 a 50).
        seed_artists: Lista de artistas específicos para el modo 'artist_spotlight' o para personalizar el mix.
        description: Descripción opcional para la playlist.
    """
    sp = get_spotify_client()
    track_count = max(5, min(track_count, 50))
    uris_to_add = []
    added_info = []

    if not description:
        description = f"Generada automáticamente por IA & Spotify MCP ({mode})"

    if mode == "top_tracks":
        top = sp.current_user_top_tracks(limit=track_count, time_range=time_range)
        for t in top.get("items", []):
            uris_to_add.append(t["uri"])
            artists = ", ".join(a.get("name", "") for a in t.get("artists", []))
            added_info.append(f"{t['name']} - {artists}")

    elif mode in ("top_artists_mix", "artist_spotlight"):
        target_artists = []
        if seed_artists:
            target_artists = seed_artists[:5]
        else:
            top_a = sp.current_user_top_artists(limit=5, time_range=time_range)
            target_artists = [a["name"] for a in top_a.get("items", [])]

        per_artist = max(1, track_count // max(1, len(target_artists)))

        for art_name in target_artists:
            search_art = sp.search(q=art_name, type="artist", limit=1)
            art_items = search_art.get("artists", {}).get("items", [])
            if not art_items:
                continue
            art_id = art_items[0]["id"]
            top_tracks_art = sp.artist_top_tracks(art_id)
            for t in top_tracks_art.get("tracks", [])[:per_artist]:
                if t["uri"] not in uris_to_add:
                    uris_to_add.append(t["uri"])
                    added_info.append(f"{t['name']} - {art_name}")
                if len(uris_to_add) >= track_count:
                    break
            if len(uris_to_add) >= track_count:
                break

    auth_mgr = sp.auth_manager
    token = auth_mgr.get_access_token(as_dict=False)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Crear playlist usando /v1/me/playlists
    res = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json={"name": name, "public": False, "description": description},
        timeout=10,
    )
    if not res.ok:
        raise RuntimeError(f"Error creando playlist ({res.status_code}): {res.text}")

    new_pl = res.json()
    pl_id = new_pl["id"]
    pl_url = new_pl["external_urls"]["spotify"]

    if uris_to_add:
        for i in range(0, len(uris_to_add), 100):
            batch = uris_to_add[i : i + 100]
            requests.post(
                f"https://api.spotify.com/v1/playlists/{pl_id}/items",
                headers=headers,
                json={"uris": batch},
                timeout=10,
            )

    return {
        "status": "success",
        "playlist_name": name,
        "playlist_url": pl_url,
        "total_canciones": len(uris_to_add),
        "canciones": added_info,
    }


if __name__ == "__main__":
    mcp.run()

