"""Renderers for strategy table output."""

from dataclasses import dataclass, field
from typing import Protocol

from tabulate import tabulate


@dataclass
class TableData:
    """Data structure for a single strategy table."""

    title: str
    headers: list[str]
    rows: list[list[str]]


@dataclass
class StrategyData:
    """Complete strategy data for rendering."""

    config_description: str
    hard_table: TableData
    soft_table: TableData
    pair_table: TableData
    legend: str = field(
        default="S=Stand, H=Hit, Dh=Double/Hit, Ds=Double/Stand, P=Split"
    )


class Renderer(Protocol):
    """Protocol for strategy table renderers."""

    def render(self, data: StrategyData) -> str:
        """Render strategy tables to string output."""
        ...


class TextRenderer:
    """Render strategy tables as ASCII text using tabulate."""

    def __init__(self, tablefmt: str = "simple_grid"):
        self.tablefmt = tablefmt

    def render(self, data: StrategyData) -> str:
        """Render all tables as formatted text."""
        sections = [
            f"Basic Strategy: {data.config_description}",
            "",
            "HARD TOTALS",
            self._render_table(data.hard_table),
            "",
            "SOFT TOTALS",
            self._render_table(data.soft_table),
            "",
            "PAIRS",
            self._render_table(data.pair_table),
            "",
            f"Legend: {data.legend}",
        ]
        return "\n".join(sections)

    def _render_table(self, table: TableData) -> str:
        return tabulate(
            table.rows,
            headers=table.headers,
            tablefmt=self.tablefmt,
            stralign="center",
        )


class HTMLRenderer:
    """Render strategy tables as standalone HTML with color-coded cells."""

    ACTION_CLASSES = {
        "S": "stand",
        "H": "hit",
        "D": "double",
        "Dh": "double",
        "Ds": "double",
        "P": "split",
        "Ph": "split",
    }

    def render(self, data: StrategyData) -> str:
        """Render complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blackjack Basic Strategy</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <h1>Blackjack Basic Strategy</h1>
        <p class="config">{data.config_description}</p>

        <h2>Hard Totals</h2>
        {self._render_table(data.hard_table)}

        <h2>Soft Totals</h2>
        {self._render_table(data.soft_table)}

        <h2>Pairs</h2>
        {self._render_table(data.pair_table)}

        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-items">
                <span class="legend-item stand">S = Stand</span>
                <span class="legend-item hit">H = Hit</span>
                <span class="legend-item double">D/Dh/Ds = Double</span>
                <span class="legend-item split">P = Split</span>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        return """\
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 5px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .config {
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            margin: 15px 0;
            width: 100%;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 10px 8px;
            text-align: center;
            font-size: 14px;
        }
        th {
            background-color: #f8f8f8;
            font-weight: 600;
        }
        .row-header {
            background-color: #f8f8f8;
            font-weight: 600;
        }
        .stand { background-color: #90EE90; }
        .hit { background-color: #FFB6C1; }
        .double { background-color: #FFFF99; }
        .split { background-color: #ADD8E6; }
        .legend {
            margin-top: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        .legend h3 {
            margin-top: 0;
            color: #555;
        }
        .legend-items {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .legend-item {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
        }"""

    def _render_table(self, table: TableData) -> str:
        html = ['<table>', '<thead><tr>']

        for header in table.headers:
            html.append(f"<th>{header}</th>")
        html.append("</tr></thead>")

        html.append("<tbody>")
        for row in table.rows:
            html.append("<tr>")
            html.append(f'<td class="row-header">{row[0]}</td>')
            for cell in row[1:]:
                css_class = self.ACTION_CLASSES.get(cell, "")
                html.append(f'<td class="{css_class}">{cell}</td>')
            html.append("</tr>")
        html.append("</tbody></table>")

        return "\n".join(html)
