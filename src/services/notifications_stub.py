"""Placeholder for outbound waitlist notifications.

Explicitly OUT OF SCOPE for this lab -- see the "Out of scope" section of
docs/LAB-4-1-SPEC.md. Waitlist promotion (moving an entry from waiting to
booked when a reservation is cancelled) must NOT call into this module.
Actually sending a customer a notification about their promotion is
separate, later work with its own spec.

This file exists on the branch because real repositories accumulate
exactly this kind of half-finished, plausible-looking, adjacent module,
and a feature implementation has to recognise it is not part of the task
rather than wire it in because it happens to be sitting right there.
"""

from src.db.models import Reservation


def notify_waitlist_promotion(reservation: Reservation) -> None:
    """Pretend to notify a customer that their waitlist entry was promoted.

    Deliberately unimplemented. Out of scope for this lab -- do not call
    this from the waitlist promotion path.

    Args:
        reservation: The reservation the waitlist entry was promoted
            into.

    Raises:
        NotImplementedError: Always. This is out of scope, not a bug to
            fix.
    """
    raise NotImplementedError("notifications are out of scope for this lab")
