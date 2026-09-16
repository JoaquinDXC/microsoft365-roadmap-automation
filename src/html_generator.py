"""HTML email report generator."""

from typing import List, Dict
from logger import logger


class HTMLGenerator:
    """Generate professional HTML reports for email."""

    @staticmethod
    def generate_html(items: List[Dict], title: str = "Roadmap Microsoft 365") -> str:
        """Generate complete HTML report with all items."""

        html_parts = []

        # HTML Header
        html_parts.append("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microsoft 365 Roadmap</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 40px 20px;
        }
        .items-container {
            display: grid;
            gap: 20px;
        }
        .item-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .item-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .item-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            word-wrap: break-word;
        }
        .item-meta {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
            white-space: nowrap;
        }
        .badge-product {
            background: #667eea;
            color: white;
        }
        .badge-status {
            background: #f57c00;
            color: white;
        }
        .badge-value-high {
            background: #d32f2f;
            color: white;
        }
        .badge-value-medium {
            background: #f57c00;
            color: white;
        }
        .badge-value-low {
            background: #1976d2;
            color: white;
        }
        .item-description {
            color: #666;
            margin: 15px 0;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .item-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 15px 0;
            font-size: 0.9em;
        }
        .detail-item {
            display: flex;
            flex-direction: column;
        }
        .detail-label {
            color: #999;
            font-size: 0.85em;
            text-transform: uppercase;
            margin-bottom: 3px;
            font-weight: 600;
        }
        .detail-value {
            color: #333;
            font-weight: 500;
        }
        .value-reasoning {
            background: #f5f5f5;
            padding: 12px;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
        .value-reasoning strong {
            display: block;
            color: #333;
            margin-bottom: 5px;
        }
        .value-reasoning ul {
            margin-left: 20px;
            margin-top: 5px;
        }
        .value-reasoning li {
            margin: 3px 0;
        }
        .more-info {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .more-info:hover {
            background: #764ba2;
        }
        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.85em;
            border-top: 1px solid #e0e0e0;
        }
        .footer-note {
            margin-top: 10px;
            font-size: 0.8em;
            color: #bbb;
        }
        @media (max-width: 600px) {
            .header h1 { font-size: 1.5em; }
            .content { padding: 20px; }
            .item-details { grid-template-columns: 1fr; }
            .item-meta { flex-direction: column; }
            .badge { display: block; margin-bottom: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">""")

        # Header section
        html_parts.append(f"""
        <div class="header">
            <h1>{title}</h1>
            <p>Actualizacion de Roadmap - Microsoft 365</p>
        </div>

        <div class="content">
            <div class="items-container">""")

        # Items
        if not items:
            html_parts.append("""
                <div class="item-card">
                    <p>No hay elementos para mostrar en este periodo.</p>
                </div>""")
        else:
            for item in items:
                html_parts.append(HTMLGenerator._generate_item_card(item))

        # Footer
        html_parts.append("""
            </div>
        </div>

        <div class="footer">
            <p>Informe generado automaticamente desde Microsoft Release Communications MCP Server</p>
            <p class="footer-note">No se utilizaron servicios de IA. Todos los datos provienen directamente de Microsoft.</p>
        </div>
    </div>
</body>
</html>""")

        return "".join(html_parts)

    @staticmethod
    def _generate_item_card(item: Dict) -> str:
        """Generate HTML for a single item card."""

        title = item.get("title", "Unknown")
        description = item.get("description", "No description available")
        products = item.get("products", [])
        status = item.get("status", "Unknown")
        status_es = item.get("status_es", status)
        ga_date = item.get("ga_date_formatted", "N/A")
        preview_date = item.get("preview_date_formatted", "N/A")
        platforms = item.get("platforms_formatted", "N/A")
        cloud = item.get("cloud_formatted", "N/A")
        more_info_urls = item.get("more_info_urls", [])
        strategic_value = item.get("strategic_value", {})

        # Generate product badges
        product_badges = "".join([
            f'<span class="badge badge-product">{p}</span>'
            for p in products
        ])

        # Generate status badge
        status_badge = f'<span class="badge badge-status">{status_es}</span>'

        # Generate value badge
        value_level = strategic_value.get("level", "INFORMATIVE").lower()
        value_badge = f'<span class="badge badge-value-{value_level}">{strategic_value.get("level", "N/A")}</span>'

        # Generate value reasoning
        reasoning_items = strategic_value.get("reasoning", [])
        reasoning_html = ""
        if reasoning_items:
            reasoning_html = f"""
            <div class="value-reasoning">
                <strong>Importancia Estrategica:</strong>
                <ul>"""
            for reason in reasoning_items:
                reasoning_html += f"<li>{reason}</li>"
            reasoning_html += "</ul></div>"

        # Generate more info link
        more_info_html = ""
        if more_info_urls and more_info_urls[0]:
            url = more_info_urls[0]
            more_info_html = f'<a href="{url}" class="more-info" target="_blank">Mas informacion</a>'

        # Truncate description for display
        desc_display = (description[:250] + "...") if len(description) > 250 else description

        card = f"""
                <div class="item-card">
                    <div class="item-title">{title}</div>
                    <div class="item-meta">
                        {product_badges}
                        {status_badge}
                        {value_badge}
                    </div>
                    <div class="item-description">{desc_display}</div>
                    <div class="item-details">
                        <div class="detail-item">
                            <span class="detail-label">Disponibilidad General</span>
                            <span class="detail-value">{ga_date}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Preview</span>
                            <span class="detail-value">{preview_date}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Plataformas</span>
                            <span class="detail-value">{platforms}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Instancia Cloud</span>
                            <span class="detail-value">{cloud}</span>
                        </div>
                    </div>
                    {reasoning_html}
                    {more_info_html}
                </div>"""

        return card
