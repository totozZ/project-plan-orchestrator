---
name: project-plan-orchestrator
description: Orchestrate plan-driven delivery in repositories that use PLAN.md, linked work-item documents, bug records, and test evidence. Use when initializing or adopting this project-planning system, continuing the highest-priority ready item, implementing a planned feature, fixing a tracked bug, recording verification, updating delivery status, or finishing any delivery change that must pass the project plan guard.
---

# Project Plan Orchestrator

Keep the repository's living plan truthful while moving one bounded work unit from intent to verified delivery.

## Choose the operation

- If `plan-orchestrator.json` is absent, initialize a new project or adopt an existing one with `scripts/planctl.py`.
- If the user names a work item, use it unless doing so conflicts with an unresolved dependency or product decision.
- If the user says "continue", "next", or equivalent, select the first `Ready` item at the highest priority whose dependencies are `Done`.
- If the request changes priorities, scope, public interfaces, or an accepted design, obtain the user's decision before implementation.
- Record durable direction, architecture, scope-boundary, technology-stack, delivery-standard, or explicit user decisions in `docs/DECISIONS.md`.
- For read-only explanation or review, inspect the plan and evidence without changing project records.

Read [references/protocol.md](references/protocol.md) before changing managed project state. Read [references/adoption.md](references/adoption.md) when adding the system to an existing repository. Read [references/validation.md](references/validation.md) when configuring or diagnosing the guard.

## Run a delivery work unit

1. Read `plan-orchestrator.json`, `PLAN.md`, and the selected linked work document.
2. Confirm the work item is `Ready` or `InProgress`, its dependencies are `Done`, and its next slice is small enough to implement and verify in one work unit.
3. Set the item to `InProgress` before delivery edits. Preserve the existing priority unless the user approved a change.
4. Implement only the selected slice. Record newly discovered scope or design conflicts instead of silently expanding the work.
5. Run proportionate automated and manual verification.
6. Append one test record for the work unit. Use `NotRun` with a concrete reason when verification was impossible; never invent a pass.
7. Update the work document with actual implementation notes, remaining acceptance gaps, and the next atomic action.
8. Update `docs/BUGS.md` when the work type is `bug` or a bug was discovered, changed, fixed, or closed.
9. Update `docs/DECISIONS.md` only when the work records a direction, architecture, scope-boundary, technology-stack, delivery-standard, or explicit user choice.
10. Update `PLAN.md` last so its status and links summarize the resulting repository state.
11. Run `.project-plan/planctl.py check --root .`. Resolve every error before handing off.

Keep delivery and verification separate. `Implemented` means the change exists; `Done` requires `Passed` verification, or an explicit `N/A` verification record with rationale.
Do not put task lists, bugs, routine implementation notes, or test results in `docs/DECISIONS.md`.

## Initialize or adopt

Run from this skill directory:

```text
python scripts/planctl.py init --root <project> --agents codex,claude
python scripts/planctl.py adopt --root <project>
python scripts/planctl.py adopt --root <project> --apply --agents codex,claude
```

Treat `adopt` without `--apply` as read-only. Preserve existing documentation during adoption; append only marked managed sections and create missing records.
`adopt --apply` persists the previewed planning-document candidates in the adoption work document, but it never infers historical `Done` or `Passed` state. Treat the guard and Dashboard incomplete-adoption warning as a prompt to finish mapping and verification, even when structural validation succeeds.

## View project status

The vendored CLI can run an optional, loopback-only dashboard without changing managed records:

```text
python .project-plan/planctl.py serve --root .
```

Use `--port <number>` to select another port and `--no-browser` for headless use. The dashboard is a read-only convenience view; never make it a required delivery or CI step, and continue to treat the repository records as the source of truth.

## Handle interruption or failure

Before yielding after delivery edits:

- Leave the item `InProgress`, `Implemented`, or `Blocked` according to reality.
- Record failed or unavailable verification in `docs/TEST_LOG.md`.
- Record any reproducible defect in `docs/BUGS.md`.
- State the exact next action in the work document and `PLAN.md`.
- Run the guard even when the work is incomplete.

Do not mark work `Done`, close a bug, remove an unresolved issue, or claim a test result without linked evidence.
