"""Training material — deliberately insecure.

Seeded example for the missing-auth-check-on-mutating-route rule. A
self-contained toy router (not wired into the real app) so the example
doesn't depend on this package ever being imported.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: int) -> dict:
    """Delete a resource outright, with no check on who is calling."""
    return {"deleted": resource_id}


@router.post("/resources/{resource_id}/deactivate")
async def deactivate_resource(resource_id: int) -> dict:
    """Deactivate a resource, again with no caller check at all."""
    return {"deactivated": resource_id}
