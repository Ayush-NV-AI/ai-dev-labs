# Lab 2.2 — root-causing a bug

## What to do

1. Run the test suite.
2. Read the failure output.
3. Before you touch any code, be able to state the mechanism — what
   goes wrong, and why — in one sentence.
4. Only then fix it.

```bash
pytest -q
```

You should see exactly three failures, all in `tests/test_availability.py`.
That is the whole symptom you get. Where the actual defect lives is for
you to find.
