# Lab 3.2 — Documenting an Undocumented Service

`src/notifications/` is a fully working, fully tested package with zero
docstrings and zero comments anywhere in it. Naming is reasonable — the
code is readable — but its purpose is not recoverable from reading it
alone. That gap between *what* the code does and *why* it does it is the
whole exercise.

## What to produce

1. A generated architecture/sequence diagram of the dispatch flow
   (`src/notifications/dispatcher.py` is the entry point — it calls at
   least four collaborators). Check the diagram against the code: does it
   include `POST /notifications/_replay`? That route is debug-only, gated
   behind a settings flag, and a generated diagram will happily include it
   as if it were part of the normal flow. Correcting the diagram is part
   of the exercise, not a mistake to avoid.
2. Documentation for `src/notifications/channels/email.py`'s retry
   behaviour. The code will tell you *what* it does (which status codes
   retry, which don't); it will not tell you *why* someone chose that —
   only a human reviewer, or someone who has been paged by an email
   provider before, can supply that part.
3. Module- and function-level docstrings for the package, written the way
   the rest of this repo writes them (see `src/api/routes/resources.py`
   for the house style) — without changing any behaviour.

## Verify you haven't accidentally fixed the exercise

Run this before you start, to confirm the package really is undocumented:

```bash
python - <<'PY'
import ast, pathlib
for p in pathlib.Path("src/notifications").rglob("*.py"):
    t = ast.parse(p.read_text())
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                          ast.AsyncFunctionDef)) and ast.get_docstring(n):
            raise SystemExit(f"docstring found in {p}")
print("clean")
PY
```

## Lab 3.2b — reviewing the bulk-send PR

`lab-3-2-review-me` branches off this one and adds bulk send: one template
fanned out to many recipients in a single request. See
`docs/LAB-3-2-BULK.md` on that branch and `PR_DESCRIPTION.md` for the PR
text as opened. Triage the diff into ACT / JUDGE / IGNORE before you look
at anyone else's notes — a green pipeline is not a review.
