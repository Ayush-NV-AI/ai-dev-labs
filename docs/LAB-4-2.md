# Lab 4.2 — Static Analysis Security Gate

## Commands

```bash
# Install semgrep (once, in your venv)
pip install semgrep

# The hand-tuned core ruleset for this repo
semgrep --config .semgrep.yml src/

# Layer the community registry packs on top for broader coverage
semgrep --config .semgrep.yml --config p/python --config p/security-audit src/

# Scan every lab branch you've built this week and get a combined summary
bash scripts/scan_all_branches.sh

# Cross-check requirements.txt against what src/ actually imports
python scripts/check_dependencies.py
```

`semgrep --config .semgrep.yml src/` must return **zero findings on
`main`** — that's the bar for a gate a security-conscious audience will
trust — and must catch every seeded example in `src/insecure_examples/`
on this branch (`lab-4-2-sast`).

## Triage table

For every finding from any of the commands above, fill in one row:

| Finding | Rule | Which lab produced it | Real / False Positive / Needs tuning | Action |
|---|---|---|---|---|
| | | | | |

- **Real**: a genuine issue. File it, or fix it now if it's small.
- **False positive**: the rule fired but there's no actual problem here
  — say why, specifically (not just "it's fine").
- **Needs tuning**: the rule is pointed at something real in spirit but
  is too broad/narrow as written — say what you'd change in
  `.semgrep.yml`.

`scripts/check_dependencies.py`'s "declared but not imported in src/"
flags are a good first real exercise in this: several will fire correctly
for dev-only tools (`pytest`, `ruff`) and CLI entry points (`uvicorn`)
that this repo never `import`s from inside `src/` — decide for yourself
whether that's a false positive or a checker that needs tuning to
understand "used via `tests/` or the command line" as a category of its
own, and write down your reasoning either way.

## Closing question

Which lab branch produced the most findings — and was it the one you
felt **least** confident about going in? Write a sentence on what that
tells you about where your blind spots are.
