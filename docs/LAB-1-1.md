# Lab 1.1 — `summarise_orders` contract

Implement `summarise_orders(orders: list[Order]) -> dict` in
`src/reporting/summary.py`. It currently raises `NotImplementedError`.

## Required return keys

| Key | Type | Meaning |
|---|---|---|
| `total_revenue` | `Decimal` | Sum of `total_amount` across the given orders. |
| `order_count` | `int` | Number of orders given. |
| `average_order` | `Decimal` | `total_revenue` divided by `order_count`. |
| `top_customer_id` | `int` | `customer_id` of the customer with the highest total spend among the given orders. |

Return exactly a `dict` with these four keys — no more, no fewer.

`Order` is defined in `src/db/models.py`. Each order has `customer_id` and
`total_amount` (already a `Decimal`), among other fields.
