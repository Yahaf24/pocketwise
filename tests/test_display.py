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


# --- Green light when the goal is reached (D10) ---------------------------------

from datetime import date

from pocketwise_engine import (
    ALREADY_ACHIEVED, FEASIBLE, NEEDS_UPDATED_INFO, NOT_FEASIBLE,
    Expense, Goal, assess, goal_light,
)


def test_goal_light_celebrates_when_achieved():
    assert goal_light(ALREADY_ACHIEVED) == "celebrate"


def test_goal_light_on_track_when_feasible():
    assert goal_light(FEASIBLE) == "on_track"


@pytest.mark.parametrize("status", [NOT_FEASIBLE, NEEDS_UPDATED_INFO])
def test_goal_light_off_for_other_statuses(status):
    # Not reached yet is never shown as red: no financial shaming (CLAUDE.md rule 9).
    assert goal_light(status) == "off"


def test_goal_light_unknown_status_rejected():
    with pytest.raises(ValueError):
        goal_light("almost_there")


def _goal(saved):
    return Goal(name="laptop", target=600000, saved=saved, deadline=date(2027, 5, 8))


def test_goal_light_follows_assessment():
    # ₪800/month available, goal ₪6,000 by 8 May 2027 (M = 6), as in DECISIONS.md.
    expenses = [Expense(name="rent", amount=0, kind="essential")]
    today = date(2026, 11, 8)
    light = lambda saved: goal_light(assess(80000, expenses, _goal(saved), today)["status"])
    assert light(0) == "off"              # needs ₪1,000/month, has ₪800: not feasible
    assert light(120000) == "on_track"    # ₪4,800 left over 6 months = ₪800/month: exactly enough
    assert light(599999) == "on_track"    # one agora short of the target
    assert light(600000) == "celebrate"   # S = T
    assert light(650000) == "celebrate"   # S > T
