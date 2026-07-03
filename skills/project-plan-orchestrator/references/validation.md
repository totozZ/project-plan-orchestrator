# Plan guard validation

## Structural checks

The guard verifies:

- Required configuration and managed documents exist.
- Work, bug, and test IDs are unique and well formed.
- Priorities, work types, delivery states, verification states, and bug states are valid.
- Work-document links exist and identify the same work item.
- Ready or active work has only `Done` dependencies.
- `Done` work links to a `Passed` test record, or to an `N/A` record with rationale.
- `Closed` bugs link to a `Passed` test record.
- Managed local Markdown links resolve.
- Completed work has no unchecked acceptance item.

## Change-sync checks

When Git changes match `delivery_globs` and do not match `exempt_globs`, the same diff must also contain:

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
