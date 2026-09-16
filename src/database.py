"""Database management for tracking processed RSS items."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import config
from logger import logger


class ProcessedItemsDB:
    """SQLite database for tracking processed RSS items."""

    def __init__(self, db_path: Path = config.DB_PATH):
        """
        Initialize database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
            logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def item_exists(self, guid: str) -> bool:
        """
        Check if item has been processed.

        Args:
            guid: Item GUID or URL

        Returns:
            True if item exists in database
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM processed_items WHERE guid = ?", (guid,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return False

    def add_item(
        self,
        guid: str,
        url: Optional[str] = None,
        title: Optional[str] = None,
        included: bool = False,
        filter_reason: Optional[str] = None,
    ) -> bool:
        """
        Add processed item to database.

        Args:
            guid: Item GUID or URL
            url: Item URL
            title: Item title
            included: Whether item was included in report
            filter_reason: Reason for exclusion if not included

        Returns:
            True if successfully added
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO processed_items
                    (guid, url, title, included_in_report, filter_reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (guid, url, title, included, filter_reason))
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database insert error: {e}")
            return False

    def mark_gemini_processed(self, guid: str) -> bool:
        """Mark item as processed by Gemini."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE processed_items
                    SET gemini_processed = 1
                    WHERE guid = ?
                """, (guid,))
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database update error: {e}")
            return False

    def mark_email_sent(self, guid: str) -> bool:
        """Mark item as included in sent email."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE processed_items
                    SET email_sent = 1
                    WHERE guid = ?
                """, (guid,))
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database update error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get processing statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN included_in_report = 1 THEN 1 ELSE 0 END) as included,
                        SUM(CASE WHEN included_in_report = 0 THEN 1 ELSE 0 END) as filtered,
                        SUM(CASE WHEN gemini_processed = 1 THEN 1 ELSE 0 END) as gemini_processed,
                        SUM(CASE WHEN email_sent = 1 THEN 1 ELSE 0 END) as email_sent
                    FROM processed_items
                    WHERE processed_at >= datetime('now', '-30 days')
                """)
                row = cursor.fetchone()
                return {
                    "total": row[0] or 0,
                    "included": row[1] or 0,
                    "filtered": row[2] or 0,
                    "gemini_processed": row[3] or 0,
                    "email_sent": row[4] or 0,
                }
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return {}
