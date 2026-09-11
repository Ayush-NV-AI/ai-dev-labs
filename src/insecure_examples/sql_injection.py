"""Training material — deliberately insecure.

Seeded example for the sql-injection-string-building rule. Looks like a
plausible "search reservations by note" helper an assistant might
generate when asked to add a quick filter, rather than an obvious CTF
exercise.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def search_reservations_by_note(session: AsyncSession, note_contains: str):
    """Look up reservations whose note contains the given text.

    Deliberately vulnerable: ``note_contains`` is interpolated directly
    into the query text rather than bound as a parameter.
    """
    query = text(f"SELECT * FROM reservations WHERE note LIKE '%{note_contains}%'")
    result = await session.execute(query)
    return result.all()


async def find_customer_by_email_raw(session: AsyncSession, email: str):
    """Look up a customer row by email using a hand-built query string."""
    result = await session.execute(
        text("SELECT * FROM customers WHERE email = '{}'".format(email))
    )
    return result.all()
