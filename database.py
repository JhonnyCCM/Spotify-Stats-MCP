"""
Spotify Local History Database
Almacena el historial de reproducciones localmente en SQLite para filtros por 1 semana y fechas exactas.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "history.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS played_tracks (
                played_at TEXT PRIMARY KEY,
                track_id TEXT,
                track_name TEXT,
                artists TEXT,
                album TEXT,
                duration_ms INTEGER,
                cover_url TEXT,
                spotify_url TEXT
            )
        """)
        conn.commit()


def save_recent_tracks(items: list[dict]):
    if not items:
        return 0

    inserted = 0
    with get_db() as conn:
        for item in items:
            track = item.get("track", {}) if "track" in item else item
            played_at = item.get("played_at") or item.get("reproducido_el")
            if not played_at:
                continue

            track_id = track.get("id")
            track_name = track.get("name") or item.get("cancion")
            
            if "artists" in track and isinstance(track["artists"], list):
                artists = ", ".join(a.get("name", "") for a in track["artists"])
            else:
                artists = item.get("artistas", "")

            album_info = track.get("album", {})
            album_name = album_info.get("name") if isinstance(album_info, dict) else item.get("album", "")
            
            cover_url = item.get("cover_url")
            if not cover_url and isinstance(album_info, dict):
                images = album_info.get("images", [])
                cover_url = images[0].get("url") if images else None

            duration_ms = track.get("duration_ms") or item.get("duration_ms", 0)
            spotify_url = track.get("external_urls", {}).get("spotify") if isinstance(track.get("external_urls"), dict) else item.get("spotify_url", "")

            cur = conn.execute("""
                INSERT OR IGNORE INTO played_tracks 
                (played_at, track_id, track_name, artists, album, duration_ms, cover_url, spotify_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (played_at, track_id, track_name, artists, album_name, duration_ms, cover_url, spotify_url))
            if cur.rowcount > 0:
                inserted += 1
        conn.commit()
    return inserted


def ms_to_time(ms: int) -> str:
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    return f"{minutes}:{seconds:02d}"


def get_stats_by_date_range(start_iso: str | None = None, end_iso: str | None = None):
    init_db()
    with get_db() as conn:
        query = "SELECT * FROM played_tracks WHERE 1=1"
        params = []
        if start_iso:
            query += " AND played_at >= ?"
            params.append(start_iso)
        if end_iso:
            query += " AND played_at <= ?"
            params.append(end_iso)

        # 1. Top canciones en este rango
        tracks_query = f"""
            SELECT track_name, artists, album, cover_url, spotify_url, 
                   COUNT(*) as play_count, MAX(duration_ms) as dur_ms
            FROM ({query})
            GROUP BY track_name, artists
            ORDER BY play_count DESC
            LIMIT 50
        """
        tracks_rows = conn.execute(tracks_query, params).fetchall()
        top_tracks = []
        for rank, r in enumerate(tracks_rows, start=1):
            top_tracks.append({
                "puesto": rank,
                "cancion": r["track_name"],
                "artistas": r["artists"],
                "album": r["album"],
                "duracion": ms_to_time(r["dur_ms"] or 0),
                "cover_url": r["cover_url"],
                "spotify_url": r["spotify_url"]
            })

        # 2. Top artistas en este rango
        artists_query = f"""
            SELECT artists, COUNT(*) as play_count, MAX(cover_url) as foto_url
            FROM ({query})
            GROUP BY artists
            ORDER BY play_count DESC
            LIMIT 50
        """
        artists_rows = conn.execute(artists_query, params).fetchall()
        top_artists = []
        for rank, r in enumerate(artists_rows, start=1):
            top_artists.append({
                "puesto": rank,
                "artista": r["artists"],
                "foto_url": r["foto_url"],
                "spotify_url": f"https://open.spotify.com/search/{r['artists']}"
            })

        return {
            "top_canciones": top_tracks,
            "top_artistas": top_artists,
        }


init_db()
