from launchforge.mcp_server.tools import classify_business_model


def test_classifier_local_service():
    result = classify_business_model("I want to start a tutoring business for GCSE maths students locally.")
    assert result["business_type"] == "local_service"
    assert 0.88 <= result["confidence"] <= 0.95
    assert result["matched_signals"]
    assert "founder-led" in " ".join(result["matched_signals"]).lower()
    assert "local service" in result["reasoning"].lower()


def test_classifier_physical_retail():
    result = classify_business_model("Open a small corner shop near a train station for commuters.")
    assert result["business_type"] == "physical_retail"
    assert any("footfall" in signal.lower() or "location" in signal.lower() for signal in result["matched_signals"])


def test_classifier_ecommerce():
    result = classify_business_model("Launch a Shopify store selling gym accessories with shipping.")
    assert result["business_type"] == "ecommerce"
    assert any("ecommerce" in signal.lower() or "product" in signal.lower() for signal in result["matched_signals"])
