# Scope notes for this build

This repo was built as a **scoped-down, Day 1 + Day 2 only** slice of the
full 9-branch course spec in `delivery-kit/04_Claude_Code_Repo_Build_Prompts.md`.
Branches built: `main`, `lab-1-1-compare`, `lab-1-2-scaffold`,
`lab-2-1-legacy`, `lab-2-2-bug`. Not built in this run: `lab-3-1-design`,
`lab-3-2-undocumented`, `lab-3-2-review-me`, `lab-4-1-agent`,
`lab-4-2-sast`, `lab-5-2-capstone`.

## Deliberate scope reductions (asked for up front)

- **No TypeScript mirror.** `lab-1-1-compare` does not have a `ts/`
  directory. The Python side is the full, real deliverable; the TS mirror
  described in Prompt 1 was explicitly dropped for this build.
- **`scripts/verify_setup.py` has no external-host reachability checks.**
  The full spec asks for HTTPS-reachability checks against
  `api.anthropic.com`, `api.githubcopilot.com`, `github.com`,
  `api2.cursor.sh`, `server.codeium.com`, `pypi.org`, plus a pip-index
  fetch. All of those need real calls to third-party services and were
  dropped. What remains and is real: Python >= 3.11 check, git-on-PATH
  check, git identity (user.name/user.email) check, inside-a-git-repo
  check, virtualenv-active check — each with a PASS/FAIL table and a
  MANUAL CHECK section, exactly as the spec's output shape requires.
- **`.semgrep.yml` is the empty-ruleset placeholder only.** The curated
  ruleset (SQL injection, `shell=True`, hardcoded secrets, permissive
  CORS, etc.) is Prompt 8 / Thursday work and out of scope here.

## Judgment calls made during the build

- **Python version.** Only Python 3.14.6 was available on this machine
  (no 3.11 install, no `py -3.11`). Per instructions, the build proceeded
  on 3.14.6 rather than blocking. Everything installs and runs cleanly on
  3.14; `pyproject.toml` still declares `target-version = "py311"` for
  ruff so lint rules match what participants running 3.11 will see.
  If a real 3.11 interpreter matters for delivery, re-run the verification
  pass on one before Monday.
- **`src/db/models.py` scope on `main`.** Prompt 0's file-layout comment
  lists `Resource, Reservation, Order, Customer` against `models.py`, but
  Prompt 1 says "add Order, OrderLine, Customer" and Prompt 2 says "add
  Reservation" — both phrased as new additions, with no "(already there)"
  note the way Prompt 2 uses for the error classes. Treating Prompt 0's
  comment as aspirational (the eventual full domain) rather than literal,
  `main` ships with only the `Resource` model, matching the fact that only
  `GET /resources` exists as a route on `main` and schemas.py only has
  `ResourceRead`. Reservation is added fresh in `lab-1-2-scaffold`; Order/
  OrderLine/Customer are added fresh in `lab-1-1-compare`. This keeps each
  branch's "add X" instruction literally true (X didn't already exist).
- **Real bug found and fixed on `main`: `get_session` never committed.**
  While building `lab-1-1-compare`'s order-creation route (the first
  *write* route in the repo — `main` only has GET routes), orders posted
  via the API silently vanished. Root cause: `src/db/session.py::get_session`
  opened a session and yielded it but never called `session.commit()`, so
  on request completion the session closed and implicitly rolled back.
  Fixed on `main` (commit `f468c3e`) so every branch cut from it inherits
  the fix: `get_session` now commits on a clean exit and rolls back if the
  route raised. `tests/conftest.py`'s test client override was updated to
  match. This is a genuine bug fix, not a scope reduction — flagging it
  because it changes behaviour the original Prompt 0 spec didn't call out
  as a requirement (no write route existed yet to expose it).
- **`lab-1-1-compare` "two assistants visibly disagree" check not run.**
  The prompt's acceptance note asks the trainer to personally run two
  different AI assistants against the `summarise_orders` stub and confirm
  they diverge on the empty-list case before Monday. That requires live
  access to multiple external assistants, which this build environment
  doesn't have. The stub, docs and skipped test are built exactly to the
  spec (edge cases undocumented, happy-path-only skipped test) so the
  exercise is set up correctly; the live two-assistant dry run is still
  outstanding and should be done by a human before the session.
