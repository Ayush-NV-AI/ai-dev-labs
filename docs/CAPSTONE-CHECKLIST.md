# Capstone Checklist

Seven steps, 75 minutes total. Tick each box as you go — a pair that
loses track of the clock is the most common way this session runs long.

- [ ] **00–12 · Design + ADR** — Pick one option from
      `docs/CAPSTONE-BRIEF.md`. Write the ADR: Context / Options /
      Decision / Consequences (see `docs/LAB-3-1-ADR-TEMPLATE.md`).
      Resolve your option's one open ambiguity explicitly.
- [ ] **12–20 · Decompose** — Write the task spec using
      `docs/LAB-4-1-TASK-TEMPLATE.md`: blast radius, definition of done,
      patterns to follow, out of scope. List the files you expect to
      touch.
- [ ] **20–48 · Build** — Implement it. If you're not done by minute 48,
      cut scope, not corners — shrink toward the acceptance criteria, not
      away from tests or error handling.
- [ ] **48–58 · Tests in a fresh context** — Start a new
      assistant/session/context to write tests against your own
      implementation. A fresh context won't inherit your assumptions
      about what "obviously" works.
- [ ] **58–66 · Docs + diagram** — Update or add the doc a future reader
      needs (an ADR update, a short README note, or a docstring on the
      new service function). Generate a sequence or flow diagram of what
      you built and check it against the actual code before trusting it.
- [ ] **66–72 · Scan gate** — Run `semgrep --config .semgrep.yml src/`.
      Triage anything it finds using the table in `docs/LAB-4-2.md`
      before deciding it's safe to ignore.
- [ ] **72–75 · Open the PR** — Push your branch and open the PR. Title
      it like you mean it; a reviewer should be able to tell what
      changed from the title and description alone.
