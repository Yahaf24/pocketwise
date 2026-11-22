"""Tests for display formatting: ₪ / $ symbol choice (D9). Display only — no conversion."""
import pytest

from pocketwise_engine import CURRENCIES, format_money, parse_amount


@pytest.mark.parametrize("agorot,currency,expected", [
    (123450, "ILS", "₪1,234.50"),
    (123450, "USD", "$1,234.50"),
    (0, "ILS", "₪0.00"),
    (5, "ILS", "₪0.05"),
    (80000, "USD", "$800.00"),
    (1_000_000_000, "ILS", "₪10,000,000.00"),
    (-20000, "ILS", "-₪200.00"),
    (-5, "USD", "-$0.05"),
])
def test_format_money(agorot, currency, expected):
    assert format_money(agorot, currency) == expected


def test_default_currency_is_shekel():
    assert format_money(80000) == "₪800.00"


def test_supported_currencies():
    assert CURRENCIES == {"ILS": "₪", "USD": "$"}


def test_unknown_currency_rejected():
    with pytest.raises(ValueError):
        format_money(100, "EUR")


@pytest.mark.parametrize("bad", [12.5, True, "100", None])
def test_only_integer_agorot_accepted(bad):
    with pytest.raises(TypeError):
        format_money(bad)


def test_symbol_does_not_change_amount():
    # Switching the symbol never converts: the same number is stored either way.
    assert parse_amount("$1,800", "amount") == parse_amount("₪1,800", "amount") == 180000
    assert parse_amount(" $ 50.25 ", "amount") == 5025
