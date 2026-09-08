"""Unit tests for SQLite database operations and bookmarks."""

import os
import tempfile
import pytest
from src.core.database import (
    init_db,
    log_query,
    get_history,
    add_bookmark,
    get_bookmarks,
    delete_bookmark,
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_init_db_seeds_default_bookmarks(temp_db):
    """Initial database must have default seeded bookmarks."""
    bookmarks = get_bookmarks(temp_db)
    assert len(bookmarks) >= 3
    names = [b["name"] for b in bookmarks]
    assert "Domel Confluence" in names


def test_log_query_and_get_history(temp_db):
    """Logged query must appear in query history."""
    q_id = log_query(
        lon=73.018,
        lat=33.704,
        year=2023,
        threshold=0.75,
        top_n=10,
        match_count=4,
        top_score=0.98,
        label="Test Search",
        db_path=temp_db,
    )
    assert q_id > 0

    history = get_history(limit=10, db_path=temp_db)
    assert len(history) >= 1
    assert history[0]["label"] == "Test Search"
    assert history[0]["top_score"] == 0.98


def test_add_and_delete_bookmark(temp_db):
    """Should successfully add and delete a bookmark."""
    b_id = add_bookmark(
        name="Custom Site",
        lon=73.100,
        lat=33.650,
        category="Research",
        description="A custom testing parcel",
        db_path=temp_db,
    )
    assert b_id > 0

    bookmarks = get_bookmarks(temp_db)
    assert any(b["name"] == "Custom Site" for b in bookmarks)

    deleted = delete_bookmark(b_id, db_path=temp_db)
    assert deleted is True

    bookmarks_after = get_bookmarks(temp_db)
    assert not any(b["id"] == b_id for b in bookmarks_after)
