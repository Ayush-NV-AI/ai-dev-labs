<!-- Hard limit: two pages. If a section needs more, it belongs in a linked doc, not here. -->

# Team AI-Assisted Development Playbook

*Team:* ______________________ *Date:* ______________________

## 1. Tool selection

*Which assistant(s) does this team use for which kind of work, and why?*

- Which tasks go to a codebase-indexing tool vs. an open-tabs-only tool?
- Where does each team member's individual preference end and a team
  standard begin?

______________________________________________________________________

## 2. When to use what

*Chat vs. agent vs. plan mode — what triggers each?*

- What is the signal that a task needs a plan reviewed before code gets
  written, rather than a direct implementation request?
- What's the smallest task this team still bothers prompting for, vs.
  just typing by hand?

______________________________________________________________________

## 3. Review checklist

*What does every human reviewer check on AI-assisted code, every time?*

- What's on this team's ACT list — the class of finding that blocks
  merge without discussion?
- Where's the line between JUDGE (defensible either way) and something
  that needs a second opinion before merge?

______________________________________________________________________

## 4. Guardrails

*What stops an agent from doing the wrong thing, structurally?*

- Which files/directories are off-limits to agent edits without a human
  in the loop?
- What's the test/lint/scan gate an agent's change must clear before a
  human even looks at it?

______________________________________________________________________

## 5. Verification gate

*What must be true before this team calls something "done"?*

- Which of pytest / ruff / semgrep / a manual smoke test are non-
  negotiable, and which are judgment calls?
- Who actually runs the gate — the agent, the human, or CI — and what
  happens when they disagree?

______________________________________________________________________

## 6. Metrics and cadence

*How does this team know the playbook above is working?*

- What's reviewed weekly vs. monthly, and by whom?
- See `docs/MEASUREMENT-PLAN-TEMPLATE.md` for the actual metrics —
  this section is about the cadence of looking at them, not the metrics
  themselves.

______________________________________________________________________
