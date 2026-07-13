# TASK-NNN: Title

Status: draft

## Objective

State one observable outcome.

## Approved behavior

- Describe what must happen.
- Describe what must remain compatible.

## Evidence and references

- Link the relevant `docs/migration.md` sections.
- List source files, specifications, fixtures, or prior test evidence.

## Allowed scope

- Files or modules the worker may change.
- Required documentation updates.

## Non-goals

- List adjacent behavior that must not change.

## TDD contract

- Name the failing behavioral test to add first.
- State what regression that test detects.

## Verification

- Commands the worker must run.
- Expected observable results.

## Delegation budget

- State the expected scope or timebox.
- Require an early blocked handoff instead of open-ended investigation.

## Stop conditions

- Conflicting behavior evidence.
- Required scope expansion.
- Unexpected user-owned changes in an allowed file.
- Missing dependency, access, fixture, or specification needed for correctness.
- Any external mutation not explicitly approved in this packet.

## Required handoff

- Status and concise outcome.
- Files changed and why.
- Tests and exact results.
- Assumptions, risks, and unresolved questions.
