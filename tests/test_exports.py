import json

from launchforge.export import export_json, export_markdown
from launchforge.schemas import BusinessInput
from launchforge.workflow import run_launchforge_workflow


def test_exports_include_core_sections():
    pack = run_launchforge_workflow(
        BusinessInput(
            idea="I want to start a cleaning service for local busy families.",
            budget=800,
            location="Local",
        )
    )
    markdown = export_markdown(pack)
    payload = json.loads(export_json(pack))
    assert "# LaunchForge Launch Pack" in markdown
    assert "Business Model Canvas" in markdown
    assert payload["classification"]["business_type"] == "local_service"


def test_export_json_is_valid_for_dict_pack():
    pack = {"classification": {"business_type": "unknown"}, "readiness_score": 50}
    payload = json.loads(export_json(pack))
    assert payload["readiness_score"] == 50
