"""Tests for content filtering module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rss_reader import RSSItem
from filter import ContentFilter


def test_filter_includes_exchange():
    """Test that items with Exchange Online are included."""
    entry = {
        "title": "New Exchange Online Features",
        "description": "Update about Exchange Online",
        "link": "https://example.com",
    }

    item = RSSItem(entry)
    filter_obj = ContentFilter()

    assert filter_obj.should_include(item) is True


def test_filter_includes_teams():
    """Test that items with Teams are included."""
    entry = {
        "title": "Microsoft Teams Improvements",
        "description": "New features in Teams",
        "link": "https://example.com",
    }

    item = RSSItem(entry)
    filter_obj = ContentFilter()

    assert filter_obj.should_include(item) is True


def test_filter_excludes_unrelated():
    """Test that unrelated items are excluded."""
    entry = {
        "title": "Power BI Updates",
        "description": "New Power BI features",
        "link": "https://example.com",
    }

    item = RSSItem(entry)
    filter_obj = ContentFilter()

    assert filter_obj.should_include(item) is False


def test_filter_reason_for_excluded():
    """Test that filter provides reason for exclusion."""
    entry = {
        "title": "Power BI Updates",
        "description": "New Power BI features",
        "link": "https://example.com",
    }

    item = RSSItem(entry)
    filter_obj = ContentFilter()

    reason = filter_obj.get_filter_reason(item)

    assert reason is not None
    assert "not in allowed list" in reason


def test_format_for_gemini():
    """Test formatting for Gemini."""
    entry = {
        "title": "Exchange Online Update",
        "description": "Description here",
        "link": "https://example.com",
        "tags": [{"term": "Available"}],
    }

    item = RSSItem(entry)
    formatted = ContentFilter.format_for_gemini(item)

    assert "PROYECTO:" in formatted
    assert "ESTADO:" in formatted
    assert "DESCRIPCIÓN:" in formatted
    assert "URL DE REFERENCIA:" in formatted


if __name__ == "__main__":
    test_filter_includes_exchange()
    test_filter_includes_teams()
    test_filter_excludes_unrelated()
    test_filter_reason_for_excluded()
    test_format_for_gemini()
    print("All filter tests passed!")
