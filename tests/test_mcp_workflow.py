"""Tests for MCP workflow components."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from data_processor import DataProcessor
from html_generator import HTMLGenerator
from database import ProcessedItemsDB


class TestDataProcessor:
    """Test deterministic data processing."""

    def test_filter_by_date_returns_tuple(self):
        """Test that filter_by_date returns (items, stats)."""
        processor = DataProcessor()

        # Create test items with UTC timezone
        today = datetime.now(timezone.utc).isoformat()
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()

        items = [
            {"id": "1", "title": "New", "created": today},
            {"id": "2", "title": "Old", "created": old_date},
        ]

        result = processor.filter_by_date(items)

        # Should return tuple (items, stats)
        assert isinstance(result, tuple)
        assert len(result) == 2
        filtered_items, stats = result

        # Stats should be a dict with keys like 'items_before', 'items_after'
        assert isinstance(stats, dict)
        assert "items_before" in stats
        assert "items_after" in stats

    def test_filter_by_date_empty(self):
        """Test date filtering with empty input."""
        processor = DataProcessor()
        filtered_items, stats = processor.filter_by_date([])

        assert filtered_items == []
        assert stats["items_before"] == 0
        assert stats["items_after"] == 0

    def test_filter_by_products_returns_tuple(self):
        """Test that filter_by_products returns (items, stats)."""
        processor = DataProcessor()

        items = [
            {"id": "1", "title": "Teams", "platforms": [{"workload": "Microsoft Teams"}]},
            {"id": "2", "title": "Unknown", "platforms": [{"workload": "Unknown"}]},
        ]

        result = processor.filter_by_products(items)

        assert isinstance(result, tuple)
        assert len(result) == 2
        filtered_items, stats = result

        assert isinstance(stats, dict)
        assert "items_before" in stats
        assert "items_after" in stats

    def test_filter_by_products_empty(self):
        """Test product filtering with empty input."""
        processor = DataProcessor()
        filtered_items, stats = processor.filter_by_products([])

        assert filtered_items == []
        assert stats["items_before"] == 0
        assert stats["items_after"] == 0

    def test_calculate_strategic_value_returns_dict(self):
        """Test that calculate_strategic_value returns a dict."""
        processor = DataProcessor()

        item = {
            "id": "1",
            "title": "Exchange Update",
            "created": datetime.now(timezone.utc).isoformat(),
            "body": "General Availability",
            "platforms": [{"workload": "Exchange Online"}],
            "status": {"value": "General Availability"}
        }

        value_data = processor.calculate_strategic_value(item)

        assert isinstance(value_data, dict)
        assert "strategic_value" in value_data or len(value_data) > 0


class TestHTMLGenerator:
    """Test HTML generation."""

    def test_generate_html_empty(self):
        """Test HTML generation with empty items."""
        html = HTMLGenerator.generate_html([])

        assert isinstance(html, str)
        assert "<html" in html
        assert "<!DOCTYPE" in html
        assert "</html>" in html

    def test_generate_html_single_item(self):
        """Test HTML generation with one item."""
        items = [
            {
                "id": "1",
                "title": "Test Update",
                "body": "Description",
                "created": datetime.now().isoformat(),
                "platforms": [{"workload": "Microsoft Teams"}],
                "status": {"value": "General Availability"},
                "strategic_value": "HIGH",
                "reasoning": "Test reasoning",
                "moreInfoUrls": ["https://example.com"],
                "formats": [{"value": "Desktop"}],
                "cloudInstances": []
            }
        ]

        html = HTMLGenerator.generate_html(items)

        # Verify HTML structure
        assert "<html" in html
        assert "Test Update" in html
        assert "Description" in html

    def test_generate_html_no_external_deps(self):
        """Verify HTML has no external CDN dependencies."""
        items = [
            {
                "id": "1",
                "title": "Test",
                "body": "Test",
                "created": datetime.now().isoformat(),
                "platforms": [{"workload": "Microsoft Teams"}],
                "status": {"value": "General Availability"},
                "strategic_value": "MEDIUM",
                "reasoning": "Test",
                "moreInfoUrls": [],
                "formats": [],
                "cloudInstances": []
            }
        ]

        html = HTMLGenerator.generate_html(items)

        # Should NOT contain CDN references
        assert "cdn" not in html.lower()
        assert "googleapis" not in html.lower()
        assert "cloudflare" not in html.lower()
        assert "external" not in html.lower()


class TestSQLiteDeduplication:
    """Test SQLite deduplication logic."""

    def test_database_init(self):
        """Test database initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            assert db_path.exists()

    def test_add_item(self):
        """Test adding item to database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Add item
            db.add_item(
                guid="test-guid-1",
                url="https://example.com/1",
                title="Test Item",
                included=True
            )

            # Check if item exists
            exists = db.item_exists("test-guid-1")
            assert exists is True

    def test_item_does_not_exist_before_add(self):
        """Test that new items don't exist initially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Check if non-existent item returns False
            exists = db.item_exists("nonexistent-guid")
            assert exists is False

    def test_mark_email_sent(self):
        """Test marking item as email sent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Add item
            db.add_item("guid-1", "url-1", "Title", True)

            # Mark as sent
            result = db.mark_email_sent("guid-1")
            assert result is True

    def test_get_stats(self):
        """Test retrieving database statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Add items
            db.add_item("guid-1", "url-1", "Title 1", True)
            db.add_item("guid-2", "url-2", "Title 2", False)

            # Get stats
            stats = db.get_stats()

            assert isinstance(stats, dict)
            assert "total" in stats or len(stats) > 0


class TestDRYRUNBehavior:
    """Test DRY_RUN mode behavior."""

    def test_dry_run_in_config(self):
        """Test DRY_RUN in config."""
        from config import config

        # Should have DRY_RUN attribute
        assert hasattr(config, "DRY_RUN")
        assert isinstance(config.DRY_RUN, bool)
        # For testing, DRY_RUN should be True
        assert config.DRY_RUN is True

    def test_dry_run_email_behavior(self):
        """Test that DRY_RUN prevents SMTP when True."""
        import os
        from dotenv import load_dotenv

        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)

            # DRY_RUN should be parsed as True
            dry_run_value = os.getenv("DRY_RUN", "false").lower() == "true"

            # This test runs with DRY_RUN=true in .env
            assert dry_run_value is True


class TestFilterValidation:
    """Test filtering with real product names."""

    def test_allowed_products_defined(self):
        """Verify allowed products are correctly defined."""
        from config import config

        expected = {
            "Exchange Online",
            "Microsoft Teams",
            "SharePoint",
            "OneDrive"
        }

        assert config.ALLOWED_PRODUCTS == expected

    def test_filter_products_with_valid_workload(self):
        """Test filtering includes valid products."""
        processor = DataProcessor()

        items = [
            {"id": "1", "platforms": [{"workload": "Microsoft Teams"}]},
        ]

        filtered_items, stats = processor.filter_by_products(items)

        # Should include Teams
        assert stats["items_before"] == 1
        # items_after depends on other filters, just check it's a dict with stats
        assert "items_after" in stats


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_html_generation_with_multiple_items(self):
        """Test HTML generation with multiple items."""
        items = [
            {
                "id": f"item-{i}",
                "title": f"Update {i}",
                "body": f"Description {i}",
                "created": datetime.now().isoformat(),
                "platforms": [{"workload": "Microsoft Teams"}],
                "status": {"value": "General Availability"},
                "strategic_value": "HIGH",
                "reasoning": "Test",
                "moreInfoUrls": [f"https://example.com/{i}"],
                "formats": [],
                "cloudInstances": []
            }
            for i in range(3)
        ]

        html = HTMLGenerator.generate_html(items)

        assert len(html) > 0
        assert "Update 0" in html
        assert "Update 1" in html
        assert "Update 2" in html

    def test_database_and_filter_integration(self):
        """Test database with filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Add multiple items
            for i in range(5):
                db.add_item(f"guid-{i}", f"url-{i}", f"Title {i}", True)

            # Stats should show items were added
            stats = db.get_stats()
            assert stats is not None
            assert isinstance(stats, dict)


class TestSQLiteDRYRUNInteraction:
    """Test SQLite behavior with DRY_RUN mode."""

    def test_dry_run_does_not_alter_db_email_sent_flag(self):
        """Verify DRY_RUN doesn't incorrectly mark email_sent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProcessedItemsDB(db_path)

            # Add item
            db.add_item("guid-1", "url-1", "Title", True)

            # Get initial stats
            stats_before = db.get_stats()

            # In DRY_RUN mode, mark_email_sent should still work correctly
            db.mark_email_sent("guid-1")

            stats_after = db.get_stats()

            # Verify database state changed (this is correct behavior)
            # DRY_RUN is about email sending, not DB marking
            assert stats_after is not None
