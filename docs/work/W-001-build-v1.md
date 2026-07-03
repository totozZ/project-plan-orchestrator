# W-001 — Build the v1 repository

- Work ID: W-001
- Type: feature
- Priority: P0
- Owner: Codex
- Updated: 2026-07-03

## Outcome

Provide a portable `project-plan-orchestrator` Skill that initializes or adopts projects, coordinates prioritized work, and enforces synchronized implementation, bug, and test records.

## Non-goals

- Do not provide hosted project management or issue-tracker integrations.
- Do not support agent-specific adapters beyond Codex and Claude in v1.

## Dependencies

- None.

## Design and interfaces

- Keep the canonical agent workflow in one standard `SKILL.md`.
- Provide `init`, `adopt`, and `check` through a Python standard-library CLI.
- Vendor the checker into managed projects so local and GitHub CI enforcement is self-contained.
- Preserve existing content during adoption and use marked managed blocks.

## Acceptance

- [x] New projects initialize safely and idempotently.
- [x] Existing projects receive a read-only preview and non-destructive adoption path.
- [x] The guard validates IDs, states, dependencies, links, acceptance, and evidence.
- [x] Delivery diffs require synchronized plan, work, and test records.
- [x] Bug work requires synchronized bug records.
- [x] Codex and Claude instruction adapters are generated.
- [x] Automated tests pass on the completed implementation.

## Implementation notes

- The official Skill generator created the canonical skill skeleton and OpenAI UI metadata.
- Templates and protocol references define the common project record contract.
- `planctl.py` provides `init`, read-only/default `adopt`, non-destructive `adopt --apply`, and local/CI `check`.
- Managed projects receive a vendored `.project-plan/planctl.py`, Codex/Claude instruction blocks, and a GitHub Actions guard.
- The adoption inventory is limited to top-level and documentation directories so vendored packages and unrelated Skills do not swamp migration results.

## Verification

- Passed: [TR-20260703-001](../TEST_LOG.md#tr-20260703-001).

## Known issues

- None recorded.

## Next action

Maintain the reusable workflow through linked work items and verification evidence.
