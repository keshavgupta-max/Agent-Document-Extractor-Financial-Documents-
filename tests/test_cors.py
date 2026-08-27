"""Tests verifying CORS configuration and preflight behavior."""

from fastapi.testclient import TestClient
from app.main import app


def test_cors_headers_on_allowed_origin():
    """Verify preflight and standard requests from allowed origin receive CORS headers."""
    client = TestClient(app)

    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_options_preflight():
    """Verify OPTIONS preflight request succeeds with appropriate CORS headers."""
    client = TestClient(app)

    response = client.options(
        "/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_health_check_unaffected():
    """Verify health endpoint continues returning healthy status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}