# Plan guard validation

## Strictness

Configure check strength in `plan-orchestrator.json`:

- `light`: validates the managed plan queue, work IDs, states, and dependencies. Missing work docs, test logs, and Done evidence are non-fatal; incomplete Done evidence is reported as a warning.
- `normal`: adds work-document and test-log requirements, requires Done work to link matching verification evidence, and warns when `docs/DECISIONS.md` is missing.
- `strict`: adds required `docs/BUGS.md`, required `docs/DECISIONS.md`, verified finished-bug states, P0/P1 block reasons, and delivery-file sync checks.

Missing `strictness` defaults to `normal`.

## Structural checks

Depending on strictness, the guard verifies:

- Required configuration and managed documents exist.
- Work, bug, and test IDs are unique and well formed.
- Priorities, work types, delivery states, verification states, and bug states are valid.
- Work-document links exist and identify the same work item.
- Ready or active work has only `Done` dependencies.
- `Done` work links to a `Passed` test record, or to an `N/A` record with rationale.
- `Fixed`, `Resolved`, and `Closed` bugs link to a `Passed` test record in strict mode.
- Managed local Markdown links resolve.
- Completed work has no unchecked acceptance item.

## Change-sync checks

In strict mode, when Git changes match `delivery_globs` and do not match `exempt_globs`, the same diff must also contain:

- `PLAN.md`
- At least one configured work document
- `docs/TEST_LOG.md`
- `docs/BUGS.md` when the current work item type is `bug`

Configure patterns in `plan-orchestrator.json`. Use forward slashes on every platform.

## Local and CI use

```text
python .project-plan/planctl.py check --root .
python .project-plan/planctl.py check --root . --base <git-ref>
python .project-plan/planctl.py check --root . --base <git-ref> --head <git-ref>
```

Without refs, the guard reads staged, unstaged, and untracked files. With `--base`, it compares the base to the working tree or the supplied head. If Git is unavailable, structural checks still run and change-sync checks are skipped with a notice.

The guard proves structural synchronization, not semantic truth. Review the actual diff and test output before recording status.
