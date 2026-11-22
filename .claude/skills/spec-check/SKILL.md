---
name: spec-check
description: Check a PocketWise screen, Stitch export, UI text or code change against the V1 spec and calculation rules. Use when reviewing a design, a pull request, or before marking a phase complete.
---

# PocketWise spec check

Review the given screen, file or diff against the rules below. Read `CLAUDE.md` and `docs/DECISIONS.md` first.

## Checklist
1. **Scope** — nothing outside V1: no login/sign-up, bank links, multiple goals, cloud sync, notifications, payments, investment advice, roommate cost splitting, currency conversion or exchange rates (a ₪/$ display symbol is allowed, D9), profile photos or user names.
2. **Numbers** — every amount shown comes from the engine and matches `docs/DECISIONS.md` for the example data (₪4,000 income, ₪3,200 expenses = ₪2,850 essential + ₪350 flexible, ₪6,000 goal, 6 months → ₪1,000 needed, ₪200 short; A = 8 months/₪750/₪50 left, B = ₪4,800, C = cut ₪200 of flexible). No fractional months ("7.5 months" is wrong). No invented numbers, percentages or "% feasible".
3. **User control** — no alternative is applied without Select → Plan Confirmation → Confirm. Every alternative has Select This Plan, Edit Scenario, Reject Suggestion and Why This Option?. Essential expenses are never changed.
4. **Statuses** — only Feasible, Not Feasible, Already Achieved, Needs Updated Information.
5. **One goal** — when a goal exists, "Create Savings Goal" is replaced by goal actions (Add Contribution, View Plan).
6. **Honesty** — no fake testimonials, invented research or claims that aren't true (e.g. "100% client-side" while calculations run on Flask).
7. **Consistency** — same goal name, same labels (Income / Expenses / Available Balance / Essential / Flexible), Essential = navy badge, Flexible = amber badge, positive = emerald, primary = navy `#0F172A` (not black).
8. **Tone** — supportive and nonjudgmental; no shaming, no pressure.
9. **Buttons** — every visible button has a defined action from the spec.
10. **Accessibility** — labels on inputs, readable contrast, touch targets ≥ 44px, nothing cut off on mobile.

## Output
A table: `# | Severity (Must fix / Should fix / Minor) | Where | Problem | Fix`, sorted by severity, then one line on what is good. Do not edit files unless asked.
