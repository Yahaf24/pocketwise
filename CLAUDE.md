# PocketWise — Project Memory for Claude Code

PocketWise is a student budgeting and savings-goal planning web app (HUJI course 55312, team: Rahaf, Dania, Nahla).
It answers three questions: How much do I have each month? Can I reach my savings goal by my deadline? If not, what are realistic alternatives?

The full specification lives in the claude.ai Project "data science" (project description). This file is the short, always-loaded version.
Calculation rules and settled decisions: `docs/DECISIONS.md` — read it before touching anything in `backend/pocketwise_engine/`.

## Stack (V1)
- Frontend: plain HTML + CSS + JavaScript (no framework), responsive, accessible forms. *(not built yet)*
- Backend: Python 3.11+, Flask. *(not built yet)*
- Calculation engine: `backend/pocketwise_engine/` — pure Python, no Flask, no I/O. **Built and tested.**
- Storage: browser LocalStorage only (guest mode). No database, no accounts, no Supabase in V1.

## Commands
```bash
pip install -r requirements.txt
python -m pytest -q          # run all tests (must pass before any commit)
```

## Layout
```
backend/pocketwise_engine/   calculation engine (money, months, validation, engine)
tests/                       pytest tests; tests/vectors.json = shared test cases (also for future JS mirror)
docs/DECISIONS.md            calculation rules + open decisions
design/                      Stitch export review and design notes
.claude/                     Claude Code agents, skills, hooks for this repo
```

## Non-negotiable rules
1. Financial calculations are deterministic Python/JS. NEVER use an LLM to compute or invent amounts.
2. Money is stored as integer agorot (₪1 = 100). Never use floats for money. Convert at the edges only.
3. Never change an essential expense automatically. Alternative C may only touch flexible expenses, and only after the user confirms.
4. Never apply a recommendation or overwrite a confirmed plan without explicit user confirmation.
5. A rejected suggestion is not shown again unless the financial assumptions change (fingerprint) or the user asks to compare again.
6. One active savings goal only (V1).
7. One month-counting rule everywhere: `planning_months()` in `months.py`. Never count months another way on any screen.
8. Out of V1 scope — do not build: login/sign-up, bank integration, multiple goals, cloud sync, push/email notifications, payments, investment advice, cost splitting with roommates, currency switching.
9. Tone in all UI text: supportive, nonjudgmental, no financial shaming.
10. Do not invent user research, testimonials, metrics, or claim a feature works unless it is implemented and tested.

## How to work in this repo (Karpathy rules)
- **Think before coding:** state assumptions; if a requirement is ambiguous, list options and ask.
- **Keep it simple:** minimum code for the request. No speculative features or abstractions.
- **Surgical changes:** touch only the files the task needs.
- **Test first:** for engine changes, add/extend a case in `tests/vectors.json` or `tests/test_engine.py` first, watch it fail, then implement.
- Use `/plan` before any change spanning more than one module.

## Status
- Phase 1 research: done. Phase 2 Stitch design: 4 of 10 screens exported, review in `design/stitch-review.md`.
- Phase 4 engine: implemented with tests (T01–T06, T08, T09 at engine level). Phases 3, 5–8: not started.
