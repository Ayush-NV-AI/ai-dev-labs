# Verification Report — Prompt V

Run against the repo at `C:\Claude\T-Systems\code`, all checks executed
for real (not described from memory). No remote is configured; "pushed"
below always means "committed locally, ready to push."

## Structure

| Check | Result | Detail |
|---|---|---|
| Exactly the 11 expected branches exist | PASS | `main`, `lab-1-1-compare`, `lab-1-2-scaffold`, `lab-2-1-legacy`, `lab-2-2-bug`, `lab-3-1-design`, `lab-3-2-undocumented`, `lab-3-2-review-me`, `lab-4-1-agent`, `lab-4-2-sast`, `lab-5-2-capstone` — `git branch --format='%(refname:short)'` |
| All branches pushed | FAIL | No remote configured anywhere in this build, by design — see `SCOPE_NOTES.md`. Nothing to push to. Ayush pushes manually. |
| Every branch cut from `main` (except `lab-3-2-review-me`, from `lab-3-2-undocumented`) | PASS | Verified via `git merge-base` against each branch; `lab-3-2-review-me`'s merge-base with `lab-3-2-undocumented` equals `lab-3-2-undocumented`'s own tip |
| Every branch contains `main`'s `README.md` and `scripts/verify_setup.py` | PASS | Checked `test -f` on both files on all 11 branches |
| `main`'s README branch table filled in, one row per lab branch | PASS | Updated this run (commit `8bf3d99`); all 10 lab rows now say "built" with the lab they serve |

## Per-branch

`pip install -r requirements.txt -r requirements-dev.txt` is identical
across every branch (same file hash on all 11) and was verified to
succeed from a **fresh venv** once — see Detail column, not repeated
per-branch below.

| Branch | pip install | ruff check . | pytest -q |
|---|---|---|---|
| `main` | PASS (fresh venv) | PASS (clean) | PASS (6 passed) |
| `lab-1-1-compare` | PASS (same file) | PASS (clean) | PASS (34 passed) |
| `lab-1-2-scaffold` | PASS (same file) | PASS (clean) | PASS (12 passed) |
| `lab-2-1-legacy` | PASS (same file) | **FAIL (expected)** — 9 findings, all in `src/legacy/pricing.py` (the documented exception) | PASS (6 passed) |
| `lab-2-2-bug` | PASS (same file) | PASS (clean) | **FAIL (expected)** — exactly 3 failures, all in `tests/test_availability.py` |
| `lab-3-1-design` | PASS (same file) | PASS (clean) | PASS (6 passed — inherited from `main`, no new tests; docs-only branch) |
| `lab-3-2-undocumented` | PASS (same file) | PASS (clean) | PASS (24 passed) |
| `lab-3-2-review-me` | PASS (same file) | **FAIL (see note below)** — 3 findings: unsorted import block + one `E501` in `src/api/routes/notifications.py`, one `E501` in `src/api/schemas.py` | PASS (28 passed) |
| `lab-4-1-agent` | PASS (same file) | PASS (clean) | PASS (21 passed) |
| `lab-4-2-sast` | PASS (same file) | **FAIL (expected)** — 4 findings, all in `src/insecure_examples/` (the documented exception) | PASS (6 passed) |
| `lab-5-2-capstone` | PASS (same file) | PASS (clean) | PASS (6 passed — no new source beyond `main`) |

**Note on `lab-3-2-review-me`'s ruff FAIL:** Prompt V's ruff-clean bar
names only `lab-2-1-legacy` and `lab-4-2-sast/src/insecure_examples` as
exceptions. But Prompt 6 explicitly requires this branch to seed
IGNORE-category findings — "style the linter already owns": inconsistent
quote style, imports out of order, two lines over the length limit —
as part of the ACT/JUDGE/IGNORE triage exercise. This build followed
Prompt 6 literally: the 3 findings are exactly those seeded IGNORE items
(confirmed by file/line — see `SCOPE_NOTES.md`), not accidental noise
elsewhere in the diff. Recorded as a FAIL against Prompt V's letter, with
this explanation, rather than silently passed or silently dropped from
the branch.

## Negative checks

| Branch | Check | Result |
|---|---|---|
| `lab-1-1-compare` | `summarise_orders` raises `NotImplementedError`; `docs/LAB-1-1.md` doesn't mention empty lists/ties | PASS |
| `lab-1-2-scaffold` | `src/api/routes/reservations.py` absent; `docs/LAB-1-2.md` doesn't state the half-open boundary rule | PASS |
| `lab-2-1-legacy` | No tests for `src/legacy/pricing.py` outside the skipped reference file; no docstring enumerating its behaviours | PASS |
| `lab-2-2-bug` | No TODO/FIXME/XXX/HACK anywhere in `src/`; `tests/test_intervals.py` doesn't test the end boundary of `overlaps()` | PASS |
| `lab-3-2-undocumented` | Zero docstrings in `src/notifications` | PASS — ast-based checker prints `clean` |
| `lab-3-2-review-me` | The three ACT bugs are genuinely present in the diff | PASS — confirmed by grep: f-string SQL in `bulk.py`, missing `await` on `mark_failed`, no cap on batch size; pytest stays green despite all three |
| `lab-4-1-agent` | No `WaitlistEntry`, no `WaitlistRepository`, no `waitlist` field on any schema | PASS — grep for both class names and the schema field returns nothing in `src/`/`tests/` |
| `lab-4-1-agent` | Trip-hazard test (exact 409 body) exists in `test_reservations.py` | PASS |
| `lab-4-1-agent` | `docs/TRAINER-4-1-REFERENCE.md` is markdown only, no code file implements waitlisting | PASS |
| `lab-5-2-capstone` | No implementation of any of the three brief options (fee/blackout/search) | PASS |

## Functional

| Check | Result | Detail |
|---|---|---|
| `uvicorn src.api.app:create_app --factory` starts, `/health` → 200, on every branch except `lab-3-1-design` | PASS | All 10 applicable branches returned `200` |
| `python scripts/verify_setup.py` exits 0 | PASS | Ran on `main`; all 5 automated checks PASS |
| `npm --prefix ts test` on `lab-1-1-compare` | **FAIL** | `ts/` does not exist — out of scope in the prior session (documented in `SCOPE_NOTES.md`) and out of scope for this session too (this run's scope was the 6 remaining branches + Prompt V, not revisiting `lab-1-1-compare`) |
| `semgrep --config .semgrep.yml src/`: zero findings on `main` | PASS | Verified twice: once in-place on `lab-4-2-sast`/`lab-5-2-capstone`'s main-equivalent source, and once against a genuinely separate `git worktree` of the real `main` tip |
| `semgrep --config .semgrep.yml src/`: all seeded findings on `lab-4-2-sast` | PASS | 17 findings across all 9 rules against `src/insecure_examples/` (9 files, one per category) |
| `lab-2-2-bug`: `<=`→`<` in `overlaps()` makes all tests pass, then reverted | PASS | Before: 3 failures. After the one-character edit: all 40 pass. Reverted; confirmed back to 3 failures. |

## Semgrep — was it actually runnable?

Yes. `pip install semgrep` succeeded in this environment (version
`1.177.0`), and every semgrep result above is a real executed scan, not
a best-effort static review. `.semgrep.yml` ships 9 hand-tuned rules
(string-built SQL, `subprocess`/`os.system` shell injection,
`requests`/`httpx` TLS verification disabled, hardcoded secrets,
permissive CORS, debug flags true, missing auth on mutating routes,
unsafe deserialisation via `pickle`/`yaml.load`, broad except-pass).

## What needs Ayush's manual attention

1. **Push everything to a real host, then open the real PR.** No remote
   is configured. Once pushed, open `lab-3-2-review-me` → 
   `lab-3-2-undocumented` and paste `PR_DESCRIPTION.md` (on
   `lab-3-2-review-me`) in verbatim as the title + description. Leave it
   open, unreviewed, per the lab design — and verify with a second/test
   account that it's actually visible to participants once it's real.
2. **The Lab 1.1 two-assistants comparison check** ("ask two different
   assistants to implement `summarise_orders`, confirm they visibly
   disagree on the empty-list case") is called out in the master prompt
   as the one thing to test personally, not delegate. Not something this
   session can do — needs Ayush running two real assistant sessions.
3. **`lab-1-1-compare`'s missing TypeScript mirror** — still not built,
   across two sessions now. Decide whether it's needed before Monday or
   staying out of scope permanently.
4. **`lab-3-2-review-me`'s ruff findings** — confirm the reasoning above
   (seeded IGNORE items, not real noise) is acceptable, or ask for the
   IGNORE-category items to be reworked so the branch is fully
   ruff-clean, accepting a slightly weaker IGNORE-bucket for the triage
   exercise.
5. **Re-run this whole verification pass on a real Python 3.11 interpreter
   before delivery** if that matters — this build (both sessions) ran on
   3.14.6, the only interpreter available on this machine.
