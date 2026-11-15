"""Tests for the PocketWise calculation engine.

Spec test IDs covered here: T01, T02, T03 (vectors), T04, T05, T06, T08, T09 (engine level).
T07, T10, T11, T12 need the frontend / Flask / AI layer and are not covered yet.
"""
import json
from datetime import date
from pathlib import Path

import pytest

from pocketwise_engine import (
    ValidationError,
    add_contribution,
    apply_flexible_reductions,
    assess,
    fingerprint,
    parse_amount,
    parse_expense,
    parse_goal,
    plan_needs_review,
    planning_months,
    should_show_suggestion,
)

VECTORS = json.loads((Path(__file__).parent / "vectors.json").read_text(encoding="utf-8"))


def ag(shekels: str) -> int:
    return parse_amount(shekels, "test", allow_negative=True)


def build(case):
    profile = VECTORS["profiles"][case["profile"]]
    today = date.fromisoformat(case["today"])
    income = parse_amount(profile["income"], "income")
    expenses = [parse_expense(e) for e in profile["expenses"]]
    goal = parse_goal(case["goal"], today, creating=False)
    return income, expenses, goal, today


# ---------- shared vectors (T01, T02, T03 + edge cases) ----------

MONEY_KEYS = {"balance", "essential", "flexible", "total_expenses", "remaining",
              "required_monthly", "monthly_remainder", "target", "reduction_needed", "flexible_total"}


def check(actual: dict, expected: dict, path: str):
    for key, want in expected.items():
        assert key in actual, f"{path}.{key} missing"
        got = actual[key]
        if isinstance(want, dict):
            check(got, want, f"{path}.{key}")
        elif key in MONEY_KEYS:
            assert got == ag(want), f"{path}.{key}: got {got} agorot, want ₪{want}"
        else:
            assert got == want, f"{path}.{key}: got {got!r}, want {want!r}"


@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda c: c["id"])
def test_vector(case):
    result = assess(*build(case))
    check(result, case["expect"], case["id"])


# ---------- months ----------

@pytest.mark.parametrize("today,deadline,months", [
    ("2026-11-08", "2027-05-08", 6),
    ("2026-11-08", "2027-05-20", 6),
    ("2026-11-08", "2027-05-07", 5),
    ("2027-01-31", "2027-02-28", 1),
    ("2026-11-08", "2026-11-08", 0),
    ("2026-11-08", "2026-10-01", 0),
])
def test_planning_months(today, deadline, months):
    assert planning_months(date.fromisoformat(today), date.fromisoformat(deadline)) == months


# ---------- T04: essential expenses are never changed ----------

def dana_expenses():
    return [parse_expense(e) for e in VECTORS["profiles"]["dana"]["expenses"]]


def test_t04_reducing_flexible_leaves_essentials_untouched():
    before = dana_expenses()
    after = apply_flexible_reductions(before, {"Campus Coffee & Dining": ag("150"), "Streaming & Subscriptions": ag("50")})
    for b, a in zip(before, after):
        if b.kind == "essential":
            assert a == b
    assert sum(e.amount for e in after) == ag("3000")
    assert before == dana_expenses(), "input list must not be mutated"


def test_t04_reducing_essential_is_refused():
    with pytest.raises(ValidationError):
        apply_flexible_reductions(dana_expenses(), {"Rent & Dorm Utilities": ag("200")})


def test_t04_cannot_reduce_below_zero_or_unknown():
    with pytest.raises(ValidationError):
        apply_flexible_reductions(dana_expenses(), {"Streaming & Subscriptions": ag("101")})
    with pytest.raises(ValidationError):
        apply_flexible_reductions(dana_expenses(), {"Gym": ag("10")})


def test_t04_alternative_c_never_counts_essentials():
    case = VECTORS["cases"][0]
    result = assess(*build(case))
    assert result["alt_c"]["flexible_total"] == ag("350")  # not 3,200


# ---------- T05: rejected suggestions ----------

def test_t05_rejected_suggestion_hidden_until_assumptions_change():
    income, expenses, goal, today = build(VECTORS["cases"][0])
    fp = fingerprint(income, expenses, goal)
    rejections = [{"type": "alt_a", "fingerprint": fp}]
    assert should_show_suggestion("alt_a", fp, rejections) is False
    assert should_show_suggestion("alt_b", fp, rejections) is True
    # user explicitly asks to compare again
    assert should_show_suggestion("alt_a", fp, rejections, compare_again=True) is True
    # meaningful change: income changes
    fp2 = fingerprint(income - ag("100"), expenses, goal)
    assert fp2 != fp
    assert should_show_suggestion("alt_a", fp2, rejections) is True


def test_fingerprint_ignores_expense_order():
    income, expenses, goal, _ = build(VECTORS["cases"][0])
    assert fingerprint(income, expenses, goal) == fingerprint(income, list(reversed(expenses)), goal)


# ---------- T06: recalculation does not replace a confirmed plan ----------

def test_t06_income_drop_recalculates_but_keeps_plan():
    income, expenses, goal, today = build(VECTORS["cases"][1])  # 8-month plan, feasible
    first = assess(income, expenses, goal, today)
    confirmed_plan = {"monthly_contribution": first["required_monthly"], "deadline": goal.deadline.isoformat()}
    plan_copy = dict(confirmed_plan)

    second = assess(ag("3200"), expenses, goal, today)  # income 4,000 -> 3,200
    assert second["balance"] == 0
    assert second["status"] == "not_feasible"
    assert plan_needs_review(confirmed_plan, second) is True
    assert confirmed_plan == plan_copy, "confirmed plan must not be modified"
    assert plan_needs_review(confirmed_plan, first) is False


# ---------- T08: invalid input ----------

@pytest.mark.parametrize("value", ["-5", "abc", "", None, "1.234", "nan", "inf", True, "10000000.01", [1]])
def test_t08_invalid_amounts_rejected(value):
    with pytest.raises(ValidationError):
        parse_amount(value, "amount")


@pytest.mark.parametrize("value,agorot", [("0", 0), ("4000", 400000), ("12.5", 1250), (99.99, 9999), (7, 700), ("1,200", 120000)])
def test_valid_amounts(value, agorot):
    assert parse_amount(value, "amount") == agorot


@pytest.mark.parametrize("goal", [
    {"name": "", "target": "100", "saved": "0", "deadline": "2027-05-08"},
    {"name": "X", "target": "0", "saved": "0", "deadline": "2027-05-08"},
    {"name": "X", "target": "100", "saved": "-1", "deadline": "2027-05-08"},
    {"name": "X", "target": "100", "saved": "0", "deadline": "2026-11-08"},  # today
    {"name": "X", "target": "100", "saved": "0", "deadline": "2026-01-01"},  # past
    {"name": "X", "target": "100", "saved": "0", "deadline": "2027-02-30"},  # not a date
    {"name": "X", "target": "100", "saved": "0", "deadline": "next year"},
])
def test_t08_invalid_goal_rejected(goal):
    with pytest.raises(ValidationError):
        parse_goal(goal, date(2026, 11, 8), creating=True)


@pytest.mark.parametrize("expense", [
    {"name": "", "amount": "10", "kind": "essential"},
    {"name": "Rent", "amount": "-10", "kind": "essential"},
    {"name": "Rent", "amount": "10", "kind": "optional"},
])
def test_t08_invalid_expense_rejected(expense):
    with pytest.raises(ValidationError):
        parse_expense(expense)


def test_validation_error_names_the_field():
    with pytest.raises(ValidationError) as err:
        parse_goal({"name": "X", "target": "abc", "saved": "0", "deadline": "2027-05-08"}, date(2026, 11, 8))
    assert err.value.field == "target"


# ---------- T09: duplicate contributions ----------

def test_t09_same_contribution_twice_is_recorded_once():
    contribs = []
    c = {"id": "c-123", "amount": ag("200"), "date": "2026-11-08"}
    contribs = add_contribution(contribs, c)
    contribs = add_contribution(contribs, dict(c))  # double click
    assert len(contribs) == 1


def test_contributions_reduce_requirement():
    income, expenses, goal, today = build(VECTORS["cases"][0])
    before = assess(income, expenses, goal, today)
    goal_after = goal.with_saved(goal.saved + ag("1200"))
    after = assess(income, expenses, goal_after, today)
    assert after["remaining"] == before["remaining"] - ag("1200")
    assert after["required_monthly"] == ag("800")
    assert after["status"] == "feasible"


def test_contribution_must_be_positive():
    with pytest.raises(ValidationError):
        add_contribution([], {"id": "c-1", "amount": 0, "date": "2026-11-08"})
