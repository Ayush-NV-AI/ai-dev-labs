# Lab 2.1 — characterizing legacy code

## File

`src/legacy/pricing.py` — one function, `price_order(order, customer, promos)`,
plus its small set of private helpers.

## The constraint

Whatever you do to this module, its behaviour must be **identical** at
the end — same inputs, same outputs, bugs and all. This is a
characterization exercise, not a refactor-and-fix exercise: you are
pinning down what the code actually does before anyone is allowed to
change how it does it.

## What to do

Write characterization tests against the current behaviour. Use them to
build confidence that you understand what this function does for a
representative range of inputs.

If, in the course of doing that, you find something that looks like a
genuine bug — a case where the code's behaviour is surely not what
anyone intended — **write it down**. Do not fix it. Fixing it changes
behaviour, and this exercise is about characterizing behaviour, not
correcting it.
