"""Deterministic business templates used when no LLM is configured.

The templates are intentionally opinionated so the capstone demo produces
specific launch packs rather than vague business-advice text.
"""

from __future__ import annotations

from typing import Any, Dict, List


KEYWORDS = {
    "local_service": [
        "tutor",
        "tuition",
        "cleaning",
        "photography",
        "coaching",
        "repair",
        "landscaping",
        "consultation",
        "mobile",
        "appointment",
        "students",
    ],
    "physical_retail": [
        "corner shop",
        "barber",
        "cafe",
        "store",
        "shop",
        "retail",
        "commuters",
        "footfall",
        "shelves",
        "premises",
        "train station",
    ],
    "ecommerce": [
        "shopify",
        "ecommerce",
        "e-commerce",
        "online store",
        "product",
        "fulfilment",
        "dropship",
        "brand",
        "accessories",
        "shipping",
    ],
    "digital_product": ["course", "template", "download", "saas", "app", "newsletter"],
    "food_drink": ["restaurant", "food truck", "bakery", "meal", "drinks", "coffee"],
    "b2b_service": ["agency", "b2b", "software consulting", "lead generation", "crm"],
    "event_community": ["event", "community", "workshop", "meetup", "club"],
}


TYPE_LABELS = {
    "local_service": "Local Service",
    "physical_retail": "Physical Retail",
    "ecommerce": "E-commerce",
    "digital_product": "Digital Product",
    "food_drink": "Food & Drink",
    "b2b_service": "B2B Service",
    "event_community": "Event / Community",
    "unknown": "Unknown",
}


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "local_service": {
        "personas": [
            {
                "name": "Busy Parent Priya",
                "segment": "Parent arranging outcomes for a child",
                "pains": ["Worries about exam confidence", "Needs trusted local proof", "Limited time to compare options"],
                "goals": ["Visible progress in 4 weeks", "Simple booking", "Clear communication"],
                "channels": ["Local Facebook groups", "School parent WhatsApp", "Referrals"],
                "buying_trigger": "A mock result, missed grade, or recommendation from another parent.",
            },
            {
                "name": "Focused Student Sam",
                "segment": "Motivated student who wants structured support",
                "pains": ["Feels stuck on hard topics", "Does not know what to revise next"],
                "goals": ["Raise grades", "Get a repeatable study plan", "Feel calmer before exams"],
                "channels": ["TikTok search", "Instagram", "School networks"],
                "buying_trigger": "Upcoming test date creates urgency.",
            },
        ],
        "offer": [
            ("Starter Diagnostic", "A low-risk first session that diagnoses gaps and sets a plan.", "New leads", ["45-minute assessment", "Personal action plan", "Parent/student summary"], "Lead books a paid follow-up"),
            ("Core Weekly Package", "A repeatable weekly service package with progress reporting.", "Committed customers", ["Weekly session", "Practice tasks", "Progress tracker"], "4-week retention"),
            ("Exam Sprint", "A premium short sprint for urgent outcomes.", "High-intent customers", ["2 sessions per week", "Past-paper plan", "Final checklist"], "Improved mock score"),
        ],
        "channels": ["Referrals", "Google Business Profile", "Local groups", "WhatsApp follow-up", "Testimonials"],
        "operations": ["Create booking calendar and intake form", "Prepare reusable diagnostic checklist", "Set response SLA under 12 hours", "Request testimonial after second successful session", "Track leads in a simple CRM sheet"],
        "risks": ["Lead flow depends on local trust signals.", "Founder time caps revenue unless packages are productised.", "Safeguarding and cancellation policies must be explicit."],
    },
    "physical_retail": {
        "personas": [
            {
                "name": "Commuter Callum",
                "segment": "Daily commuter buying fast convenience items",
                "pains": ["Queues are slow", "Breakfast options run out", "Prices are unclear"],
                "goals": ["Grab items in under 3 minutes", "Reliable opening hours", "Good morning bundle"],
                "channels": ["Station signage", "Google Maps", "Window offers"],
                "buying_trigger": "Morning commute or evening top-up shop.",
            },
            {
                "name": "Local Resident Lina",
                "segment": "Nearby resident needing essentials",
                "pains": ["Does not want a supermarket trip", "Needs predictable stock"],
                "goals": ["Essentials close by", "Friendly service", "Occasional local deals"],
                "channels": ["Leaflets", "Local WhatsApp groups", "In-store prompts"],
                "buying_trigger": "Running out of household basics.",
            },
        ],
        "offer": [
            ("Commuter Morning Bundle", "Coffee or drink plus breakfast/snack combo at a fast price point.", "Commuters", ["Hero bundle", "Counter display", "Morning signage"], "Repeat morning visits"),
            ("Essentials Wall", "High-frequency household basics grouped near the entrance.", "Local residents", ["Milk/bread/eggs", "Toiletries", "Phone chargers"], "Basket size"),
            ("Local Loyalty Stamp", "Simple loyalty offer for repeat footfall.", "Regular shoppers", ["Stamp card", "Weekly deal", "Referral prompt"], "Weekly repeat purchases"),
        ],
        "channels": ["Window signage", "Google Maps", "Station leaflet", "Local partnerships", "In-store upsells"],
        "operations": ["Map supplier list by category", "Define opening-hour rota", "Set reorder points for fast movers", "Plan store layout for speed", "Run daily cash-up and shrinkage check"],
        "risks": ["Stockouts on fast movers hurt trust.", "Footfall assumptions need validation at specific hours.", "Waste and shrinkage can quietly erase margin."],
    },
    "ecommerce": {
        "personas": [
            {
                "name": "Budget Lifter Ben",
                "segment": "Gym user who wants functional accessories without premium prices",
                "pains": ["Cheap products break", "Reviews feel fake", "Shipping uncertainty"],
                "goals": ["Reliable basics", "Clear sizing/use cases", "Fast delivery"],
                "channels": ["TikTok", "Instagram Reels", "Reddit/search", "YouTube Shorts"],
                "buying_trigger": "New training goal or replacing worn gear.",
            },
            {
                "name": "Starter Athlete Amira",
                "segment": "Beginner building a first gym kit",
                "pains": ["Overwhelmed by options", "Does not know what matters"],
                "goals": ["Starter bundle", "Simple guidance", "Good value"],
                "channels": ["Search", "Influencer recommendations", "Email offers"],
                "buying_trigger": "Joining a gym or starting a programme.",
            },
        ],
        "offer": [
            ("Hero Product", "One validated product page with clear benefits and proof.", "Cold traffic", ["Strong product page", "FAQ", "Guarantee"], "Add-to-cart rate"),
            ("Starter Bundle", "Bundled accessories that raise average order value.", "New customers", ["3-5 product bundle", "Savings anchor", "Usage guide"], "AOV above target"),
            ("Repeat Kit", "Email/SMS follow-up with replacement or companion items.", "Existing customers", ["Post-purchase flow", "Review request", "Cross-sell"], "Second purchase rate"),
        ],
        "channels": ["TikTok testing", "SEO product pages", "Email capture", "Micro-influencers", "Retargeting"],
        "operations": ["Validate supplier lead times", "Order samples before launch", "Set product-page QA checklist", "Define returns policy", "Track CAC, AOV, conversion rate, and gross margin"],
        "risks": ["Supplier quality must be verified with samples.", "Paid ads can spend faster than conversion learning.", "Generic products need strong positioning and proof."],
    },
}


GENERIC_TEMPLATE = {
    "personas": [
        {
            "name": "Early Adopter Alex",
            "segment": "Customer with an urgent problem and willingness to test",
            "pains": ["Current options feel inefficient", "Hard to judge quality before buying"],
            "goals": ["Quick proof of value", "Low-risk trial", "Clear next step"],
            "channels": ["Search", "Referrals", "Social proof"],
            "buying_trigger": "A near-term problem makes the status quo expensive.",
        }
    ],
    "offer": [
        ("Validation Offer", "A simple paid pilot that proves demand.", "First customers", ["Clear promise", "Defined scope", "Feedback call"], "First 3 paid customers"),
        ("Core Offer", "The repeatable package to sell after validation.", "Main market", ["Outcome", "Delivery process", "Support"], "Repeatable fulfilment"),
        ("Premium Add-on", "A higher-touch option for customers who want speed.", "Best-fit customers", ["Priority support", "Customisation", "Review"], "Higher margin"),
    ],
    "channels": ["Direct outreach", "Content", "Referrals"],
    "operations": ["Define the promise", "Create intake process", "Track leads and customer feedback"],
    "risks": ["The business type needs sharper validation before investing heavily."],
}


def template_for(business_type: str) -> Dict[str, Any]:
    return TEMPLATES.get(business_type, GENERIC_TEMPLATE)


def type_label(business_type: str) -> str:
    return TYPE_LABELS.get(business_type, business_type.replace("_", " ").title())
