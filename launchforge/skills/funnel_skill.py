"""Sales funnel skill used by the MarketingAgent and VisualPackAgent."""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.mcp_server.tools import generate_sales_funnel


def run_funnel_skill(business_type: str, channels: List[str]) -> Dict[str, Any]:
    """Create a tailored funnel model for the classified business type."""

    return generate_sales_funnel(business_type, channels)
