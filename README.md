# PocketWise

Student budgeting and savings-goal planner — HUJI Business Data & Technology (55312). Team: Rahaf, Dania, Nahla.

PocketWise answers three questions: How much do I have each month? Can I reach my savings goal by my deadline? If not, what are realistic alternatives?

## Get started
```bash
git clone https://github.com/Yahaf24/pocketwise.git
cd pocketwise
pip install -r requirements.txt
python -m pytest -q
```

## Branches
- `main` — stable; tests always pass. Only merged into from `dev`.
- `dev` — day-to-day work. Run `git pull` before you start, and make sure the tests pass before you push.

## Continue with Claude Code
```bash
cd pocketwise
claude
```
Claude reads `CLAUDE.md` automatically. Already set up for this repo:

| Workshop feature | Where | What it does |
|---|---|---|
| CLAUDE.md | `CLAUDE.md` | Project rules, scope, Karpathy rules |
| Hook (PostToolUse) | `.claude/settings.json`, `.claude/hooks/check_python.py` | After every edit: syntax check + run tests; failures go back to Claude |
| Sub-agent | `.claude/agents/test-writer.md` | Writes tests from the rules, never copies engine output |
| Skill | `.claude/skills/spec-check/SKILL.md` | `/spec-check` reviews a screen or change against the spec |

Mac/Linux: if `python` isn't found, change it to `python3` in `.claude/settings.json`.

## What exists
- `backend/pocketwise_engine/` — calculation engine (balance, months, feasibility, alternatives A/B/C, validation, rejections, contributions). Tested.
- `docs/DECISIONS.md` — calculation rules; items marked *Proposed* need team confirmation.
- `design/stitch-review.md` — review of the first 4 Stitch screens.

Not built yet: frontend, Flask API, LocalStorage, AI explanations.
