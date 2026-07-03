# W-004 — Remove project-specific content

- Work ID: W-004
- Type: maintenance
- Priority: P0
- Owner: Codex
- Updated: 2026-07-03

## Outcome

Keep the public repository focused on a reusable Project Plan Orchestrator Skill with no dependency on or references to an unrelated private project.

## Non-goals

- Do not change the `planctl.py` command interface.
- Do not remove generic adoption guidance or automated adoption coverage.

## Dependencies

- W-001.

## Design and interfaces

- Remove the project-specific work item and its linked document.
- Remove project-specific language from shipped Skill references and historical project records.
- Retain generic adoption guidance and automated verification.

## Acceptance

- [x] No removed project or work-item name remains in tracked repository content.
- [x] Generic initialization, adoption, and validation tests still pass.
- [x] The project plan and linked records pass the repository guard.

## Implementation notes

- Removed the project-specific work item from the priority queue and deleted its work document.
- Removed project-specific language from the shipped adoption reference and existing project records.
- Retained the generic legacy-workflow migration guidance and automated adoption coverage.

## Verification

- Passed: [TR-20260703-003](../TEST_LOG.md#tr-20260703-003).

## Known issues

- None recorded.

## Next action

Review release metadata and create the `v0.1.0` tag when ready.
