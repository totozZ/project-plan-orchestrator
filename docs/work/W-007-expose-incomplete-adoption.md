# W-007 - Expose incomplete existing-project adoption

- Work ID: W-007
- Type: bug
- Priority: P0
- Owner: Codex
- Updated: 2026-07-15

## Outcome

Make the migration skeleton created by `adopt --apply` self-explanatory: preserve the discovered legacy planning-document inventory, show that adoption is incomplete, and state that Dashboard progress covers only managed work with verification evidence.

## Non-goals

- Do not infer work-item boundaries, delivery states, or verification results from arbitrary legacy Markdown.
- Do not add an automatic mapping command in this work unit.
- Do not move, overwrite, or duplicate legacy project documents.

## Dependencies

- W-001.
- W-006.

## Design and interfaces

- Persist the pre-apply `document_candidates` as an unchecked checklist in the generated adoption work document.
- Keep repeated `adopt --apply` non-destructive while allowing it to backfill the inventory into a legacy generated adoption document.
- Detect the canonical single-item adoption skeleton from managed plan data and expose a structured Dashboard adoption state plus a prominent diagnostic.
- Emit the same condition as a non-blocking guard warning.
- Keep verified-progress calculation unchanged; historical completion is never inferred without managed work and linked evidence.

## Acceptance

- [x] Adoption preview remains read-only and `--apply` preserves every existing document.
- [x] The adoption work document contains every reported legacy planning-document candidate as a pending mapping checklist.
- [x] Re-running `adopt --apply` can backfill that checklist into a previously generated adoption work document without duplicating it.
- [x] Dashboard API and UI identify incomplete adoption and explain the verified-progress scope.
- [x] `check` remains successful but prints an incomplete-adoption warning.
- [x] Legacy completion wording never increases verified progress.
- [x] Automated tests, source/vendored parity, and both plan guards pass.

## Implementation notes

- Diagnosed from the supplied SoccerBot reproduction: Dashboard parsing and progress math were correct; the adoption flow discarded its preview inventory after printing it.
- Added marked adoption-inventory sections with unchecked candidate checklists. New adoption writes the pre-apply inventory, while a repeated apply backfills an older generated work document and preserves an existing checklist unchanged.
- Excluded orchestrator-owned bug, test, decision, and managed work records from repeated-adoption candidate discovery.
- Added a shared adoption-state reader for the Dashboard API and guard. The state includes candidate/review counts and stays incomplete until the adoption work item is `Done` with `Passed` or justified `N/A` verification.
- Added a prominent Dashboard diagnostic and progress-scope explanation plus a non-blocking `check` warning; verified-progress calculation itself remains unchanged.
- Updated English/Chinese onboarding documentation, the adoption reference, and D-002 to make the evidence-conservative migration boundary explicit.

## Verification

- Passed: [TR-20260715-002](../TEST_LOG.md#tr-20260715-002).

## Known issues

- Automatic draft work-item generation remains future scope.

## Next action

Return to the planned transactional `next`, `start`, `record-test`, and `complete` CLI command design; keep automatic draft adoption mapping as a separately scoped future item.
