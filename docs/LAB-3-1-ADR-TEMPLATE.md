# ADR-NNNN: <short title>

> Copy this file into `docs/adr/NNNN-short-title.md`, using the next
> number in sequence (see `docs/adr/README.md`). Delete this note line
> once you've filled in the sections below.

## Status

Proposed | Accepted | Superseded by ADR-NNNN

## Context

*Who writes this: you.*

What problem are we solving, and what forces make it hard? State the
numbers and constraints from the brief that actually bear on this
decision — not all of them, just the ones this ADR turns on. This section
should let a reader who has never seen the brief understand why a
decision was needed at all.

## Options

*Who writes this: AI helps.*

List the architectures you seriously considered — at minimum, the one you
picked and the strongest runner-up. For each: a sentence on how it works,
and a sentence on why it does or doesn't survive the anti-requirements. An
assistant is good at generating a wide option set quickly; use it to make
sure you aren't only seeing the first idea that occurred to you.

## Decision

*Who writes this: you.*

Which option did you pick, stated as a single unambiguous sentence, plus
the two or three sentences of reasoning that made it the call. This is the
part nobody else can write for you — it is your team committing to a
position on the ambiguities in the brief.

## Consequences

*Who writes this: AI helps, especially the negative ones.*

What does this decision cost you? Be specific about what gets harder, not
just what gets easier — an assistant is useful here precisely because it
has no investment in the decision looking good. Cover at least: one thing
that becomes harder to change later, one operational cost (on-call,
monitoring, the junior engineers' learning curve), and one way this
decision could age badly if a stated assumption turns out wrong.
