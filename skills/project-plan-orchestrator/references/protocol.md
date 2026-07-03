# Project planning protocol

## Document contract

`PLAN.md` is the sole project-level queue and status summary. Keep detailed design and implementation notes in `docs/work/`, defects in `docs/BUGS.md`, and verification attempts in `docs/TEST_LOG.md`.

Use these identifiers:

- Work item: `W-001`
- Bug: `BUG-001`
- Test record: `TR-YYYYMMDD-NNN`

Keep the managed Markdown tables and marker comments intact so the validator can read them.

## Work selection

Use priorities `P0` through `P3`, where `P0` is highest. When asked to continue:

1. Exclude items that are not `Ready`.
2. Exclude items with a dependency that is not `Done`.
3. Select the lowest priority number.
4. Break ties by table order.

An explicit user request overrides queue order, but it does not waive unresolved dependencies or authorize reprioritization of unrelated work.

## Work states

Delivery states:

- `Backlog`: recorded but not yet actionable.
- `Ready`: scoped, accepted, and dependency-ready.
- `InProgress`: the active work unit is being changed.
- `Implemented`: implementation exists but completion evidence is absent or incomplete.
- `Done`: acceptance conditions are satisfied and verification is `Passed` or justified `N/A`.
- `Blocked`: progress requires an external decision, input, or state change.
- `Deferred`: intentionally postponed.
- `Cancelled`: intentionally abandoned.

Verification states:

- `NotRun`, `Partial`, `Passed`, `Failed`, or `N/A`.

Use work types `feature`, `bug`, `maintenance`, or `research`.

## Bug states

- `Open`, `Diagnosed`, `FixedUnverified`, `Closed`, or `Deferred`.
- Use `FixedUnverified` after a fix exists but before its regression evidence passes.
- Use `Closed` only with a linked `Passed` test record.

## Evidence rules

Append one test record for every delivery work unit. Include the environment, revision or dirty-tree basis, command or manual procedure, result, evidence, and linked work or bug IDs.

`NotRun` and `N/A` are evidence dispositions, not silent omissions. Give a reason. A manual device check is as valid as an automated test when its procedure and observation are reproducible.

## Update order

After implementation:

1. Append test evidence.
2. Update the detailed work document.
3. Update bugs when applicable.
4. Update `PLAN.md`.
5. Run the guard.

This order keeps the summary derived from the detailed evidence.
