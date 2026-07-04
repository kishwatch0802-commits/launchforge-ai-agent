from launchforge.mcp_server.tools import classify_business_model


def test_classifier_local_service():
    result = classify_business_model("I want to start a tutoring business for GCSE maths students locally.")
    assert result["business_type"] == "local_service"
    assert result["confidence"] > 0.5


def test_classifier_physical_retail():
    result = classify_business_model("Open a small corner shop near a train station for commuters.")
    assert result["business_type"] == "physical_retail"


def test_classifier_ecommerce():
    result = classify_business_model("Launch a Shopify store selling gym accessories with shipping.")
    assert result["business_type"] == "ecommerce"
