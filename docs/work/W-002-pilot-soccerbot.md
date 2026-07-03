# W-002 — Pilot SoccerBot adoption

- Work ID: W-002
- Type: maintenance
- Priority: P1
- Owner: Unassigned
- Updated: 2026-07-03

## Outcome

Adopt Project Plan Orchestrator in SoccerBot without losing its existing plan, design history, active dirty changes, or project-specific workflow knowledge.

## Non-goals

- Do not apply migration while unrelated SoccerBot delivery changes cannot be separated safely.
- Do not delete the existing `plan-sync`, `design-doc-sync`, or `impl-phase` Skills before behavior parity is demonstrated.

## Dependencies

- W-001.

## Design and interfaces

- Retain the existing root `PLAN.md`.
- Link active documents in place rather than moving or duplicating them.
- Add dedicated bug and test evidence records.
- Map the three legacy Skills into the unified preflight, implementation, evidence, and plan-sync lifecycle.

## Acceptance

- [ ] Review and accept the migration mapping for the existing plan and six active documentation candidates.
- [ ] Run `adopt --apply` against a safe SoccerBot worktree.
- [ ] Reconcile existing project status and detailed design ownership.
- [ ] Pass the vendored plan guard without weakening delivery globs.
- [ ] Forward-test equivalent workflows in fresh Codex and Claude sessions.
- [ ] Retire legacy Skills only after parity is confirmed.

## Implementation notes

- A read-only adoption preview completed successfully.
- The preview found the existing `PLAN.md` and six active top-level/docs candidates while excluding vendored Unity Skills and the temporary staging copy.
- No SoccerBot file was changed by the preview.

## Verification

- Not run; the preview was read-only and the actual migration has not been authorized against the dirty worktree.

## Known issues

- SoccerBot currently contains unrelated uncommitted feature work, so automatic adoption would mix governance changes into an active delivery diff.

## Next action

Review the six-document mapping and choose a safe migration point before running `adopt --apply`.
