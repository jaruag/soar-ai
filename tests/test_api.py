"""API tests for SOAR-AI, using FastAPI's test client.

These test the API's behaviour and shape of the responses, without
depending on a live scan or LLM call where we can avoid it.
"""

from fastapi.testclient import TestClient
import pytest

from api import app

client = TestClient(app)


def test_health_endpoint():
    """The health endpoint should report the service is up."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_serves_html():
    """The root should serve the web page, not JSON."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_scan_requires_package_and_version():
    """A scan request without the required fields should be rejected."""
    response = client.post("/scan", json={})

    # FastAPI returns 422 when the request body fails validation.
    assert response.status_code == 422

@pytest.mark.slow
def test_scan_defaults_to_pip():
    """The ecosystem field should default to pip when not provided."""
    # We only check the request is accepted and reaches the scan logic;
    # the actual scan may find nothing, which is fine for this test.
    response = client.post("/scan", json={"package": "nonexistent-xyz", "version": "0.0.0"})

    assert response.status_code == 200
    body = response.json()
    assert body["package"] == "nonexistent-xyz"
    assert "findings" in body

@pytest.mark.slow
def test_scan_npm_ecosystem():
    """A scan with ecosystem=npm should be accepted and reach the scan logic."""
    response = client.post("/scan", json={
        "package": "nonexistent-npm-xyz",
        "version": "0.0.0",
        "ecosystem": "npm",
    })
    assert response.status_code == 200
    assert response.json()["package"] == "nonexistent-npm-xyz"

@pytest.mark.slow
def test_scan_respects_limit():
    """The limit field should cap how many findings come back."""
    response = client.post("/scan", json={
        "package": "django",
        "version": "2.2.0",
        "ecosystem": "pip",
        "limit": 2,
    })
    assert response.status_code == 200
    body = response.json()
    # Django 2.2.0 has many findings; with limit=2 we expect at most 2.
    assert len(body["findings"]) <= 2


def test_history_endpoint():
    """The history endpoint returns a list (possibly empty)."""
    response = client.get("/history")
    assert response.status_code == 200
    assert "history" in response.json()
    assert isinstance(response.json()["history"], list)


def test_history_detail_not_found():
    """Requesting a non-existent scan id returns a graceful message, not a crash."""
    response = client.get("/history/999999")
    assert response.status_code == 200
    body = response.json()
    assert body["findings"] == []