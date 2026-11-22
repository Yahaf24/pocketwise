"""Display formatting for money (D9). Display only: the symbol never converts or changes an amount."""

CURRENCIES = {"ILS": "₪", "USD": "$"}


def format_money(agorot: int, currency: str = "ILS") -> str:
    """Integer agorot -> e.g. "₪1,234.50" or "$1,234.50". Never feeds back into calculations."""
    if isinstance(agorot, bool) or not isinstance(agorot, int):
        raise TypeError("format_money expects an integer amount in agorot.")
    if currency not in CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency!r}")
    sign = "-" if agorot < 0 else ""
    whole, cents = divmod(abs(agorot), 100)
    return f"{sign}{CURRENCIES[currency]}{whole:,}.{cents:02d}"


def goal_light(status: str) -> str:
    """Goal indicator (D10), from an assess() status.

    "celebrate" = goal reached (green flash, message and celebration),
    "on_track"  = the plan reaches the goal by the deadline (steady green),
    "off"       = anything else.
    Display only. Never red: a goal not reached yet is not a failure (CLAUDE.md rule 9).
    """
    from .engine import ALREADY_ACHIEVED, FEASIBLE, NEEDS_UPDATED_INFO, NOT_FEASIBLE
    if status not in (ALREADY_ACHIEVED, FEASIBLE, NEEDS_UPDATED_INFO, NOT_FEASIBLE):
        raise ValueError(f"Unknown status: {status!r}")
    if status == ALREADY_ACHIEVED:
        return "celebrate"
    if status == FEASIBLE:
        return "on_track"
    return "off"
