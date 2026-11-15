"""PocketWise calculation engine — pure, deterministic, no I/O. See docs/DECISIONS.md."""
from .engine import (
    ALREADY_ACHIEVED, FEASIBLE, NEEDS_UPDATED_INFO, NOT_FEASIBLE,
    add_contribution, apply_flexible_reductions, assess, fingerprint,
    monthly_summary, plan_needs_review, should_show_suggestion,
)
from .months import add_months, planning_months
from .validation import Expense, Goal, ValidationError, parse_amount, parse_date, parse_expense, parse_goal
