"""Input validation: turns raw user/JSON input into safe values (money in integer agorot)."""
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation

MAX_AMOUNT_AGOROT = 10_000_000 * 100  # ₪10,000,000
MAX_NAME_LENGTH = 60
KINDS = ("essential", "flexible")


class ValidationError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


@dataclass(frozen=True)
class Expense:
    name: str
    amount: int  # agorot
    kind: str    # "essential" | "flexible"


@dataclass(frozen=True)
class Goal:
    name: str
    target: int  # agorot
    saved: int   # agorot (initial amount + contributions)
    deadline: date

    def with_saved(self, saved: int) -> "Goal":
        return replace(self, saved=saved)


def parse_amount(value, field: str, allow_negative: bool = False) -> int:
    """Shekel amount (number or string, max 2 decimals) -> integer agorot."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValidationError(field, "Please enter an amount.")
    text = str(value).strip().replace(",", "").replace("₪", "")
    if text == "":
        raise ValidationError(field, "Please enter an amount.")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValidationError(field, "Please enter a number, for example 1200.")
    if not amount.is_finite():
        raise ValidationError(field, "Please enter a number, for example 1200.")
    if amount.as_tuple().exponent < -2 and amount != amount.quantize(Decimal("0.01")):
        raise ValidationError(field, "Use at most 2 decimal places.")
    if amount < 0 and not allow_negative:
        raise ValidationError(field, "The amount can't be negative.")
    agorot = int(amount * 100)
    if abs(agorot) > MAX_AMOUNT_AGOROT:
        raise ValidationError(field, "That amount is too large.")
    return agorot


def parse_name(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field, "Please enter a name.")
    name = value.strip()
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(field, f"Keep the name under {MAX_NAME_LENGTH} characters.")
    return name


def parse_expense(raw: dict) -> Expense:
    kind = raw.get("kind")
    if kind not in KINDS:
        raise ValidationError("kind", "Choose Essential or Flexible.")
    return Expense(parse_name(raw.get("name"), "name"), parse_amount(raw.get("amount"), "amount"), kind)


def parse_date(value, field: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError(field, "Please choose a valid date.")


def parse_goal(raw: dict, today: date, creating: bool = True) -> Goal:
    name = parse_name(raw.get("name"), "name")
    target = parse_amount(raw.get("target"), "target")
    if target == 0:
        raise ValidationError("target", "The target must be more than ₪0.")
    saved = parse_amount(raw.get("saved", 0), "saved")
    deadline = parse_date(raw.get("deadline"), "deadline")
    if creating and deadline <= today:
        raise ValidationError("deadline", "Choose a date in the future.")
    return Goal(name, target, saved, deadline)
