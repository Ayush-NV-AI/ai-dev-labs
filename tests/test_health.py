"""Tests for the health check route."""


async def test_health_returns_200_ok(client):
    """GET /health returns 200 with a status body."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
