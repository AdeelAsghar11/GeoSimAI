"""Lightweight SQLite persistence module for GeoSimAI query history and bookmarks."""

import os
import sqlite3
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "geosim.db"
)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite database connection with dictionary row factory."""
    path = db_path or os.getenv("GEOSIM_DB_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables for query history and bookmarked sites."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Query history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            label TEXT,
            lon REAL NOT NULL,
            lat REAL NOT NULL,
            year INTEGER NOT NULL,
            threshold REAL NOT NULL,
            top_n INTEGER NOT NULL,
            match_count INTEGER NOT NULL,
            top_score REAL
        )
    """)

    # Saved bookmarks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            category TEXT,
            lon REAL NOT NULL,
            lat REAL NOT NULL,
            description TEXT
        )
    """)

    conn.commit()

    # Seed default bookmarks if empty
    cursor.execute("SELECT COUNT(*) FROM bookmarks")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            ("Domel Confluence", "River", 73.4650, 34.3830, "Confluence of Neelum and Jhelum rivers"),
            ("Muzaffarabad City Core", "Urban", 73.4720, 34.3580, "Central urban fabric and commercial core"),
            ("Pir Chinasi Plateau", "Forest", 73.5500, 34.3890, "High-altitude alpine forest and green plateau"),
            ("Neelum Valley Slope", "Vegetation", 73.4800, 34.3950, "Terraced valley greenery and montane canopy"),
        ]
        cursor.executemany(
            "INSERT INTO bookmarks (name, category, lon, lat, description) VALUES (?, ?, ?, ?, ?)",
            seed_data,
        )
        conn.commit()

    conn.close()


def log_query(
    lon: float,
    lat: float,
    year: int,
    threshold: float,
    top_n: int,
    match_count: int,
    top_score: Optional[float] = None,
    label: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Log an executed similarity search query to history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO query_history (label, lon, lat, year, threshold, top_n, match_count, top_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (label, lon, lat, year, threshold, top_n, match_count, top_score),
    )
    conn.commit()
    query_id = cursor.lastrowid
    conn.close()
    return query_id


def get_history(limit: int = 30, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve reverse-chronological query history."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM query_history ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def add_bookmark(
    name: str,
    lon: float,
    lat: float,
    category: Optional[str] = "General",
    description: Optional[str] = "",
    db_path: Optional[str] = None,
) -> int:
    """Add a new geographic location to bookmarks."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bookmarks (name, category, lon, lat, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, category, lon, lat, description),
    )
    conn.commit()
    bookmark_id = cursor.lastrowid
    conn.close()
    return bookmark_id


def get_bookmarks(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all bookmarked locations."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookmarks ORDER BY id ASC")
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def delete_bookmark(bookmark_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a bookmark by ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
