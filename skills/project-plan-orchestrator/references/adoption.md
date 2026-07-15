# Adopting an existing repository

## Safe sequence

1. Run `planctl.py adopt --root <project>` without `--apply`.
2. Review the reported plan, status, design, bug, test, and agent-instruction candidates.
3. Run `adopt --apply` to create missing records, including `docs/DECISIONS.md`, append marked plan governance, install the vendored validator, add missing agent adapters, and persist the preview's document candidates in the adoption work document.
4. Review the adoption inventory checklist and map active existing design documents to work items. Prefer linking them in place over moving or duplicating them.
5. Reconcile duplicate status summaries so `PLAN.md` becomes the project-level source of truth.
6. Run the guard and resolve structural errors before changing delivery code.

`adopt --apply` must not replace existing file contents. It may append a clearly delimited managed block to an existing `PLAN.md`, `AGENTS.md`, or `CLAUDE.md`.

## Migration semantics

- Adoption creates a safe migration work item; it does not infer managed work items, delivery states, or verification results from arbitrary legacy Markdown.
- Until the adoption work item is `Done` with `Passed` or justified `N/A` verification, the guard warns and the Dashboard reports that adoption is incomplete.
- Dashboard progress always counts managed, non-cancelled work and verified completion. During adoption it is migration progress, not a reconstruction of historical project completion.
- Re-run `adopt --apply` to backfill the inventory into a migration work document created by an older version. Existing inventory content and checklist state are preserved.

## Consolidating older workflows

When a project already has separate implementation, documentation-sync, and plan-sync skills:

- Preserve them during migration.
- Map their behavior into the orchestrator workflow.
- Forward-test equivalent initialization, implementation, bug, and evidence flows.
- Retire the older skills only after the unified guard and workflow cover their active responsibilities.
