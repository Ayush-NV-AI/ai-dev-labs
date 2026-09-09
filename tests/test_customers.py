"""Tests for the customers routes and service."""

import pytest

from src.services.customers import CustomerService, SqlAlchemyCustomerRepository
from src.services.errors import NotFound


async def test_list_customers_empty(client):
    """GET /customers returns an empty list when none exist."""
    response = await client.get("/customers")

    assert response.status_code == 200
    assert response.json() == []


async def test_get_customer_returns_resolved_tier(
    client, db_session_instance, customer_factory
):
    """GET /customers/{id} returns the customer with its tier resolved."""
    customer = customer_factory(name="Grace Hopper", tier="gold")
    db_session_instance.add(customer)
    await db_session_instance.commit()
    await db_session_instance.refresh(customer)

    response = await client.get(f"/customers/{customer.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Grace Hopper"
    assert body["tier"] == "gold"


async def test_get_customer_404_envelope(client):
    """GET /customers/{id} for a missing id returns the standard envelope."""
    response = await client.get("/customers/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_service_get_customer_raises_not_found(db_session_instance):
    """CustomerService.get_customer raises NotFound for a missing id."""
    service = CustomerService(SqlAlchemyCustomerRepository(db_session_instance))

    with pytest.raises(NotFound):
        await service.get_customer(12345)


async def test_resolve_tier_returns_recognised_tier_unchanged(
    db_session_instance, customer_factory
):
    """A recognised tier is returned as-is."""
    service = CustomerService(SqlAlchemyCustomerRepository(db_session_instance))
    customer = customer_factory(tier="silver")

    assert service.resolve_tier(customer) == "silver"


async def test_resolve_tier_falls_back_to_standard_for_unknown_value(
    db_session_instance, customer_factory
):
    """An unrecognised stored tier resolves down to 'standard'."""
    service = CustomerService(SqlAlchemyCustomerRepository(db_session_instance))
    customer = customer_factory(tier="platinum-legacy-typo")

    assert service.resolve_tier(customer) == "standard"
