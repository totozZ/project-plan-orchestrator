# W-003 — Improve bilingual README quick starts

- Work ID: W-003
- Type: maintenance
- Priority: P1
- Owner: Codex
- Updated: 2026-07-03

## Outcome

Provide complete English and Simplified Chinese README documents with consistent, copyable quick-start paths for new and existing projects.

## Non-goals

- Do not change CLI behavior.
- Do not alter the active SoccerBot adoption work.

## Dependencies

- W-001.

## Design and interfaces

- Keep `README.md` as the English entry point.
- Add `README.zh-CN.md` as the Simplified Chinese entry point.
- Cross-link the two language versions near the top.
- Cover prerequisites, cloning, initialization, adoption preview, adoption apply, and guard verification in both quick starts.

## Acceptance

- [x] English and Simplified Chinese README documents link to each other.
- [x] Both quick starts describe the same new-project and existing-project workflows.
- [x] Commands match the current `planctl.py` CLI.
- [x] Windows path usage is called out.
- [x] Repository tests and the plan guard pass.

## Implementation notes

- Reworked the English introduction into a dedicated English README.
- Added a complete Simplified Chinese README rather than a short translated summary.
- Added matching quick starts with the repository URL and end-to-end guard commands.

## Verification

- Passed: [TR-20260703-002](../TEST_LOG.md#tr-20260703-002).

## Known issues

- None recorded.

## Next action

Continue the SoccerBot adoption pilot under W-002.
