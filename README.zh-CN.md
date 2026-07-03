# Project Plan Orchestrator

> 面向 AI Agent 的活计划项目编排 Skill：按优先级推进工作，并让实现文档、Bug 状态与测试证据始终同步。

[English](README.md) | 简体中文

`project-plan-orchestrator` 把仓库中的计划转化为可执行的交付契约。它让 Codex 和 Claude 使用同一工作队列，将“实现完成”和“验证通过”明确分开，并在计划、工作记录、Bug 状态或测试证据不同步时阻止交付。

## 快速开始

环境要求：Git、Python 3.11 或更高版本。运行时仅使用 Python 标准库，无需安装第三方依赖。

克隆仓库：

```bash
git clone https://github.com/totozZ/project-plan-orchestrator.git
cd project-plan-orchestrator
```

新项目：生成计划记录和 Agent 指令，然后运行项目内置检查器：

```bash
python skills/project-plan-orchestrator/scripts/planctl.py init --root /path/to/new-project --agents codex,claude

cd /path/to/new-project
python .project-plan/planctl.py check --root .
```

已有项目：先执行只读预览，确认工具将要接入的文件：

```bash
python skills/project-plan-orchestrator/scripts/planctl.py adopt --root /path/to/existing-project
```

检查预览结果后，以非破坏方式应用接入，并运行检查器：

```bash
python skills/project-plan-orchestrator/scripts/planctl.py adopt --root /path/to/existing-project --apply --agents codex,claude

cd /path/to/existing-project
python .project-plan/planctl.py check --root .
```

在 Windows PowerShell 中，请把 `/path/to/existing-project` 换成带引号的 Windows 路径，例如 `"C:\work\my-project"`。

## 管理内容

- `PLAN.md`：目标、优先级、依赖关系、交付状态、验证状态和相关链接。
- `docs/work/W-###-slug.md`：边界明确的设计、验收标准、实现记录和下一步行动。
- `docs/BUGS.md`：缺陷生命周期和回归验证证据。
- `docs/TEST_LOG.md`：只追加、不覆盖的自动化与人工验证记录。
- `plan-orchestrator.json`：项目专属路径、交付文件范围和豁免规则。

生成到 `AGENTS.md` 和 `CLAUDE.md` 中的规则块，让 Codex 与 Claude 始终遵循同一套工作流。工具还会把仅依赖 Python 标准库的检查器安装到 `.project-plan/planctl.py`，用于本地检查和 CI 门禁。

## 安装 Skill

克隆本仓库后，将 `skills/project-plan-orchestrator` 复制或链接到 Agent 使用的 Skills 目录。

Codex：

```text
~/.codex/skills/project-plan-orchestrator
```

Claude：

```text
~/.claude/skills/project-plan-orchestrator
```

`adopt --apply` 会保留已有文件内容，只创建缺失的记录，并在必要时追加带边界标记的治理规则块。

## 运行检查器

```bash
python .project-plan/planctl.py check --root .
python .project-plan/planctl.py check --root . --base origin/main
```

检查器会验证 ID、状态、依赖关系、文档链接、完成证据、Bug 关闭证据，以及交付变更是否同步更新了必要记录。

## 工作方式

Agent 每次处理一个具有优先级、依赖关系和验收标准的小型工作单元。代码写完只能标记为 `Implemented`；获得自动化测试或人工实测证据后，才能进入 `Done`。

初始化或接入后，项目会获得 Codex/Claude 常驻规则、工作文档、Bug 表、测试日志，以及可在本地和 GitHub Actions 中运行的强制检查器。

## 开发与验证

```bash
python -m unittest discover -s tests -v
python skills/project-plan-orchestrator/scripts/planctl.py check --root .
```

本仓库也使用同一套计划契约管理自身开发。
