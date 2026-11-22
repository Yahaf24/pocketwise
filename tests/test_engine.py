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
    add_months,
    monthly_summary,
    parse_date,
    plan_needs_review,
    planning_months,
    should_show_suggestion,
    total_contributed,
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


# ---------- stage 2 hardening: month arithmetic ----------

@pytest.mark.parametrize("start,n,expected", [
    ("2027-01-31", 1, "2027-02-28"),
    ("2028-01-31", 1, "2028-02-29"),   # leap year
    ("2026-12-15", 1, "2027-01-15"),   # year rollover
    ("2026-11-08", 0, "2026-11-08"),
    ("2026-11-08", 14, "2028-01-08"),
    ("2026-08-31", 3, "2026-11-30"),
])
def test_add_months(start, n, expected):
    assert add_months(date.fromisoformat(start), n) == date.fromisoformat(expected)


def test_planning_months_leap_day_deadline():
    assert planning_months(date(2028, 1, 31), date(2028, 2, 29)) == 1
    assert planning_months(date(2028, 1, 31), date(2028, 2, 28)) == 0


# ---------- stage 2 hardening: summary and status order ----------

def test_monthly_summary_dana():
    income, expenses, _, _ = build(VECTORS["cases"][0])
    s = monthly_summary(income, expenses)
    assert s["essential"] == ag("2850")
    assert s["flexible"] == ag("350")
    assert s["total_expenses"] == ag("3200")
    assert s["balance"] == ag("800")


def custom(income, essential, flexible, target, deadline, saved="0", today=date(2026, 11, 8)):
    expenses = []
    if essential:
        expenses.append(parse_expense({"name": "Rent", "amount": essential, "kind": "essential"}))
    if flexible:
        expenses.append(parse_expense({"name": "Fun", "amount": flexible, "kind": "flexible"}))
    goal = parse_goal({"name": "G", "target": target, "saved": saved, "deadline": deadline}, today, creating=False)
    return assess(parse_amount(income, "income"), expenses, goal, today)


def test_already_achieved_wins_over_expired_deadline():
    result = custom("1000", "400", "300", "500", "2026-11-08", saved="500")
    assert result["status"] == "already_achieved"
    assert result["months"] == 0
    assert result["required_monthly"] == 0


def test_saved_above_target_is_already_achieved():
    result = custom("1000", "400", "300", "500", "2027-05-08", saved="900")
    assert result["status"] == "already_achieved"
    assert result["remaining"] == 0


def test_expired_deadline_needs_updated_info():
    result = custom("1000", "400", "300", "500", "2026-11-08")
    assert result["status"] == "needs_updated_info"
    assert result["required_monthly"] is None
    assert result["alt_a"] is None and result["alt_b"] is None and result["alt_c"] is None


# ---------- stage 2 hardening: alternative C boundaries ----------

def test_alt_c_available_when_flexible_exactly_covers_reduction():
    # balance 300, goal 600 in 1 month -> need 300 more; flexible is exactly 300
    result = custom("1000", "400", "300", "600", "2026-12-08")
    assert result["status"] == "not_feasible"
    assert result["alt_c"]["available"] is True
    assert result["alt_c"]["reduction_needed"] == ag("300")


def test_alt_c_unavailable_one_agora_over_flexible():
    # same, but goal is 601 -> need 301 and only 300 is flexible
    result = custom("1000", "400", "300", "600.01", "2026-12-08")
    assert result["status"] == "not_feasible"
    assert result["alt_c"]["available"] is False
    assert result["alt_c"]["reason"] == "not_enough_flexible_spending"


def test_negative_balance_blocks_a_and_b_but_not_c_when_flexible_is_large():
    # income 1000, expenses 1200 -> balance -200; reduction needed = 600 + 200 = 800 = flexible
    result = custom("1000", "400", "800", "600", "2026-12-08")
    assert result["balance"] == ag("-200")
    assert result["status"] == "not_feasible"
    assert result["alt_a"] == {"available": False, "reason": "no_monthly_surplus"}
    assert result["alt_b"] == {"available": False, "reason": "no_monthly_surplus"}
    assert result["alt_c"]["available"] is True


def test_alternatives_absent_when_feasible():
    result = custom("2000", "400", "300", "600", "2026-12-08")
    assert result["status"] == "feasible"
    assert result["alt_a"] is None and result["alt_b"] is None and result["alt_c"] is None


# ---------- stage 2 hardening: validation edges ----------

def test_amount_cap_boundary():
    assert parse_amount("10000000", "amount") == 10_000_000 * 100
    with pytest.raises(ValidationError):
        parse_amount("10000000.01", "amount")


def test_name_length_boundary_and_hebrew():
    ok = parse_expense({"name": "ת" * 60, "amount": "10", "kind": "flexible"})
    assert len(ok.name) == 60
    with pytest.raises(ValidationError):
        parse_expense({"name": "ת" * 61, "amount": "10", "kind": "flexible"})
    assert parse_expense({"name": "שכר דירה", "amount": "₪1,800", "kind": "essential"}).amount == ag("1800")


def test_parse_goal_existing_goal_may_have_past_deadline():
    goal = parse_goal({"name": "X", "target": "100", "saved": "0", "deadline": "2026-01-01"},
                      date(2026, 11, 8), creating=False)
    assert goal.deadline == date(2026, 1, 1)


def test_parse_date_accepts_date_and_rejects_garbage():
    assert parse_date(date(2027, 5, 8), "deadline") == date(2027, 5, 8)
    with pytest.raises(ValidationError):
        parse_date("2027-02-30", "deadline")


def test_goal_with_saved_keeps_other_fields():
    _, _, goal, _ = build(VECTORS["cases"][0])
    updated = goal.with_saved(ag("500"))
    assert updated.saved == ag("500")
    assert (updated.name, updated.target, updated.deadline) == (goal.name, goal.target, goal.deadline)
    assert goal.saved != updated.saved, "original goal must not change"


# ---------- stage 2: summing contributions (S = initial amount + contributions) ----------

def test_total_contributed():
    assert total_contributed([]) == 0
    contribs = add_contribution([], {"id": "a", "amount": ag("200"), "date": "2026-11-08"})
    contribs = add_contribution(contribs, {"id": "b", "amount": ag("50.50"), "date": "2026-11-09"})
    contribs = add_contribution(contribs, {"id": "a", "amount": ag("200"), "date": "2026-11-08"})  # duplicate
    assert total_contributed(contribs) == ag("250.50")


def test_saved_is_initial_plus_contributions():
    income, expenses, goal, today = build(VECTORS["cases"][0])
    contribs = add_contribution([], {"id": "a", "amount": ag("1200"), "date": "2026-11-08"})
    result = assess(income, expenses, goal.with_saved(goal.saved + total_contributed(contribs)), today)
    assert result["saved"] == goal.saved + ag("1200")
    assert result["status"] == "feasible"
