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
- **Real bug found and fixed: `get_session` never committed.** While
  building `lab-1-1-compare`'s order-creation route (the first *write*
  route in the repo — `main` itself only has GET routes, so this never
  surfaced here), data written through the FastAPI `get_session`
  dependency was silently rolled back: the session was opened and
  yielded but never committed, so closing it at the end of the request
  discarded the write. Fixed in `src/db/session.py::get_session`, which
  now commits on a clean exit and rolls back if the route raised;
  `tests/conftest.py`'s test-client session override matches. Fixed here
  on `main` so every lab branch cut from it inherits the fix.
- **`lab-2-2-bug` adds its own minimal `Reservation` model.** This branch
  is cut fresh from `main` (not from `lab-1-2-scaffold`), so it doesn't
  inherit that branch's reservations scaffold. `free_slots`/`next_available`/
  `is_free` need something to check against, so a small standalone
  `Reservation` model (same shape, no repository/CRUD) was added directly
  to this branch's `src/db/models.py`. This is expected duplication across
  independent lab branches, not an oversight.
- **`free_slots` design was chosen specifically so the planted bug has a
  real, deterministic, exactly-3-test effect.** `overlaps()`'s boundary
  bug only misfires at an *exact* touching instant. A naive "merge
  reservations, then subtract from the day" implementation is naturally
  self-correcting at exact boundaries (interval-clamping absorbs the
  off-by-one-instant error harmlessly), so it doesn't reproduce the bug
  at all. `free_slots` here instead sweeps the day's reservation-boundary
  instants and classifies each resulting segment via `is_free()` (which
  calls the buggy `overlaps()` directly) — this is what makes a
  reservation's immediately-following segment silently vanish. The 3
  failing tests target exactly that: the slot right after a single
  reservation, the gap between two reservations, and the final slot of
  the day. `is_free`/`next_available` have the same underlying bug at
  the identical boundary condition, but no test in this suite exercises
  that specific case for them (deliberately, to keep the failure count at
  exactly 3) — a participant who investigates by hand will find it there
  too, which is fine; nothing claims it's absent.
