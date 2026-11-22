"""Display formatting for money (D9). Display only: the symbol never converts or changes an amount."""

CURRENCIES = {"ILS": "₪", "USD": "$"}


def format_money(agorot: int, currency: str = "ILS") -> str:
    """Integer agorot -> e.g. "₪800", "₪1,234.50" or "$1,234.50" (".00" hidden). Never feeds back into calculations."""
    if isinstance(agorot, bool) or not isinstance(agorot, int):
        raise TypeError("format_money expects an integer amount in agorot.")
    if currency not in CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency!r}")
    sign = "-" if agorot < 0 else ""
    whole, cents = divmod(abs(agorot), 100)
    decimals = f".{cents:02d}" if cents else ""
    return f"{sign}{CURRENCIES[currency]}{whole:,}{decimals}"
