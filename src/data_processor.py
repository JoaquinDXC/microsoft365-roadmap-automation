"""Deterministic data processing - no AI required."""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from logger import logger
from config import config


class DataProcessor:
    """Process roadmap data with deterministic rules (no AI)."""

    # Target products
    TARGET_PRODUCTS = {
        "Exchange Online",
        "Microsoft Teams",
        "SharePoint",
        "OneDrive",
        "OneDrive for Business"
    }

    # Product aliases for matching
    PRODUCT_ALIASES = {
        "teams": "Microsoft Teams",
        "sharepoint online": "SharePoint",
        "onedrive for business": "OneDrive for Business",
    }

    # Spanish translations for labels
    LABELS_ES = {
        "In development": "En desarrollo",
        "Launched": "Disponible",
        "Coming soon": "Proximamente",
        "Launched": "Disponible",
        "In rollout": "En despliegue",
    }

    STATUS_ES = {
        "In development": "En desarrollo",
        "Launched": "Disponible",
        "Coming soon": "Proximamente",
        "In rollout": "En despliegue",
    }

    @staticmethod
    def filter_by_date(items: List[Dict], months_back: int = 1) -> Tuple[List[Dict], Dict]:
        """Filter items by date (last X months)."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months_back)

        filtered_items = []
        date_field_usage = {"created": 0, "modified": 0, "no_date": 0}

        for item in items:
            item_id = item.get("id")

            # Prefer 'created', fallback to 'modified'
            date_str = item.get("created") or item.get("modified")

            if not date_str:
                date_field_usage["no_date"] += 1
                continue

            try:
                # Parse ISO 8601 date
                if item.get("created"):
                    item_date = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                    date_field_usage["created"] += 1
                else:
                    item_date = datetime.fromisoformat(item["modified"].replace("Z", "+00:00"))
                    date_field_usage["modified"] += 1

                if item_date >= cutoff_date:
                    filtered_items.append(item)

            except Exception as e:
                logger.warning(f"Failed to parse date for item {item_id}: {e}")
                date_field_usage["no_date"] += 1

        return filtered_items, {
            "cutoff_date": cutoff_date.isoformat(),
            "items_before": len(items),
            "items_after": len(filtered_items),
            "date_field_usage": date_field_usage
        }

    @staticmethod
    def filter_by_products(items: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Filter items by target products."""
        filtered_items = []
        products_found = {}

        for item in items:
            products = item.get("products", [])

            # Check if any product matches target
            match_found = False
            for product in products:
                if product in DataProcessor.TARGET_PRODUCTS:
                    match_found = True
                    products_found[product] = products_found.get(product, 0) + 1

            if match_found:
                filtered_items.append(item)

        return filtered_items, {
            "items_before": len(items),
            "items_after": len(filtered_items),
            "products_found": products_found
        }

    @staticmethod
    def process_batch(items: List[Dict]) -> Dict[str, Any]:
        """Process a batch of items with enrichment."""
        enriched_items = []

        for item in items:
            # Extract key fields
            enriched = {
                "id": item.get("id"),
                "title": item.get("title", "Unknown"),
                "description": item.get("description", ""),
                "products": item.get("products", []),
                "status": item.get("status", "Unknown"),
                "status_es": DataProcessor.STATUS_ES.get(item.get("status", "Unknown"), item.get("status", "Unknown")),
                "platforms": item.get("platforms", []),
                "platforms_formatted": ", ".join(item.get("platforms", [])) or "N/A",
                "cloud_instances": item.get("cloudInstances", []),
                "cloud_formatted": ", ".join(item.get("cloudInstances", [])) or "N/A",
                "release_rings": item.get("releaseRings", []),
                "ga_date": item.get("generalAvailabilityDate", "N/A"),
                "ga_date_formatted": DataProcessor._format_ga_date(item.get("generalAvailabilityDate", "")),
                "preview_date": item.get("previewAvailabilityDate", "N/A"),
                "preview_date_formatted": DataProcessor._format_ga_date(item.get("previewAvailabilityDate", "")),
                "created": item.get("created", ""),
                "modified": item.get("modified", ""),
                "more_info_urls": item.get("moreInfoUrls", []),
            }

            enriched_items.append(enriched)

        return {"items": enriched_items}

    @staticmethod
    def _format_ga_date(date_str: str) -> str:
        """Format GA date for display."""
        if not date_str or date_str == "N/A":
            return "N/A"

        try:
            # Handle YYYY-MM format
            if len(date_str) == 7:  # YYYY-MM
                dt = datetime.strptime(date_str, "%Y-%m")
                return dt.strftime("%B %Y")

            # Handle ISO format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%B %Y")
        except:
            return date_str

    @staticmethod
    def calculate_strategic_value(item: Dict) -> Dict:
        """Calculate strategic value score deterministically (no AI)."""
        score = 0
        reasoning = []

        # Normalize product name for checking
        products = item.get("products", [])
        products_str = " ".join(products).lower()

        # Check product criticality
        critical_products = ["microsoft teams", "exchange online", "sharepoint"]
        if any(cp.lower() in products_str for cp in critical_products):
            score += 2
            reasoning.append(f"Feature affects critical product: {', '.join(products)}")

        # Check status
        status = item.get("status", "").lower()
        if "launched" in status or "general availability" in status:
            score += 1
            reasoning.append("Feature is launched or GA")
        elif "coming soon" in status or "in rollout" in status:
            score += 1
            reasoning.append("Feature is rolling out soon")

        # Check GA date proximity
        ga_date = item.get("generalAvailabilityDate", "")
        if ga_date:
            try:
                if len(ga_date) == 7:  # YYYY-MM
                    ga_dt = datetime.strptime(ga_date, "%Y-%m")
                else:
                    ga_dt = datetime.fromisoformat(ga_date.replace("Z", "+00:00"))

                now = datetime.now(timezone.utc)
                if ga_dt.replace(tzinfo=timezone.utc) < now:
                    score += 1
                    reasoning.append("GA date has passed or is imminent")
                elif (ga_dt.replace(tzinfo=timezone.utc) - now).days < 90:
                    score += 1
                    reasoning.append(f"GA expected within 90 days")
            except:
                pass

        # Determine level
        if score >= 4:
            level = "HIGH"
        elif score >= 2:
            level = "MEDIUM"
        else:
            level = "INFORMATIVE"

        if not reasoning:
            reasoning.append("Standard roadmap item")

        return {
            "level": level,
            "score": score,
            "reasoning": reasoning,
            "deterministic": True,
            "note": "Assessed using deterministic rules (no AI)"
        }

    @staticmethod
    def assess_batch(items: List[Dict]) -> List[Dict]:
        """Assess strategic value for batch of items."""
        for item in items:
            item["strategic_value"] = DataProcessor.calculate_strategic_value(item)

        return items
