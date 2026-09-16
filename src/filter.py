"""Content filtering for allowed Microsoft 365 products."""

from typing import Optional
from rss_reader import RSSItem
from config import config
from logger import logger


class ContentFilter:
    """Filters RSS items by product and relevance."""

    def __init__(self, allowed_products: set[str] = config.ALLOWED_PRODUCTS):
        """
        Initialize filter.

        Args:
            allowed_products: Set of allowed product names (lowercase)
        """
        self.allowed_products = allowed_products

    def should_include(self, item: RSSItem) -> bool:
        """
        Check if item should be included based on product filter.

        Args:
            item: RSS item to check

        Returns:
            True if item should be included
        """
        combined_text = self._get_searchable_text(item)

        # Check if any allowed product is mentioned
        for product in self.allowed_products:
            if product.lower() in combined_text.lower():
                return True

        return False

    def get_filter_reason(self, item: RSSItem) -> Optional[str]:
        """
        Get reason why item was filtered out.

        Args:
            item: RSS item

        Returns:
            Reason string if filtered out, None if included
        """
        if self.should_include(item):
            return None
        return "Product not in allowed list (Exchange, Teams, SharePoint, OneDrive)"

    @staticmethod
    def _get_searchable_text(item: RSSItem) -> str:
        """Combine all searchable text from item."""
        text_parts = [
            str(item.title or ""),
            str(item.description or ""),
            str(item.summary or ""),
        ]

        # Add categories (convert to strings)
        if item.categories:
            for cat in item.categories:
                if isinstance(cat, dict):
                    # FeedParserDict: extract term or use str()
                    cat_text = cat.get("term", "") or str(cat)
                else:
                    cat_text = str(cat)
                text_parts.append(cat_text)

        return " ".join(text_parts)

    @staticmethod
    def format_for_gemini(item: RSSItem) -> str:
        """
        Format item for Gemini processing.

        Args:
            item: RSS item

        Returns:
            Formatted text block
        """
        date_str = ""
        if item.date_created:
            date_str = item.date_created.strftime("%Y-%m-%d")
        elif item.date_updated:
            date_str = item.date_updated.strftime("%Y-%m-%d")

        # Convert categories to strings
        categories_list = []
        if item.categories:
            for cat in item.categories:
                if isinstance(cat, dict):
                    cat_text = cat.get("term", "") or str(cat)
                else:
                    cat_text = str(cat)
                if cat_text:
                    categories_list.append(cat_text)

        categories_str = ", ".join(categories_list) if categories_list else "Sin categoría"

        return f"""PROYECTO: {item.title}
ESTADO: {categories_str}
DESCRIPCIÓN: {item.description}
FECHA DE PUBLICACIÓN: {date_str}
URL DE REFERENCIA: {item.url}
---"""

    @staticmethod
    def format_all_for_gemini(items: list[RSSItem]) -> str:
        """
        Format multiple items for Gemini processing.

        Args:
            items: List of RSS items

        Returns:
            Combined formatted text
        """
        formatted_items = [ContentFilter.format_for_gemini(item) for item in items]
        return "\n".join(formatted_items)


def filter_items(items: list[RSSItem]) -> tuple[list[RSSItem], dict]:
    """
    Filter RSS items by product.

    Args:
        items: List of RSS items to filter

    Returns:
        Tuple of (included_items, filter_stats)
    """
    filter_obj = ContentFilter()
    included = []
    filtered = []

    for item in items:
        if filter_obj.should_include(item):
            included.append(item)
        else:
            filtered.append(item)
            logger.debug(f"Filtered out: {item.title}")

    stats = {
        "total": len(items),
        "included": len(included),
        "filtered": len(filtered),
        "products": list(config.ALLOWED_PRODUCTS),
    }

    logger.info(f"Filtering complete: {stats['included']} included, {stats['filtered']} filtered")

    return included, stats
