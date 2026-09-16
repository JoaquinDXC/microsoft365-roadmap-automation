"""Tests for reset_database.py functionality."""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import config


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_processed_items.db"

        # Create schema
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE NOT NULL,
                    url TEXT,
                    title TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    included_in_report BOOLEAN DEFAULT 0,
                    filter_reason TEXT,
                    gemini_processed BOOLEAN DEFAULT 0,
                    email_sent BOOLEAN DEFAULT 0
                )
            """)
            conn.commit()

        yield db_path

        # Cleanup
        if db_path.exists():
            db_path.unlink()


@pytest.fixture
def db_with_data(temp_db):
    """Create database with test data."""
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        # Insert test data
        test_items = [
            ("guid-1", "http://example.com/1", "Item 1"),
            ("guid-2", "http://example.com/2", "Item 2"),
            ("guid-3", "http://example.com/3", "Item 3"),
        ]
        for guid, url, title in test_items:
            cursor.execute(
                """
                INSERT INTO processed_items (guid, url, title, email_sent)
                VALUES (?, ?, ?, 1)
                """,
                (guid, url, title),
            )
        conn.commit()

    return temp_db


def test_database_reset_clears_records(db_with_data):
    """Test that database reset clears all records."""
    # Import here to use patched config
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = db_with_data
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()
        initial_count = reset.get_record_count()
        assert initial_count == 3

        # Create backup and reset
        reset.create_backup()
        reset.reset_database()

        final_count = reset.get_record_count()
        assert final_count == 0


def test_backup_creation(db_with_data):
    """Test that backup is created successfully."""
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = db_with_data
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()
        assert reset.create_backup()
        assert reset.backup_path.exists()
        assert reset.backup_path.suffix == ".db"


def test_backup_contains_data(db_with_data):
    """Test that backup contains original data."""
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = db_with_data
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()

        # Get initial count
        initial_count = reset.get_record_count()
        assert initial_count == 3

        # Create backup
        reset.create_backup()

        # Reset database
        reset.reset_database()

        # Verify database is empty
        assert reset.get_record_count() == 0

        # Verify backup has original data
        with sqlite3.connect(reset.backup_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_items")
            backup_count = cursor.fetchone()[0]
        assert backup_count == 3


def test_schema_unchanged(db_with_data):
    """Test that schema remains unchanged after reset."""
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = db_with_data
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()

        # Get original schema
        original_schema = reset.get_schema_info()

        # Reset
        reset.create_backup()
        reset.reset_database()

        # Get new schema
        new_schema = reset.get_schema_info()

        # Verify tables unchanged
        assert set(original_schema["tables"]) == set(new_schema["tables"])

        # Verify columns unchanged
        orig_cols = {c["name"]: c["type"] for c in original_schema["columns"]}
        new_cols = {c["name"]: c["type"] for c in new_schema["columns"]}
        assert orig_cols == new_cols


def test_reset_empty_database(temp_db):
    """Test reset on empty database."""
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = temp_db
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()
        assert reset.get_record_count() == 0

        # Should still work on empty database
        reset.create_backup()
        reset.reset_database()

        assert reset.get_record_count() == 0


def test_backup_dir_creation(temp_db):
    """Test that backup directory is created if it doesn't exist."""
    sys.path.insert(0, str(Path(__file__).parent.parent))

    with patch("reset_database.config") as mock_config:
        mock_config.DB_PATH = temp_db
        mock_config.DRY_RUN = True

        from reset_database import DatabaseReset

        reset = DatabaseReset()
        assert reset.backup_dir.exists()


def test_no_emails_sent():
    """Test that reset_database doesn't attempt to send emails."""
    # This is a sanity check - reset_database.py should never import email_sender
    with open(Path(__file__).parent.parent / "reset_database.py", "r") as f:
        content = f.read()

    assert "email_sender" not in content
    assert "send_email" not in content
    assert "graph_sender" not in content
    assert "oauth" not in content


def test_no_internet_access():
    """Test that reset_database doesn't access external services."""
    with open(Path(__file__).parent.parent / "reset_database.py", "r") as f:
        content = f.read()

    # Check for common external service patterns
    assert "httpx" not in content
    assert "requests" not in content
    assert "aiohttp" not in content
    assert "mcp_client" not in content
