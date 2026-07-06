import pytest

from launchforge.business_plan_export import (
    build_business_plan_dict,
    generate_business_plan_docx,
    generate_business_plan_markdown,
)
from launchforge.schemas import BusinessInput
from launchforge.workflow import run_launchforge_workflow


def test_business_plan_markdown_includes_template_sections():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to launch a Shopify store selling affordable gym accessories.",
            budget=1800,
            location="Online",
        )
    )
    markdown = generate_business_plan_markdown(pack)

    assert "Business plan generated using the King's Trust-style section structure." in markdown
    assert "## Section 1: Executive summary" in markdown
    assert "### 1.1 Business summary" in markdown
    assert "## Section 3: Products and services" in markdown
    assert "## Section 4: The market" in markdown
    assert "## Section 6: Marketing strategy" in markdown
    assert "## Section 10: Financial forecasts" in markdown
    assert "## Section 11: Back-up Plan" in markdown
    assert "Planning model only" in markdown


def test_business_plan_dict_handles_missing_optional_fields():
    plan = build_business_plan_dict(
        {
            "classification": {"business_type": "unknown", "confidence": 0.5, "matched_signals": []},
            "input": {"idea": "A small test business"},
            "cashflow": [],
            "startup_costs": {},
            "offer_ladder": [],
            "personas": [],
        }
    )

    assert plan["business_name"]
    assert plan["sections"]["2_owner_background"]["Qualifications and education"] == "To be completed by founder"
    assert len(plan["sections"]["10_financial_forecasts"]["10.1 Sales and costs forecast"]) == 12


def test_business_plan_docx_fails_gracefully_without_optional_dependency(tmp_path):
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to start a tutoring business helping GCSE students with Maths.",
            budget=600,
            location="Local area",
        )
    )
    try:
        import docx  # noqa: F401
    except ModuleNotFoundError:
        with pytest.raises(RuntimeError, match="python-docx"):
            generate_business_plan_docx(pack, output_path=str(tmp_path / "plan.docx"))
    else:
        path = generate_business_plan_docx(pack, output_path=str(tmp_path / "plan.docx"))
        assert path.endswith(".docx")
