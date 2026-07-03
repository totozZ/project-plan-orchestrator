# Project Plan Orchestrator

> Living-plan-driven project orchestration for AI agents: prioritize work and keep implementation docs, bugs, and test evidence in sync. 面向 AI Agent 的活计划项目编排 Skill：拆分并排序任务，同步实现文档、Bug 与测试记录。

`project-plan-orchestrator` turns a repository plan into an executable delivery contract. It gives Codex and Claude the same work queue, separates implementation from verification, and blocks delivery changes whose plan, work notes, bug state, or test evidence drift out of sync.

## What it manages

- `PLAN.md`: objectives, priorities, dependencies, delivery state, verification state, and links.
- `docs/work/W-###-slug.md`: bounded design, acceptance, implementation notes, and the next action.
- `docs/BUGS.md`: defect lifecycle and regression evidence.
- `docs/TEST_LOG.md`: append-only automated and manual verification records.
- `plan-orchestrator.json`: repository-specific paths and delivery/exemption globs.

The generated `AGENTS.md` and `CLAUDE.md` blocks keep the workflow resident for Codex and Claude. A vendored, standard-library-only validator at `.project-plan/planctl.py` provides the local and CI gate.

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

## Initialize a new project

```text
python skills/project-plan-orchestrator/scripts/planctl.py init \
  --root /path/to/project \
  --agents codex,claude
```

## Adopt an existing project

Preview first:

```text
python skills/project-plan-orchestrator/scripts/planctl.py adopt \
  --root /path/to/project
```

Apply non-destructively:

```text
python skills/project-plan-orchestrator/scripts/planctl.py adopt \
  --root /path/to/project \
  --apply \
  --agents codex,claude
```

Existing file contents are preserved. Adoption creates missing records and appends marked governance blocks where necessary.

## Run the guard

```text
python .project-plan/planctl.py check --root .
python .project-plan/planctl.py check --root . --base origin/main
```

The guard validates IDs, states, dependencies, document links, completion evidence, closed-bug evidence, and whether delivery changes synchronized the required records.

## 中文快速说明

这个 Skill 把 `PLAN.md` 变成项目执行入口。Agent 每次只处理一个有优先级、有依赖、有验收标准的小工作单元；代码写完只能标记为 `Implemented`，具有自动测试或人工实测证据后才能进入 `Done`。

初始化后，项目会获得 Codex/Claude 常驻规则、功能实现文档、Bug 表、实测日志，以及可以在本地和 GitHub Actions 中运行的强制检查器。

## Development

```text
python -m unittest discover -s tests -v
python skills/project-plan-orchestrator/scripts/planctl.py check --root .
```

This repository manages itself with the same plan contract.
