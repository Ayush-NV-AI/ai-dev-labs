"""Tests for the orders routes and service."""

from decimal import Decimal

import pytest

from src.services.customers import SqlAlchemyCustomerRepository
from src.services.errors import NotFound
from src.services.orders import OrderLineInput, OrderService, SqlAlchemyOrderRepository


async def _seed_customer(db_session_instance, customer_factory):
    customer = customer_factory()
    db_session_instance.add(customer)
    await db_session_instance.commit()
    await db_session_instance.refresh(customer)
    return customer


async def test_create_order_via_api_rounds_total(client, db_session_instance, customer_factory):
    """POST /orders computes and rounds the total from its lines."""
    customer = await _seed_customer(db_session_instance, customer_factory)

    payload = {
        "customer_id": customer.id,
        "lines": [
            {"resource_id": 1, "quantity": 3, "unit_price": "3.335"},
        ],
    }

    response = await client.post("/orders", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == customer.id
    assert body["status"] == "pending"
    # 3 * 3.335 = 10.005 -> half-up rounds to 10.01
    assert Decimal(body["total_amount"]) == Decimal("10.01")
    assert len(body["lines"]) == 1


async def test_create_order_for_missing_customer_returns_404(client):
    """POST /orders for a nonexistent customer returns the 404 envelope."""
    payload = {
        "customer_id": 999,
        "lines": [{"resource_id": 1, "quantity": 1, "unit_price": "1.00"}],
    }

    response = await client.post("/orders", json=payload)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_create_order_requires_at_least_one_line(
    client, db_session_instance, customer_factory
):
    """POST /orders with zero lines is rejected by request validation."""
    customer = await _seed_customer(db_session_instance, customer_factory)

    response = await client.post("/orders", json={"customer_id": customer.id, "lines": []})

    assert response.status_code == 422


async def test_list_orders_for_customer(client, db_session_instance, customer_factory):
    """GET /orders?customer_id= lists only that customer's orders."""
    customer = await _seed_customer(db_session_instance, customer_factory)

    for price in ("5.00", "7.50"):
        await client.post(
            "/orders",
            json={
                "customer_id": customer.id,
                "lines": [{"resource_id": 1, "quantity": 1, "unit_price": price}],
            },
        )

    response = await client.get("/orders", params={"customer_id": customer.id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {Decimal(o["total_amount"]) for o in body} == {Decimal("5.00"), Decimal("7.50")}


async def test_cancel_order_sets_status(client, db_session_instance, customer_factory):
    """DELETE /orders/{id} cancels the order and returns it."""
    customer = await _seed_customer(db_session_instance, customer_factory)
    create_response = await client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "lines": [{"resource_id": 1, "quantity": 1, "unit_price": "9.99"}],
        },
    )
    order_id = create_response.json()["id"]

    response = await client.delete(f"/orders/{order_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_cancel_missing_order_returns_404(client):
    """DELETE /orders/{id} for a missing id returns the 404 envelope."""
    response = await client.delete("/orders/999")

    assert response.status_code == 404


async def test_service_cancel_is_idempotent(db_session_instance, customer_factory):
    """Cancelling an already-cancelled order does not raise."""
    customer = await _seed_customer(db_session_instance, customer_factory)
    service = OrderService(
        SqlAlchemyOrderRepository(db_session_instance),
        SqlAlchemyCustomerRepository(db_session_instance),
    )
    order = await service.create(
        customer.id, [OrderLineInput(resource_id=1, quantity=1, unit_price=Decimal("1.00"))]
    )

    once = await service.cancel(order.id)
    twice = await service.cancel(order.id)

    assert once.status == "cancelled"
    assert twice.status == "cancelled"


async def test_service_list_for_customer_raises_not_found_for_missing_customer(
    db_session_instance,
):
    """list_for_customer raises NotFound rather than returning an empty list
    for a customer that does not exist."""
    service = OrderService(
        SqlAlchemyOrderRepository(db_session_instance),
        SqlAlchemyCustomerRepository(db_session_instance),
    )

    with pytest.raises(NotFound):
        await service.list_for_customer(999)
