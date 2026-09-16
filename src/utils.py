"""Utility functions."""

from datetime import datetime, timedelta


def format_date(date: datetime, fmt: str = "%Y-%m-%d") -> str:
    """Format datetime object."""
    if not date:
        return "N/A"
    return date.strftime(fmt)


def get_cutoff_date(months_back: int = 1) -> datetime:
    """Get cutoff date for filtering."""
    return datetime.now() - timedelta(days=30 * months_back)


def sanitize_html(text: str) -> str:
    """Basic HTML escaping."""
    if not text:
        return ""
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
