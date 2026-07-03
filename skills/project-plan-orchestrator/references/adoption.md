# Adopting an existing repository

## Safe sequence

1. Run `planctl.py adopt --root <project>` without `--apply`.
2. Review the reported plan, status, design, bug, test, and agent-instruction candidates.
3. Run `adopt --apply` to create missing records, append marked plan governance, install the vendored validator, and add missing agent adapters.
4. Map active existing design documents to work items. Prefer linking them in place over moving or duplicating them.
5. Reconcile duplicate status summaries so `PLAN.md` becomes the project-level source of truth.
6. Run the guard and resolve structural errors before changing delivery code.

`adopt --apply` must not replace existing file contents. It may append a clearly delimited managed block to an existing `PLAN.md`, `AGENTS.md`, or `CLAUDE.md`.

## Consolidating older workflows

When a project already has separate implementation, documentation-sync, and plan-sync skills:

- Preserve them during migration.
- Map their behavior into the orchestrator workflow.
- Forward-test equivalent initialization, implementation, bug, and evidence flows.
- Retire the older skills only after the unified guard and workflow cover their active responsibilities.

For SoccerBot, retain the existing root `PLAN.md` and detailed design documents in place, add dedicated bug and test records, then phase out `plan-sync`, `design-doc-sync`, and `impl-phase` after parity is demonstrated.
