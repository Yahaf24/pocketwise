"""Deterministic financial calculations (docs/DECISIONS.md). All money values are integer agorot."""
import hashlib
import json
from datetime import date

from .months import add_months, planning_months
from .validation import Expense, Goal, ValidationError

FEASIBLE = "feasible"
NOT_FEASIBLE = "not_feasible"
ALREADY_ACHIEVED = "already_achieved"
NEEDS_UPDATED_INFO = "needs_updated_info"


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def monthly_summary(income: int, expenses: list[Expense]) -> dict:
    essential = sum(e.amount for e in expenses if e.kind == "essential")
    flexible = sum(e.amount for e in expenses if e.kind == "flexible")
    total = essential + flexible
    return {"income": income, "essential": essential, "flexible": flexible,
            "total_expenses": total, "balance": income - total}


def assess(income: int, expenses: list[Expense], goal: Goal, today: date) -> dict:
    """Feasibility assessment plus alternatives A/B/C (alternatives only when not feasible)."""
    s = monthly_summary(income, expenses)
    balance = s["balance"]
    remaining = max(goal.target - goal.saved, 0)
    months = planning_months(today, goal.deadline)

    result = {**s, "target": goal.target, "saved": goal.saved, "remaining": remaining,
              "months": months, "required_monthly": None, "monthly_remainder": None,
              "status": None, "alt_a": None, "alt_b": None, "alt_c": None}

    if remaining == 0:
        result.update(status=ALREADY_ACHIEVED, required_monthly=0, monthly_remainder=balance)
        return result
    if months < 1:
        result["status"] = NEEDS_UPDATED_INFO
        return result

    required = ceil_div(remaining, months)
    result["required_monthly"] = required
    result["monthly_remainder"] = balance - required
    if balance * months >= remaining:
        result["status"] = FEASIBLE
        return result

    result["status"] = NOT_FEASIBLE
    result["alt_a"] = _alt_extend_deadline(balance, remaining, today)
    result["alt_b"] = _alt_adjust_goal(balance, goal.saved, months)
    result["alt_c"] = _alt_flexible(balance, required, s["flexible"])
    return result


def _alt_extend_deadline(balance: int, remaining: int, today: date) -> dict:
    if balance <= 0:
        return {"available": False, "reason": "no_monthly_surplus"}
    months = ceil_div(remaining, balance)
    required = ceil_div(remaining, months)
    return {"available": True, "months": months, "deadline": add_months(today, months).isoformat(),
            "required_monthly": required, "monthly_remainder": balance - required}


def _alt_adjust_goal(balance: int, saved: int, months: int) -> dict:
    if balance <= 0:
        return {"available": False, "reason": "no_monthly_surplus"}
    return {"available": True, "target": saved + balance * months,
            "required_monthly": balance, "monthly_remainder": 0}


def _alt_flexible(balance: int, required: int, flexible_total: int) -> dict:
    needed = required - balance
    if needed > flexible_total:
        return {"available": False, "reason": "not_enough_flexible_spending",
                "reduction_needed": needed, "flexible_total": flexible_total}
    return {"available": True, "reduction_needed": needed, "flexible_total": flexible_total,
            "monthly_remainder": 0}


def apply_flexible_reductions(expenses: list[Expense], reductions: dict[str, int]) -> list[Expense]:
    """Return a NEW expense list with the user's chosen reductions. Only flexible expenses may be reduced."""
    by_name = {e.name: e for e in expenses}
    for name, cut in reductions.items():
        if name not in by_name:
            raise ValidationError(name, "Unknown expense.")
        if by_name[name].kind != "flexible":
            raise ValidationError(name, "Essential expenses are never changed by a plan.")
        if not isinstance(cut, int) or cut < 0 or cut > by_name[name].amount:
            raise ValidationError(name, "The reduction must be between ₪0 and the current amount.")
    return [Expense(e.name, e.amount - reductions.get(e.name, 0), e.kind) for e in expenses]


def fingerprint(income: int, expenses: list[Expense], goal: Goal) -> str:
    """Stable hash of the financial assumptions, used to remember rejected suggestions."""
    data = {"income": income,
            "expenses": sorted([e.name, e.amount, e.kind] for e in expenses),
            "goal": [goal.target, goal.saved, goal.deadline.isoformat()]}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def should_show_suggestion(kind: str, current_fingerprint: str, rejections: list[dict],
                           compare_again: bool = False) -> bool:
    if compare_again:
        return True
    return not any(r["type"] == kind and r["fingerprint"] == current_fingerprint for r in rejections)


def plan_needs_review(confirmed_plan: dict, assessment: dict) -> bool:
    """True if the confirmed monthly contribution no longer fits the balance. Never modifies the plan."""
    return assessment["balance"] < confirmed_plan["monthly_contribution"]


def add_contribution(contributions: list[dict], contribution: dict) -> list[dict]:
    """Append a contribution unless one with the same id exists (double-click protection)."""
    amount = contribution.get("amount")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise ValidationError("amount", "The contribution must be more than ₪0.")
    if not contribution.get("id"):
        raise ValidationError("id", "Missing contribution id.")
    if any(c["id"] == contribution["id"] for c in contributions):
        return list(contributions)
    return [*contributions, dict(contribution)]
