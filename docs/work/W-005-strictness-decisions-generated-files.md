# W-005 - Add strictness modes and decisions support

- Work ID: W-005
- Type: feature
- Priority: P0
- Owner: Codex
- Updated: 2026-07-03

## Outcome

Support configurable check strictness, add project decision records, and document generated files in both README variants.

## Non-goals

- Do not add external services, databases, web UI, or third-party Python dependencies.
- Do not change the project from a lightweight, repository-native AI coding agent skill.
- Do not rename existing commands or remove current `init`, `adopt`, or `check` behavior.

## Dependencies

- W-001.

## Design and interfaces

- Add `strictness` to `plan-orchestrator.json` with `light`, `normal`, and `strict` modes; missing configuration defaults to `normal`.
- Add `docs/DECISIONS.md` as a generated project decision record for initialization and adoption.
- Keep validation mode behavior in the standard-library `planctl.py` implementation and mirror the vendored copy.
- Document generated and maintained files in English and Chinese README files.

## Acceptance

- [x] `check` displays the active strictness and rejects invalid strictness values.
- [x] `light`, `normal`, and `strict` enforce the requested validation levels.
- [x] `init` and `adopt --apply` create `docs/DECISIONS.md` without overwriting an existing file.
- [x] README and Skill guidance explain DECISIONS and generated-file responsibilities.
- [x] Automated tests and both guard copies pass.

## Implementation notes

- Added configurable `strictness` modes to `planctl.py`, including default `normal`, invalid-value errors, warnings, and CLI display.
- Split structural, evidence, bug, decision-record, blocked-work, and delivery-sync checks across `light`, `normal`, and `strict`.
- Added the `docs/DECISIONS.md` template and made initialization/adoption create it without overwriting existing content.
- Updated README, Skill, agent instruction fragments, and validation/protocol references for generated files and decision-record behavior.
- Expanded unit coverage for strictness defaults, light warnings, normal failures, strict-only checks, invalid strictness, DECISIONS creation, and DECISIONS preservation.

## Verification

- Passed: [TR-20260703-004](../TEST_LOG.md#tr-20260703-004).

## Known issues

- None recorded.

## Next action

Review release metadata and create the `v0.1.0` tag when ready.
