"""Main workflow orchestration using MRC MCP (no Gemini)."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import config, ConfigError
from logger import logger
from mcp_client import MCPClient
from data_processor import DataProcessor
from html_generator import HTMLGenerator
from email_sender import send_roadmap_email
from database import ProcessedItemsDB


async def run_automation() -> int:
    """
    Run the complete automation workflow using MRC MCP.

    Workflow:
    1. Connect to MRC MCP
    2. Fetch roadmaps (paginated)
    3. Filter by date (last 30 days)
    4. Filter by products
    5. Check for duplicates
    6. Fetch full details
    7. Process deterministically
    8. Generate HTML
    9. Send email

    Returns:
        Exit code (0 for success, 1 for error)
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("M365 Roadmap Automation Started (MRC MCP)")
    logger.info("=" * 60)

    try:
        # Validate configuration
        config.ensure_directories()

        # Initialize database
        db = ProcessedItemsDB()

        # STEP 1: Connect to MRC MCP and discover tools
        logger.info("STEP 1: Connecting to MRC MCP Server")
        mcp_client = MCPClient()

        tools = await mcp_client.discover_tools()
        if not tools:
            logger.error("Failed to discover MCP tools")
            return 1

        logger.info(f"  Discovered {len(tools)} MCP tools")
        tool_names = [t.get("name") for t in tools]
        logger.debug(f"  Available tools: {tool_names}")

        # STEP 2: Fetch all roadmaps with pagination
        logger.info("STEP 2: Fetching roadmaps from MCP (paginated)")

        all_items = []
        page = 0
        has_more = True

        while has_more and page < 50:  # Safety limit
            logger.debug(f"  Fetching page {page + 1}...")

            result = await mcp_client.get_recent_roadmaps(skip=page * 50)

            if "error" in result:
                logger.error(f"Failed to fetch roadmaps: {result['error']}")
                return 1

            items = result.get("items", [])
            all_items.extend(items)
            has_more = result.get("hasMore", False)

            if page % 5 == 0:
                logger.info(f"  Page {page + 1}: {len(items)} items (total: {len(all_items)})")

            page += 1
            await asyncio.sleep(0.1)  # Rate limiting

        logger.info(f"Total items fetched: {len(all_items)} from {page} pages")

        if not all_items:
            logger.warning("No items fetched from MCP")
            return 1

        # STEP 3: Filter by date
        logger.info("STEP 3: Filtering by date (last 30 days)")

        date_filtered, date_info = DataProcessor.filter_by_date(
            all_items,
            months_back=config.RSS_MONTHS_BACK
        )

        logger.info(f"  After date filter: {date_info['items_after']} items")
        logger.debug(f"  Date field usage: {date_info['date_field_usage']}")

        if not date_filtered:
            logger.info("No items matched date filter")
            return 0

        # STEP 4: Filter by products
        logger.info("STEP 4: Filtering by products")

        product_filtered, product_info = DataProcessor.filter_by_products(date_filtered)

        logger.info(f"  After product filter: {product_info['items_after']} items")
        for product, count in product_info['products_found'].items():
            logger.debug(f"    {product}: {count}")

        if not product_filtered:
            logger.info("No items matched product filter")
            return 0

        # STEP 5: Check for duplicates
        logger.info("STEP 5: Checking for new items")

        new_items = []
        for item in product_filtered:
            item_id = str(item.get("id"))

            if not db.item_exists(item_id):
                new_items.append(item)
            else:
                logger.debug(f"Item already processed: {item.get('title', '')[:50]}")

        logger.info(f"  New items: {len(new_items)} (already processed: {len(product_filtered) - len(new_items)})")

        if not new_items:
            logger.info("No new items to process")
            return 0

        # STEP 6: Fetch full details for new items
        logger.info("STEP 6: Fetching full details from MCP")

        full_items = []
        for idx, item in enumerate(new_items):
            item_id = item.get("id")

            result = await mcp_client.get_roadmap_by_id(item_id)

            if "error" not in result:
                full_items.append(result)
            else:
                logger.warning(f"Failed to fetch details for item {item_id}: {result.get('error')}")

            if (idx + 1) % 10 == 0:
                logger.debug(f"  Fetched details for {idx + 1}/{len(new_items)} items")

            await asyncio.sleep(0.05)  # Rate limiting

        logger.info(f"  Fetched full details for {len(full_items)} items")

        if not full_items:
            logger.error("Failed to fetch details for any items")
            return 1

        # STEP 7: Process deterministically (no AI)
        logger.info("STEP 7: Processing items (deterministic, no AI)")

        processing_result = DataProcessor.process_batch(full_items)
        processed_items = processing_result["items"]

        # Add strategic value assessment
        processed_items = DataProcessor.assess_batch(processed_items)

        logger.info(f"  Processed {len(processed_items)} items")

        # STEP 8: Generate HTML
        logger.info("STEP 8: Generating HTML email")

        html_content = HTMLGenerator.generate_html(processed_items)

        logger.debug(f"  HTML generated ({len(html_content)} bytes)")

        # Save HTML preview for visual inspection (always, for DRY_RUN and regular)
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        preview_file = output_dir / "roadmap_preview.html"

        try:
            with open(preview_file, "w", encoding="utf-8") as f:
                # Write complete HTML document
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microsoft 365 Roadmap Update - Preview</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif;">
    <div style="max-width: 900px; margin: 0 auto;">
        <div style="background-color: #f3f3f3; padding: 20px; text-align: center; border-bottom: 3px solid #0078d4;">
            <h1 style="color: #0078d4; margin: 0; font-size: 28px;">Microsoft 365 Roadmap Update</h1>
            <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">Preview - {len(processed_items)} Items</p>
            <p style="color: #999; margin: 5px 0 0 0; font-size: 12px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div style="padding: 20px;">
            {html_content}
        </div>

        <div style="background-color: #f3f3f3; padding: 15px; text-align: center; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <p style="margin: 0;">
                This is a visual preview of the roadmap update.<br>
                Open this file in your browser to review the content.
            </p>
        </div>
    </div>
</body>
</html>""")
            logger.info(f"  HTML preview saved to: {preview_file.absolute()}")
        except Exception as e:
            logger.warning(f"Failed to save HTML preview: {e}")

        # CRITICAL: Save items to DB BEFORE sending email
        # This ensures we never reprocess items even if email fails
        logger.info("Saving items to database")
        for item in new_items:
            db.add_item(
                guid=str(item.get("id")),
                url=item.get("moreInfoUrls", [""])[0] if item.get("moreInfoUrls") else "",
                title=item.get("title", "Unknown"),
                included=True,
            )

        # STEP 9: Send email
        logger.info("STEP 9: Sending email")

        try:
            email_sent = await send_roadmap_email(html_content)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            logger.warning("Email send failed but items were saved to DB")
            return 1

        if not email_sent:
            logger.error("Email was not sent successfully")
            logger.warning("Email send failed but items were saved to DB")
            return 1

        # Mark items as email_sent only if email was ACTUALLY sent (not in DRY_RUN mode)
        for item in new_items:
            if not config.DRY_RUN:
                db.mark_email_sent(str(item.get("id")))
            else:
                logger.info(f"  DRY_RUN: Item '{item.get('title')}' not marked as email_sent")

        # Success
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("M365 Roadmap Automation Completed Successfully")
        logger.info(f"Elapsed time: {elapsed:.2f}s")
        logger.info("=" * 60)

        # Log summary
        db_stats = db.get_stats()
        logger.info("Database statistics (last 30 days):")
        logger.info(f"  Total processed: {db_stats.get('total', 0)}")
        logger.info(f"  Included in reports: {db_stats.get('included', 0)}")
        logger.info(f"  Filtered out: {db_stats.get('filtered', 0)}")
        logger.info(f"  Email sent: {db_stats.get('email_sent', 0)}")

        # Show HTML preview path
        preview_path = Path("output") / "roadmap_preview.html"
        if preview_path.exists():
            logger.info("")
            logger.info("HTML Preview:")
            logger.info(f"  File: {preview_path.absolute()}")
            logger.info(f"  Size: {preview_path.stat().st_size} bytes")
            logger.info("")
            logger.info("To view the email preview, open this file in your browser:")
            logger.info(f"  {preview_path.absolute()}")

        # Show DRY_RUN status
        if config.DRY_RUN:
            logger.info("")
            logger.info("DRY_RUN MODE: Email was NOT sent")
            logger.info("Items were NOT marked as email_sent in SQLite")

        return 0

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
