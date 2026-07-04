"""Marketing agent."""

from __future__ import annotations

from typing import Any, Dict, List

from launchforge.agents.base import LaunchForgeAgent
from launchforge.sample_data import template_for
from launchforge.skills.funnel_skill import run_funnel_skill


class MarketingAgent(LaunchForgeAgent):
    name = "MarketingAgent"
    role = "Creates tailored channels, funnel, hooks, and outreach copy."

    def _messages(self, business_type: str) -> Dict[str, List[str]]:
        if business_type == "local_service":
            return {
                "hooks": ["From exam panic to a calm 4-week plan.", "Local, structured support with visible progress."],
                "social_posts": ["Opening 5 local diagnostic slots this week for students who want a clearer revision plan."],
                "whatsapp_email": ["Hi, I am opening a few local assessment slots. I can review current gaps, create a study plan, and explain the next step after one session."],
            }
        if business_type == "physical_retail":
            return {
                "hooks": ["Your 3-minute commuter stop for breakfast, snacks, and essentials.", "Fast local essentials before and after the train."],
                "social_posts": ["Morning bundle now available near the station: drink + breakfast snack for commuters in a hurry."],
                "whatsapp_email": ["We are mapping local essentials before opening. What one item should always be in stock for residents near the station?"],
            }
        if business_type == "ecommerce":
            return {
                "hooks": ["Affordable gym kit that survives real training.", "Build your starter gym bag without premium-brand pricing."],
                "social_posts": ["Testing our first gym accessory bundle. Comment 'KIT' if you want the launch discount and sizing guide."],
                "whatsapp_email": ["Thanks for joining the waitlist. Reply with your main training goal and we will send the best starter-kit recommendation."],
            }
        return {
            "hooks": ["A focused first offer for customers who need a faster result."],
            "social_posts": ["We are testing a new offer and looking for first users who want early access."],
            "whatsapp_email": ["Hi, I am validating a new launch offer and would value your feedback on the first version."],
        }

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        business_type = context["business_type"]
        channels = template_for(business_type)["channels"]
        funnel = run_funnel_skill(business_type, channels)
        return {
            "launch_channels": channels,
            "sales_funnel": funnel,
            "marketing_messages": self._messages(business_type),
        }
