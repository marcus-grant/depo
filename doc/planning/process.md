# Development Process

Principles and learnings about how we develop depo.

## Type Friction as Design Signal

When the type checker fights your implementation, the data model is wrong.
Don't suppress — investigate. Pyright complaints during PR 8's upload work
led from `dict` → `TypedDict` → algebraic union of three TypedDicts,
each representing a distinct upload path. The final design is more
expressive, testable, and self-documenting than the original.

## Start Naive, Let Pressure Reveal Shape

Begin with the simplest implementation. Let tests and types push toward
the right abstraction. The upload module evolved through:

1. Plain `dict` return — no type safety
2. `TypedDict` with `total=False` — pyright couldn't narrow key access
3. Algebraic union of concrete TypedDicts — each branch fully typed

Each step was forced by real friction, not premature abstraction.

## TDD + Strict Typing as Complementary Forces

TDD says "make it work for this case." Typing says "make the contract
precise." The tension between them produces better interfaces. Neither
alone would have arrived at the algebraic upload params.

## Commit Hygiene Under Pressure

When refactoring crosses commit boundaries mid-work, stop and assess.
Stage what's coherent, commit, then continue. Fighting to keep unrelated
changes in one commit creates confusion. Splitting into clean commits is
always worth the pause.
