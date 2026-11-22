# PocketWise — Calculation Rules & Decisions

Status legend: **Proposed** = implemented as the default, team has not yet confirmed. **Agreed** = team confirmed.
All rules below are implemented in `backend/pocketwise_engine/` and covered by `tests/`.

## Variables
| Symbol | Meaning |
|---|---|
| I | Estimated average monthly income |
| E | Total estimated monthly expenses (essential + flexible) |
| B | Available monthly balance = I − E (may be negative) |
| T | Target amount |
| S | Already saved = amount entered at goal creation + recorded contributions |
| G | Remaining requirement = max(T − S, 0) |
| M | Planning months (see D1) |
| R | Required monthly saving = G / M, rounded **up** to the agora |

## D1 — Month counting (Proposed)
M = number of **whole** calendar months from today until the deadline. Partial months are not counted.
Implementation: the largest n such that "today + n months" ≤ deadline, where adding months clamps to the end of the month (31 Jan + 1 month = 28/29 Feb).

| Today | Deadline | M |
|---|---|---|
| 8 Nov 2026 | 8 May 2027 | 6 |
| 8 Nov 2026 | 20 May 2027 | 6 |
| 8 Nov 2026 | 7 May 2027 | 5 |
| 31 Jan 2027 | 28 Feb 2027 | 1 |

If M < 1 (deadline less than a month away, or passed) → status **Needs Updated Information**.
At goal creation, a deadline that is today or in the past is rejected as invalid input.

## D2 — Money and rounding (Proposed)
- All amounts stored as integer agorot. Inputs accept at most 2 decimal places; negative, non-numeric, NaN/∞ and amounts above ₪10,000,000 are rejected.
- R is rounded **up** to the agora (you cannot save a fraction of an agora; rounding down would leave the goal short).
- Feasibility is decided exactly: **feasible ⇔ B × M ≥ G** (no rounding involved). This is equivalent to B ≥ R.
- Display formatting (₪ sign, thousands separators, whether to hide ".00") is a frontend concern and never feeds back into calculations.

## D3 — Statuses (Proposed)
Checked in this order:
1. **Already Achieved** — G = 0.
2. **Needs Updated Information** — M < 1.
3. **Feasible** — B × M ≥ G.
4. **Not Feasible** — otherwise (includes B ≤ 0).

## D4 — Alternatives (Proposed)
Shown only when status is Not Feasible. Order and letters match the spec and tests.

- **A — Extend deadline.** Shortest whole-month plan: M′ = ⌈G / B⌉, new deadline = today + M′ months. Example: ₪6,000 at ₪800/month → 7.5 → **8 months, ₪750/month, ₪50 left**. Not available if B ≤ 0.
- **B — Adjust goal amount.** Largest target reachable by the current deadline: T′ = S + B × M. Example: 0 + 800 × 6 = **₪4,800**. Not available if B ≤ 0.
- **C — Adjust flexible expenses.** Needed reduction = R − B (the monthly shortfall). Available only if total flexible expenses ≥ that amount; the user chooses which flexible categories to reduce. Essential expenses are never part of this alternative. Example: needs **₪200/month** out of ₪350 flexible.
- If none is available (e.g. B ≤ 0 and not enough flexible spending), the app shows a clear, nonjudgmental summary of the gap instead of suggestions.

## D5 — Rejected suggestions (Proposed)
A rejection is stored with an **assumptions fingerprint** (hash of income, expenses with classifications, target, saved amount, deadline). The suggestion is hidden while the fingerprint is unchanged, and shown again when it changes or when the user presses "Compare Again".

## D6 — Reassessment (Proposed)
When inputs change, the assessment is recalculated. A confirmed plan is **never** replaced automatically; the app only flags "your plan needs review" if the plan no longer fits.

## D7 — Contributions (Proposed)
Each contribution has a unique ID generated when the form opens. Adding the same ID twice is a no-op (duplicate-click protection, T09). Contributions increase S, so G and R decrease.

## D8 — Where calculations run (Proposed, needs team decision)
The Python engine is the reference implementation. Recommendation: mirror it in a small JS module in the browser, both checked against `tests/vectors.json`, so the app still works if Flask is unavailable (T12) and Flask is needed only for optional AI explanations.
Alternative: calculations only in Flask; the app shows a "service unavailable" message when Flask is down.

## D9 — Currency symbol (Proposed, needs team confirmation)
The user may choose how amounts are **shown**: ₪ (ILS, default) or $ (USD). This is a display label only:
- No conversion and no exchange rates. Stored amounts, calculations and test vectors are unchanged (still integer minor units; "agorot" in the code).
- `format_money(agorot, currency)` in `display.py` gives e.g. `₪1,234.50` / `$1,234.50`, negative as `-₪200.00`. Always 2 decimals.
- `parse_amount` ignores a ₪ or $ typed in the input.
- Changing the symbol does not change the assumptions fingerprint (D5) and does not trigger reassessment (D6).
Note: this narrows CLAUDE.md rule 8 ("currency switching" out of scope) to "currency conversion" out of scope; the spec in the claude.ai Project still needs the same update.

## D10 — Green light when the goal is reached (Proposed, needs team confirmation)
When the status is **Already Achieved** (G = 0, meaning S ≥ T), the UI shows a green light.
- `goal_light(status)` in `display.py` returns `"green"` for Already Achieved and `"off"` for every other status. An unknown status raises `ValueError`.
- It is display only. It reads the status from `assess()` and never changes amounts, the fingerprint (D5) or a confirmed plan (D6).
- There is no red state. A goal that hasn't been reached yet is not shown as a failure (CLAUDE.md rule 9).

## Open
- D8 needs a team decision.
- D9 needs team confirmation.
- D10 needs team confirmation.
- Whether feasibility screen allows editing goal parameters inline (Stitch design does) or only via Edit Goal (spec).
