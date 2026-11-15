# Stitch export review — 8 Nov 2026

Exported screens: Welcome, Financial Setup, Dashboard, Savings Feasibility (folder `screen_4` = spec Screen 5), plus `DESIGN.md`.
Missing: Create Savings Goal, Alternative Plans (currently inside Feasibility), Plan Confirmation, Savings Progress, Reassessment, Settings & Privacy, and the Feasible / Already Achieved / Needs Updated Information states.

## Must fix
| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | Feasibility, Alt A | "Extend to 7.5 months" — fractional month | 8 months, ₪750/month, ₪50 left (D1/D4, T03) |
| 2 | Feasibility, alternatives | "Apply…" / "Set Target…" apply immediately | Select This Plan → Plan Confirmation; add Reject Suggestion, Why This Option?, advantages, trade-offs, remaining balance |
| 3 | Welcome | Testimonial "Noam R., CS Student, Tel Aviv" is invented | Remove |
| 4 | Dashboard | "Create Savings Goal" shown while a goal exists; no Add Contribution | Swap for Add Contribution when a goal exists |
| 5 | Dashboard | No Available Monthly Balance card (₪800) | Add as a main card |
| 6 | Setup, Dashboard, header, DESIGN.md | Out of scope: Manage Split, currency settings/ILS chip, profile photo, "Hi, Alex", Peer Split Bar, quick transfers, multi-account | Remove (also from DESIGN.md so Stitch stops generating them) |

## Should fix
- One example goal everywhere (three different names now; Welcome uses MacBook Air ₪4,800).
- Alternative order A = deadline, B = goal amount, C = flexible (screen has B and C swapped).
- "Needs Feasibility" is not a status → "Not Feasible". Remove "84% / 100% Feasible".
- Flexible badges green → amber (DESIGN.md says amber; green = positive).
- DESIGN.md YAML `primary: #000000` → `#0F172A` (buttons render black).
- Budget Allocation mixes % of expenses (89%) with "80% of Income".
- Setup says "saved automatically · LIVE" but has Save & Continue; pick explicit save. Add Cancel.
- Invented content: "October 2024", "Stable Regular", "+₪1,450 Safe", "₪150/week" tip.
- Labels: Income / Inflow / Stipend & Income; Essential / Fix → pick one each.
- "100% Free & Client-Side" → "Your data stays in this browser" (unless D8 = all calculations in browser).

## Minor
- Broken logo image on every screen.
- Dashboard Expenses card cut off on mobile.
- Bottom nav has Welcome but no Goal/Progress or Settings.
- Code depends on Tailwind CDN, Google Fonts and Google-hosted images — replace during frontend build.
