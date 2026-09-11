# ai-dev-labs

Lab monorepo for the T-Systems / Skillverse course **"Efficient Software
Development with AI Tools."** `main` is the shared base every lab branch
is cut from: a small, clean, boringly conventional resource-booking
service. Participants will judge their AI assistants against the
conventions they find here, so read `src/api/routes/resources.py` first —
it is the reference pattern every later route follows.

**Domain**, kept constant across branches so nobody context-switches:
resources, reservations, orders, pricing for a resource-booking service.

## Stack

Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), SQLite via
`aiosqlite` by default (zero external dependencies to get started),
pytest, ruff.

## Install

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements-dev.txt
```

## Run the service

```bash
uvicorn src.api.app:create_app --factory --reload
```

Then check `http://127.0.0.1:8000/health`.

## Run the tests

```bash
pytest -q
```

## Lint

```bash
ruff check .
```

## Verify your environment

Before installing anything, you can sanity-check your machine with the
standard library only:

```bash
python scripts/verify_setup.py
```

## Branch table

| Branch | Serves lab | Status |
|---|---|---|
| `main` | shared base | built |
| `lab-1-1-compare` | Lab 1.1 — comparing AI assistants on a mid-sized codebase | built |
| `lab-1-2-scaffold` | Lab 1.2 — generating an endpoint from natural language | built |
| `lab-2-1-legacy` | Lab 2.1 — characterizing legacy code before refactoring | built |
| `lab-2-2-bug` | Lab 2.2 — root-causing a non-local bug with a red herring | built |
| `lab-3-1-design` | Lab 3.1 — designing a notification capability from a brief | built |
| `lab-3-2-undocumented` | Lab 3.2 — documenting a working, undocumented service | built |
| `lab-3-2-review-me` | Lab 3.2 — reviewing a PR (act/judge/ignore triage) | built |
| `lab-4-1-agent` | Lab 4.1 — supervising an agent on a multi-file feature | built |
| `lab-4-2-sast` | Lab 4.2 — static analysis security gate | built |
| `lab-5-2-capstone` | Capstone — design, build, test, document, scan | built |

See `SCOPE_NOTES.md` at the repo root for what was deliberately left out
of this build and why.

## Keep your branches

Thursday's lab scans **every branch created during the week**, including
the ones you create yourself while working through the labs. That scan
only sees what has been pushed. **Push every branch you create at the end
of each day** — `git push -u origin <your-branch-name>` — even if you
think you'll come back to it tomorrow. A branch that only exists on your
laptop does not exist for Thursday's purposes.
