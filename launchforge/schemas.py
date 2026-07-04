"""Pydantic schemas shared across agents, tools, UI, and exports."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BusinessType = Literal[
    "local_service",
    "physical_retail",
    "ecommerce",
    "digital_product",
    "food_drink",
    "b2b_service",
    "event_community",
    "unknown",
]


class BusinessInput(BaseModel):
    idea: str = Field(..., description="Raw business idea from the founder")
    budget: float = Field(default=1000, ge=0)
    location: str = Field(default="Online")
    founder_resources: str = Field(default="")
    timeframe: str = Field(default="30 days")
    stage: str = Field(default="Idea only")
    target_customer: Optional[str] = None
    privacy_mode: bool = True


class BusinessClassification(BaseModel):
    business_type: BusinessType
    confidence: float = Field(default=0.5, ge=0, le=1)
    reasoning: str
    assumptions: List[str] = Field(default_factory=list)


class CustomerPersona(BaseModel):
    name: str
    segment: str
    pains: List[str]
    goals: List[str]
    channels: List[str]
    buying_trigger: str


class OfferPackage(BaseModel):
    name: str
    description: str
    ideal_for: str
    deliverables: List[str]
    success_metric: str


class PricingTier(BaseModel):
    tier: str
    price: float
    unit: str
    includes: List[str]
    rationale: str


class CashflowMonth(BaseModel):
    month: int
    revenue: float
    costs: float
    net_cashflow: float
    cumulative_cashflow: float


class LaunchTask(BaseModel):
    day: int
    week: int
    title: str
    owner: str
    outcome: str
    category: str


class LaunchPack(BaseModel):
    input: BusinessInput
    classification: BusinessClassification
    readiness_score: int = Field(ge=0, le=100)
    readiness_breakdown: Dict[str, int]
    business_model_canvas: Dict[str, List[str]]
    personas: List[CustomerPersona]
    offer_ladder: List[OfferPackage]
    pricing: List[PricingTier]
    sales_funnel: Dict[str, Any]
    roadmap: List[LaunchTask]
    cashflow: List[CashflowMonth]
    startup_costs: Dict[str, float]
    breakeven_month: str
    operations_checklist: List[str]
    marketing_messages: Dict[str, List[str]]
    risks: List[str]
    assumptions: List[str]
    next_3_actions: List[str]
    critic_notes: List[str]
    diagrams: Dict[str, str]


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Pydantic v1/v2 compatible dict export."""

    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
