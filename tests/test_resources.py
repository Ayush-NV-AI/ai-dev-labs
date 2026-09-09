"""Tests for the resources routes and service."""

import pytest

from src.services.errors import NotFound
from src.services.resources import ResourceService, SqlAlchemyResourceRepository


async def test_list_resources_empty(client):
    """GET /resources returns an empty list when none exist."""
    response = await client.get("/resources")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_and_get_resource_round_trip(client, db_session_instance, resource_factory):
    """A created resource is returned by both list and get-by-id."""
    resource = resource_factory(name="Studio A")
    db_session_instance.add(resource)
    await db_session_instance.commit()
    await db_session_instance.refresh(resource)

    list_response = await client.get("/resources")
    assert list_response.status_code == 200
    assert [r["name"] for r in list_response.json()] == ["Studio A"]

    get_response = await client.get(f"/resources/{resource.id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["id"] == resource.id
    assert body["name"] == "Studio A"
    assert body["kind"] == "room"
    assert body["capacity"] == 4
    assert body["is_active"] is True


async def test_get_resource_404_envelope(client):
    """GET /resources/{id} for a missing id returns the standard envelope."""
    response = await client.get("/resources/999")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "999" in body["error"]["message"]


async def test_service_get_resource_raises_not_found(db_session_instance):
    """ResourceService.get_resource raises NotFound for a missing id."""
    service = ResourceService(SqlAlchemyResourceRepository(db_session_instance))

    with pytest.raises(NotFound):
        await service.get_resource(12345)


async def test_service_list_resources_orders_by_id(db_session_instance, resource_factory):
    """ResourceService.list_resources returns resources ordered by id."""
    first = resource_factory(name="A")
    second = resource_factory(name="B")
    db_session_instance.add_all([first, second])
    await db_session_instance.commit()

    service = ResourceService(SqlAlchemyResourceRepository(db_session_instance))
    resources = await service.list_resources()

    assert [r.name for r in resources] == ["A", "B"]
