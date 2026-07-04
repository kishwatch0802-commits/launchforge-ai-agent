"""Export skill used by the Streamlit app and MCP export tool."""

from __future__ import annotations

from typing import Any, Dict

from launchforge.export import export_json, export_markdown


def run_export_skill(pack: Dict[str, Any], format: str = "markdown") -> str:
    """Export a launch pack in markdown or JSON without storing user input."""

    return export_json(pack) if format.lower() == "json" else export_markdown(pack)
