<!-- project-plan-orchestrator:instructions:start -->
## Project Plan Orchestrator

For every delivery change:

1. Read `plan-orchestrator.json`, `PLAN.md`, and the current linked work document.
2. When asked to continue, select the highest-priority `Ready` item whose dependencies are `Done`.
3. Keep delivery and verification separate; implementation alone is not `Done`.
4. Before handoff, update the work document, `docs/TEST_LOG.md`, relevant bugs, and `PLAN.md`.
5. Run `python .project-plan/planctl.py check --root .` and resolve every error.

Do not mark work `Done` or bugs `Closed` without linked verification evidence.
<!-- project-plan-orchestrator:instructions:end -->
