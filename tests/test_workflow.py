from launchforge.schemas import BusinessInput
from launchforge.workflow import run_launchforge_workflow, validate_launch_pack


def test_workflow_generates_complete_local_service_pack():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to start a tutoring business helping GCSE and A-Level students with Maths and Physics.",
            budget=600,
            location="Local",
            target_customer="Parents of GCSE students",
        )
    )
    assert pack.classification.business_type == "local_service"
    assert pack.readiness_score >= 60
    assert pack.readiness_score < 80
    assert sum(pack.readiness_breakdown.values()) == pack.readiness_score
    assert pack.currency_code == "GBP"
    assert pack.currency_symbol == "£"
    assert pack.business_model_canvas["Customer Segments"]
    assert "GCSE" in " ".join(pack.business_model_canvas["Value Propositions"])
    assert pack.readiness_strengths
    assert pack.readiness_gaps
    assert len(pack.next_3_actions) == 3
    assert validate_launch_pack(pack) is True


def test_workflow_adapts_physical_retail():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="Open a small corner shop near a train station selling snacks and breakfast items for commuters.",
            budget=12000,
            location="Station area",
        )
    )
    assert pack.classification.business_type == "physical_retail"
    assert any("stock" in item.lower() or "supplier" in item.lower() for item in pack.operations_checklist)


def test_workflow_adapts_ecommerce():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="Launch a Shopify store selling lifting straps, shaker bottles, and resistance bands.",
            budget=2500,
            location="Online",
        )
    )
    assert pack.classification.business_type == "ecommerce"
    assert any("samples" in item.lower() for item in pack.operations_checklist)


def test_demo_scenarios_are_clearly_different():
    tutoring = run_launchforge_workflow(
        BusinessInput(
            idea="I want to start a tutoring business helping GCSE and A-Level students with Maths, Physics, and admissions tests like ESAT. I want to start locally, keep costs low, and get my first 10 students.",
            budget=600,
            location="Local area",
        )
    )
    corner_shop = run_launchforge_workflow(
        BusinessInput(
            idea="I want to open a small corner shop near a train station selling snacks, drinks, essentials, and quick breakfast items for commuters and local residents.",
            budget=12000,
            location="Near a train station",
        )
    )
    shopify = run_launchforge_workflow(
        BusinessInput(
            idea="I want to launch a Shopify store selling affordable gym accessories like lifting straps, shaker bottles, resistance bands, and training notebooks.",
            budget=2500,
            location="Online",
        )
    )

    assert [tutoring.classification.business_type, corner_shop.classification.business_type, shopify.classification.business_type] == [
        "local_service",
        "physical_retail",
        "ecommerce",
    ]
    assert "booking" in " ".join(tutoring.operations_checklist).lower()
    assert "supplier" in " ".join(corner_shop.operations_checklist).lower()
    assert "product-page" in " ".join(shopify.operations_checklist).lower()
    assert len({tutoring.readiness_score, corner_shop.readiness_score, shopify.readiness_score}) > 1
    assert tutoring.pricing[0].tier != corner_shop.pricing[0].tier != shopify.pricing[0].tier
    assert tutoring.roadmap[0].outcome != corner_shop.roadmap[0].outcome != shopify.roadmap[0].outcome
    assert all("Evidence that" not in task.outcome for pack in [tutoring, corner_shop, shopify] for task in pack.roadmap)
    assert "local service customers" not in " ".join(tutoring.business_model_canvas["Value Propositions"]).lower()
    assert "flowchart TD" not in " ".join(tutoring.sales_funnel["stages"])


def test_cashflow_assumptions_and_agent_trace_present():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to launch a Shopify store selling affordable gym accessories.",
            budget=2500,
            location="Online",
        )
    )
    assert {"revenue", "costs", "conversion", "break_even"} <= set(pack.cashflow_assumptions)
    assert pack.forecast_disclaimer
    assert len(pack.agent_trace) >= 10
    assert any(item["agent"] == "LaunchForge Copilot Agent" for item in pack.agent_trace)
    assert any("Finance Agent" == item["agent"] for item in pack.agent_trace)
    assert any(item["name"] == "simulate_cashflow_scenarios" for item in pack.execution_trace)


