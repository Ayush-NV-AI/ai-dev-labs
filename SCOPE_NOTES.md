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

## 2026-09-11 — remaining six branches + Prompt V verification

This session built everything the prior run left as TODO: `lab-3-1-design`,
`lab-3-2-undocumented`, `lab-3-2-review-me`, `lab-4-1-agent`,
`lab-4-2-sast`, `lab-5-2-capstone`, updated `main`'s README branch table
from TODO to built, and ran the full Prompt V verification pass. Results
are in `VERIFICATION_REPORT.md` at the repo root. Judgment calls made
along the way:

- **No remote, no real PR.** Per instructions for this run, nothing was
  pushed and no PR was opened anywhere. `lab-3-2-review-me` was built
  exactly as Prompt 6 specifies (the bulk-send diff with all three
  ACT-category bugs genuinely present, verified by grep and by pytest
  staying green despite them), and `PR_DESCRIPTION.md` on that branch
  holds the intended title + description for the user to paste in
  verbatim once he pushes to a real host and opens
  `lab-3-2-review-me` → `lab-3-2-undocumented` himself.
- **`lab-3-2-review-me` is not ruff-clean, and that's intentional.**
  Prompt V's ruff-clean bar names only `lab-2-1-legacy` and
  `lab-4-2-sast/src/insecure_examples` as exceptions, but Prompt 6's own
  spec for this branch explicitly requires an IGNORE-category finding
  set "style the linter already owns" — inconsistent quote style,
  imports out of order, two lines over the length limit. Fidelity to
  Prompt 6 (the more specific, later instruction for this exact branch)
  won out: `ruff check .` on `lab-3-2-review-me` reports exactly 3
  findings (one unsorted-import block, two `E501`s), all inside the two
  files touched by the bulk-send diff
  (`src/api/routes/notifications.py`, `src/api/schemas.py`), and all
  are the deliberately-seeded IGNORE items, not accidental noise. See
  `VERIFICATION_REPORT.md` for the reasoning recorded as a FAIL-with-
  explanation rather than a silent pass.
- **`lab-4-1-agent`'s reservation feature is new, not reused.** The
  prompt's PRESENT list (reservations model/repo/service/routes,
  "complete and tested") doesn't already exist on `main` — only
  `Resource` does, per the judgment call above from the prior session.
  Built a full, working reservation CRUD feature from scratch for this
  branch (independent of `lab-1-2-scaffold`'s reservation scaffold,
  which is a different, deliberately-incomplete branch cut from the same
  `main`) so there is a complete, real pattern for the waitlisting task
  spec to point at.
- **`.semgrep.yml` ruleset design.** Iterated on all nine rules against
  a real, separate `git worktree` of `main` until it hit zero findings,
  then against nine seeded files in `src/insecure_examples/` until all
  nine rules fired at least once (17 findings total). The
  `missing-auth-check-on-mutating-route` rule uses a `pattern-not-regex`
  over the whole matched route (decorator + signature + body) rather
  than a structural "no auth dependency" pattern-not, since `main` and
  every branch checked in this run have no authentication system at all
  — a structurally-precise rule would have nothing to distinguish
  against here. This is noted as a known simplification, not a final
  answer for a repo that later adds real auth.
- **Semgrep was actually installable and runnable in this environment**
  (`pip install semgrep` succeeded, version 1.177.0), so every semgrep
  claim in `VERIFICATION_REPORT.md` is a real, executed result, not a
  best-effort unverified ruleset.
- **`check_dependencies.py` excludes `src/insecure_examples/` from its
  import scan.** Those files intentionally import packages (`requests`,
  `PyYAML`) the real app has no reason to depend on; including them would
  add noise, not signal, to the dependency cross-check.
- **The TypeScript mirror gap on `lab-1-1-compare` is still open.** It
  was out of scope for the prior session and out of scope for this one
  too (this run's scope was the six remaining branches plus Prompt V);
  `npm --prefix ts test` still fails because `ts/` does not exist. Flagged
  again here so it doesn't get lost.
