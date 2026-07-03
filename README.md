# Project Plan Orchestrator

> Living-plan-driven project orchestration for AI agents: prioritize work and keep implementation docs, bugs, and test evidence in sync.

English | [简体中文](README.zh-CN.md)

`project-plan-orchestrator` turns a repository plan into an executable delivery contract. It gives Codex and Claude the same work queue, separates implementation from verification, and blocks delivery changes whose plan, work notes, bug state, or test evidence drift out of sync.

## Quick start

Requirements: Git and Python 3.11 or later. The runtime uses only the Python standard library.

Clone the repository:

```bash
git clone https://github.com/totozZ/project-plan-orchestrator.git
cd project-plan-orchestrator
```

For a new project, initialize the plan records and agent instructions, then run the installed guard:

```bash
python skills/project-plan-orchestrator/scripts/planctl.py init --root /path/to/new-project --agents codex,claude

cd /path/to/new-project
python .project-plan/planctl.py check --root .
```

For an existing project, preview the adoption first. The preview is read-only:

```bash
python skills/project-plan-orchestrator/scripts/planctl.py adopt --root /path/to/existing-project
```

Review the reported files, then apply the non-destructive adoption and verify it:

```bash
python skills/project-plan-orchestrator/scripts/planctl.py adopt --root /path/to/existing-project --apply --agents codex,claude

cd /path/to/existing-project
python .project-plan/planctl.py check --root .
```

On Windows PowerShell, replace paths such as `/path/to/existing-project` with a quoted Windows path, for example `"C:\work\my-project"`.

## What it manages

- `PLAN.md`: objectives, priorities, dependencies, delivery state, verification state, and links.
- `docs/work/W-###-slug.md`: bounded design, acceptance, implementation notes, and the next action.
- `docs/BUGS.md`: defect lifecycle and regression evidence.
- `docs/TEST_LOG.md`: append-only automated and manual verification records.
- `docs/DECISIONS.md`: durable project decisions about direction, scope, technology, and delivery standards.
- `plan-orchestrator.json`: repository-specific paths and delivery/exemption globs.

The generated `AGENTS.md` and `CLAUDE.md` blocks keep the workflow resident for Codex and Claude. A vendored, standard-library-only validator at `.project-plan/planctl.py` provides the local and CI gate.

## Generated Files

| File | Purpose |
|---|---|
| `PLAN.md` | The project plan and task queue, including work IDs, status, priority, dependencies, and delivery evidence. |
| `docs/work/W-xxx.md` | A per-work-item record for implementation notes, changes, verification method, and follow-up notes. |
| `docs/BUGS.md` | A defect registry that tracks bug status, impact, fix notes, and verification evidence. |
| `docs/TEST_LOG.md` | The test and verification log that proves work was actually checked, not just marked complete. |
| `docs/DECISIONS.md` | A directional decision log explaining why a solution, dropped direction, technology choice, strictness mode, or delivery boundary was selected. |
| `plan-orchestrator.json` | Project configuration, including paths, globs, and the `strictness` mode. |
| `AGENTS.md` | Persistent project rules for Codex and general AI coding agents. |
| `CLAUDE.md` | Persistent project rules for Claude Code. |
| `.project-plan/planctl.py` | The vendored local project-plan checker used for `init`, `adopt`, and `check`. |
| `.github/workflows/project-plan.yml` | The GitHub Actions workflow that runs the project-plan check in CI. |

## Install the Skill

Clone this repository, then copy or link `skills/project-plan-orchestrator` into the Skills directory used by your agent.

For Codex:

```text
~/.codex/skills/project-plan-orchestrator
```

For Claude:

```text
~/.claude/skills/project-plan-orchestrator
```

Existing file contents are preserved. Adoption creates missing records and appends marked governance blocks where necessary.

## Run the guard

```text
python .project-plan/planctl.py check --root .
python .project-plan/planctl.py check --root . --base origin/main
```

The guard displays the active strictness mode and validates the matching level of IDs, states, dependencies, document links, completion evidence, bug evidence, decision records, and delivery-change synchronization.

## Development

```bash
python -m unittest discover -s tests -v
python skills/project-plan-orchestrator/scripts/planctl.py check --root .
```

This repository manages itself with the same plan contract.
