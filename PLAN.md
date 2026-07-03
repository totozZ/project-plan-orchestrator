# Project Plan Orchestrator Project Plan

- Updated: 2026-07-03
- Current objective: Pilot the non-destructive adoption workflow in SoccerBot.
- Current work unit: W-002

## Priority queue

<!-- project-plan-orchestrator:work-items:start -->
| ID | Priority | Type | Delivery | Verification | Dependencies | Detail | Tests | Bugs |
|---|---|---|---|---|---|---|---|---|
| W-001 | P0 | feature | Done | Passed | — | [Build the v1 repository](docs/work/W-001-build-v1.md) | [TR-20260703-001](docs/TEST_LOG.md#tr-20260703-001) | — |
| W-002 | P1 | maintenance | Ready | NotRun | W-001 | [Pilot SoccerBot adoption](docs/work/W-002-pilot-soccerbot.md) | — | — |
<!-- project-plan-orchestrator:work-items:end -->

## Next action

Review the SoccerBot adoption preview, apply the migration only when its active dirty worktree can be reconciled safely, then forward-test the unified workflow in Codex and Claude.

## Record index

- [Work items](docs/work/)
- [Bug registry](docs/BUGS.md)
- [Test log](docs/TEST_LOG.md)
