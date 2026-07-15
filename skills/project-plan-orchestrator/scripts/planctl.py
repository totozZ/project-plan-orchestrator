#!/usr/bin/env python3
"""Initialize, adopt, validate, and visualize Project Plan Orchestrator repositories."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import unquote, urlparse


SCHEMA_VERSION = 1
WORK_ID_RE = re.compile(r"\bW-\d{3,}\b")
BUG_ID_RE = re.compile(r"\bBUG-\d{3,}\b")
TEST_ID_RE = re.compile(r"\bTR-\d{8}-\d{3,}\b")
LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")

PLAN_START = "<!-- project-plan-orchestrator:work-items:start -->"
PLAN_END = "<!-- project-plan-orchestrator:work-items:end -->"
BUG_START = "<!-- project-plan-orchestrator:bugs:start -->"
BUG_END = "<!-- project-plan-orchestrator:bugs:end -->"
TEST_START = "<!-- project-plan-orchestrator:tests:start -->"
TEST_END = "<!-- project-plan-orchestrator:tests:end -->"
INSTRUCTION_START = "<!-- project-plan-orchestrator:instructions:start -->"
ADOPTION_CANDIDATES_START = "<!-- project-plan-orchestrator:adoption-candidates:start -->"
ADOPTION_CANDIDATES_END = "<!-- project-plan-orchestrator:adoption-candidates:end -->"
DECISIONS_PATH = "docs/DECISIONS.md"

STRICTNESS_ORDER = {"light": 0, "normal": 1, "strict": 2}
STRICTNESS_VALUES = tuple(STRICTNESS_ORDER)
PRIORITIES = {"P0", "P1", "P2", "P3"}
WORK_TYPES = {"feature", "bug", "maintenance", "research"}
DELIVERY_STATES = {
    "Backlog",
    "Ready",
    "InProgress",
    "Implemented",
    "Done",
    "Blocked",
    "Deferred",
    "Cancelled",
}
VERIFICATION_STATES = {"NotRun", "Partial", "Passed", "Failed", "N/A"}
BUG_STATES = {
    "Open",
    "Diagnosed",
    "FixedUnverified",
    "Fixed",
    "Resolved",
    "Closed",
    "Deferred",
}
VERIFIED_BUG_STATES = {"Fixed", "Resolved", "Closed"}
TEST_RESULTS = {"Passed", "Failed", "Blocked", "NotRun", "N/A"}

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"

DASHBOARD_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project Plan Dashboard</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <main class="shell">
    <header class="hero">
      <div>
        <p class="eyebrow">PROJECT PLAN ORCHESTRATOR</p>
        <h1 id="project-name">Loading project…</h1>
        <p id="objective" class="objective"></p>
      </div>
      <div id="connection" class="connection waiting"><span></span>连接中</div>
    </header>

    <section id="diagnostics" class="diagnostics" hidden>
      <strong>计划记录需要注意</strong>
      <ul id="diagnostic-list"></ul>
    </section>

    <section class="overview">
      <article class="progress-card panel">
        <div class="section-heading">
          <div><p class="label">VERIFIED PROGRESS</p><h2>已验证交付进度</h2></div>
          <strong id="progress-percent" class="percent">0%</strong>
        </div>
        <progress id="progress-bar" class="track" max="100" value="0">0%</progress>
        <p id="progress-detail" class="muted">等待计划数据…</p>
      </article>
      <div id="count-grid" class="count-grid"></div>
    </section>

    <section class="focus-grid">
      <article class="panel">
        <p class="label">CURRENT WORK</p>
        <div id="current-work"></div>
      </article>
      <article class="panel next-panel">
        <p class="label">NEXT ACTION</p>
        <p id="next-action" class="next-action">等待计划数据…</p>
        <p id="plan-updated" class="muted"></p>
      </article>
    </section>

    <section class="panel work-panel">
      <div class="section-heading work-heading">
        <div><p class="label">WORK QUEUE</p><h2>功能与工作项</h2></div>
        <div class="controls">
          <input id="search" type="search" placeholder="搜索 ID、标题或类型" aria-label="搜索工作项">
          <select id="status-filter" aria-label="按交付状态筛选">
            <option value="">全部状态</option>
            <option>Backlog</option><option>Ready</option><option>InProgress</option>
            <option>Implemented</option><option>Blocked</option><option>Deferred</option>
            <option>Done</option><option>Cancelled</option>
          </select>
          <button id="refresh" type="button">立即刷新</button>
        </div>
      </div>
      <div class="auto-row">
        <label><input id="auto-refresh" type="checkbox" checked> 每 2 秒自动刷新</label>
        <span id="refreshed-at" class="muted"></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>工作项</th><th>优先级</th><th>类型</th><th>交付</th><th>验证</th><th>依赖</th></tr></thead>
          <tbody id="work-items"></tbody>
        </table>
        <p id="empty-state" class="empty" hidden>没有符合当前筛选条件的工作项。</p>
      </div>
    </section>

    <footer>只读本地视图 · 仓库文件仍是唯一事实来源 · Ctrl+C 停止服务器</footer>
  </main>
  <script src="/app.js" defer></script>
</body>
</html>
"""

DASHBOARD_CSS = """:root {
  color-scheme: dark;
  --bg: #08111f; --panel: rgba(16, 30, 50, .88); --line: #263a55;
  --text: #edf5ff; --muted: #93a8c2; --cyan: #55d6be; --blue: #62a8ff;
  --amber: #f4bd62; --red: #ff7a87; --green: #64df9b;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; color: var(--text); background:
  radial-gradient(circle at 12% 0%, rgba(44, 122, 190, .25), transparent 32rem),
  radial-gradient(circle at 90% 10%, rgba(69, 190, 164, .13), transparent 30rem), var(--bg); }
.shell { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 44px 0 30px; }
.hero, .section-heading, .auto-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.hero { margin-bottom: 28px; }
.eyebrow, .label { margin: 0 0 8px; color: var(--cyan); font-size: 11px; font-weight: 800; letter-spacing: .16em; }
h1 { margin: 0; max-width: 780px; font-size: clamp(30px, 5vw, 55px); line-height: 1.02; letter-spacing: -.04em; }
h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
.objective { max-width: 760px; margin: 14px 0 0; color: var(--muted); font-size: 16px; line-height: 1.6; }
.connection { display: flex; align-items: center; gap: 8px; padding: 9px 13px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); white-space: nowrap; background: rgba(7, 16, 29, .65); }
.connection span { width: 8px; height: 8px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 14px currentColor; }
.connection.online span { background: var(--green); }.connection.offline span { background: var(--red); }
.panel { border: 1px solid var(--line); border-radius: 18px; background: var(--panel); box-shadow: 0 18px 60px rgba(0, 0, 0, .18); backdrop-filter: blur(14px); }
.overview { display: grid; grid-template-columns: 1.45fr 1fr; gap: 16px; }
.progress-card { padding: 24px; }.percent { color: var(--cyan); font-size: 34px; }
.track { width: 100%; height: 12px; margin: 27px 0 12px; overflow: hidden; border: 0; border-radius: 999px; background: #16263a; appearance: none; }
.track::-webkit-progress-bar { border-radius: 999px; background: #16263a; }
.track::-webkit-progress-value { border-radius: 999px; background: linear-gradient(90deg, var(--blue), var(--cyan)); transition: width .35s ease; }
.track::-moz-progress-bar { border-radius: 999px; background: linear-gradient(90deg, var(--blue), var(--cyan)); }
.muted { color: var(--muted); font-size: 13px; }
.count-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.count { min-height: 92px; padding: 17px; border: 1px solid var(--line); border-radius: 16px; background: rgba(15, 29, 48, .75); }
.count strong { display: block; margin-top: 7px; font-size: 28px; }.count span { color: var(--muted); font-size: 12px; }
.focus-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 16px; margin-top: 16px; }
.focus-grid .panel { min-height: 175px; padding: 22px; }
.work-title { margin: 12px 0 10px; font-size: 22px; }.work-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.pill { display: inline-flex; padding: 5px 9px; border: 1px solid var(--line); border-radius: 999px; color: #bdd0e6; font-size: 12px; }
.pill.state-Done { color: var(--green); }.pill.state-Blocked, .pill.state-Failed { color: var(--red); }
.pill.state-InProgress, .pill.state-Ready { color: var(--cyan); }.pill.state-NotRun { color: var(--amber); }
.next-action { margin: 18px 0 28px; font-size: 18px; line-height: 1.55; }
.diagnostics { margin-bottom: 16px; padding: 15px 18px; border: 1px solid rgba(255, 122, 135, .45); border-radius: 14px; background: rgba(128, 35, 48, .18); }
.diagnostics ul { margin: 8px 0 0; padding-left: 20px; color: #ffc0c7; }
.work-panel { margin-top: 16px; padding: 22px; }.work-heading { align-items: flex-end; }
.controls { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
input, select, button { min-height: 38px; border: 1px solid var(--line); border-radius: 9px; color: var(--text); background: #0d1b2d; font: inherit; }
input, select { padding: 0 11px; } input[type="search"] { width: min(260px, 42vw); }
button { padding: 0 14px; cursor: pointer; background: #163553; } button:hover { border-color: var(--blue); }
.auto-row { margin: 18px 0 10px; }.auto-row label { color: var(--muted); font-size: 13px; }.auto-row input { min-height: auto; }
.table-wrap { overflow-x: auto; } table { width: 100%; border-collapse: collapse; }
th, td { padding: 13px 10px; border-bottom: 1px solid rgba(38, 58, 85, .7); text-align: left; font-size: 13px; vertical-align: middle; }
th { color: var(--muted); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; }
td.title-cell { min-width: 230px; font-weight: 650; }.current-row { background: rgba(85, 214, 190, .055); }
.empty { padding: 35px 0; text-align: center; color: var(--muted); }
footer { padding: 24px 4px 0; color: #6f859f; font-size: 12px; text-align: center; }
@media (max-width: 800px) {
  .shell { width: min(100% - 20px, 1180px); padding-top: 28px; }
  .hero, .section-heading.work-heading { align-items: flex-start; flex-direction: column; }
  .overview, .focus-grid { grid-template-columns: 1fr; }.controls { justify-content: flex-start; }
  input[type="search"] { width: 100%; }.work-panel { padding: 16px; }
}
"""

DASHBOARD_JS = """const $ = (id) => document.getElementById(id);
let latest = null;
let timer = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function pill(text) { return element('span', `pill state-${String(text).replace(/[^A-Za-z]/g, '')}`, text); }

function setConnection(mode, text) {
  const box = $('connection');
  box.className = `connection ${mode}`;
  box.replaceChildren(element('span'), document.createTextNode(text));
}

function renderDiagnostics(items) {
  const box = $('diagnostics');
  const list = $('diagnostic-list');
  list.replaceChildren(...items.map((item) => element('li', '', item)));
  box.hidden = items.length === 0;
}

function renderCurrent(item) {
  const box = $('current-work');
  if (!item) {
    box.replaceChildren(element('p', 'muted', 'PLAN.md 尚未指定当前工作项。'));
    return;
  }
  const title = element('h3', 'work-title', `${item.id} · ${item.title}`);
  const meta = element('div', 'work-meta');
  [item.priority, item.type, item.delivery, item.verification].forEach((value) => meta.appendChild(pill(value)));
  if (item.dependencies.length) meta.appendChild(pill(`依赖 ${item.dependencies.join(', ')}`));
  box.replaceChildren(title, meta);
}

function renderCounts(data) {
  const cards = [
    ['待处理', data.summary.pending], ['进行中', data.counts.InProgress || 0],
    ['阻塞', data.counts.Blocked || 0], ['已完成', data.counts.Done || 0]
  ];
  $('count-grid').replaceChildren(...cards.map(([label, value]) => {
    const card = element('article', 'count');
    card.append(element('span', '', label), element('strong', '', value));
    return card;
  }));
}

function renderWorkItems() {
  if (!latest) return;
  const query = $('search').value.trim().toLowerCase();
  const status = $('status-filter').value;
  const visible = latest.work_items.filter((item) => {
    const haystack = `${item.id} ${item.title} ${item.type} ${item.priority}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!status || item.delivery === status);
  });
  const rows = visible.map((item) => {
    const row = element('tr', item.current ? 'current-row' : '');
    row.append(
      element('td', '', item.id), element('td', 'title-cell', item.title),
      element('td', '', item.priority), element('td', '', item.type),
      element('td', '', item.delivery), element('td', '', item.verification),
      element('td', '', item.dependencies.join(', ') || '—')
    );
    return row;
  });
  $('work-items').replaceChildren(...rows);
  $('empty-state').hidden = visible.length !== 0;
}

function render(data) {
  latest = data;
  document.title = `${data.project.name} · Plan Dashboard`;
  $('project-name').textContent = data.project.name;
  $('objective').textContent = data.project.objective || '尚未记录当前目标。';
  $('progress-percent').textContent = `${data.summary.percent}%`;
  $('progress-bar').value = data.summary.percent;
  $('progress-bar').textContent = `${data.summary.percent}%`;
  const progressScope = data.adoption && data.adoption.incomplete
    ? '；接入迁移尚未完成，这不是项目历史完成度'
    : '；只统计受管且有验证证据的工作';
  $('progress-detail').textContent = `${data.summary.verified_done} / ${data.summary.scope_total} 个范围内工作项已经完成并通过验证${progressScope}`;
  $('next-action').textContent = data.project.next_action || '尚未记录下一步操作。';
  $('plan-updated').textContent = data.project.updated ? `计划更新：${data.project.updated}` : '';
  $('refreshed-at').textContent = `页面刷新：${new Date(data.refreshed_at).toLocaleTimeString()}`;
  renderCounts(data); renderCurrent(data.current); renderDiagnostics(data.diagnostics); renderWorkItems();
  setConnection('online', '本地实时');
}

async function refresh() {
  clearTimeout(timer);
  $('refresh').disabled = true;
  try {
    const response = await fetch('/api/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
  } catch (error) {
    setConnection('offline', '已断开，正在重试');
    renderDiagnostics([`无法读取本地状态：${error.message}`]);
  } finally {
    $('refresh').disabled = false;
    if ($('auto-refresh').checked) timer = setTimeout(refresh, 2000);
  }
}

$('search').addEventListener('input', renderWorkItems);
$('status-filter').addEventListener('change', renderWorkItems);
$('refresh').addEventListener('click', refresh);
$('auto-refresh').addEventListener('change', () => {
  clearTimeout(timer);
  if ($('auto-refresh').checked) refresh();
});
refresh();
"""


class PlanCtlError(RuntimeError):
    """A user-facing CLI error."""


@dataclass
class CheckResult:
    errors: list[str]
    notices: list[str]
    warnings: list[str]
    strictness: str = "normal"

    @property
    def ok(self) -> bool:
        return not self.errors


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_new(path: Path, content: str, actions: list[str]) -> bool:
    if path.exists():
        actions.append(f"preserved {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")
    actions.append(f"created {path}")
    return True


def _append_block(path: Path, block: str, marker: str, actions: list[str]) -> bool:
    if not path.exists():
        return _write_new(path, block, actions)
    existing = _read(path)
    if marker in existing:
        actions.append(f"preserved managed block in {path}")
        return False
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n" + block.rstrip() + "\n")
    actions.append(f"appended managed block to {path}")
    return True


def _template(name: str) -> str:
    path = TEMPLATE_DIR / name
    if not path.is_file():
        raise PlanCtlError(
            f"Template {name!r} is unavailable. Run init/adopt from the installed Skill; "
            "the vendored .project-plan/planctl.py supports check only."
        )
    return _read(path)


def _render(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", result)))
    if unresolved:
        raise PlanCtlError(f"Unresolved template values: {', '.join(unresolved)}")
    return result


def _next_work_id(root: Path) -> str:
    numbers: list[int] = []
    for path in root.glob("docs/work/W-*.md"):
        match = re.match(r"W-(\d+)", path.name)
        if match:
            numbers.append(int(match.group(1)))
    plan = root / "PLAN.md"
    if plan.is_file():
        numbers.extend(int(item[2:]) for item in WORK_ID_RE.findall(_read(plan)))
    return f"W-{(max(numbers, default=0) + 1):03d}"


def _normalize_agents(raw: str) -> list[str]:
    agents = [item.strip().lower() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(agents) - {"codex", "claude"})
    if unknown:
        raise PlanCtlError(f"Unsupported agent adapter(s): {', '.join(unknown)}")
    if not agents:
        raise PlanCtlError("Select at least one agent: codex, claude")
    return list(dict.fromkeys(agents))


def _base_values(root: Path, work_id: str, adopt: bool) -> dict[str, str]:
    suffix = "adopt-project-plan" if adopt else "define-first-delivery"
    title = "Adopt the existing project plan" if adopt else "Define the first delivery slice"
    outcome = (
        "Reconcile existing planning documents into one linked, verifiable delivery queue."
        if adopt
        else "Define and verify the project's first bounded delivery slice."
    )
    return {
        "PROJECT_NAME": root.name,
        "DATE": date.today().isoformat(),
        "WORK_ID": work_id,
        "WORK_FILE": f"{work_id}-{suffix}.md",
        "WORK_TITLE": title,
        "WORK_OUTCOME": outcome,
    }


def _render_adoption_inventory(candidates: Sequence[str]) -> str:
    if candidates:
        checklist = "\n".join(
            f"- [ ] `{path.replace('`', '``')}`" for path in candidates
        )
    else:
        checklist = "No legacy planning-document candidates were detected during preview."
    return (
        "## Adoption inventory\n\n"
        "This is the document inventory reported before adoption files were installed. "
        "Review each candidate and map relevant delivery scope to managed work items; "
        "a checked item records mapping review, not historical verification.\n\n"
        f"{ADOPTION_CANDIDATES_START}\n"
        f"{checklist}\n"
        f"{ADOPTION_CANDIDATES_END}"
    )


def _persist_adoption_inventory(
    root: Path,
    candidates: Sequence[str],
    actions: list[str],
    *,
    document: Path | None = None,
) -> bool:
    if document is None:
        adoption_documents = sorted(
            (root / "docs" / "work").glob("W-*-adopt-project-plan.md")
        )
        if not adoption_documents:
            return False
        document = adoption_documents[0]
    return _append_block(
        document,
        _render_adoption_inventory(candidates),
        ADOPTION_CANDIDATES_START,
        actions,
    )


def _install_common(
    root: Path,
    agents: Sequence[str],
    *,
    adopt: bool,
    adoption_candidates: Sequence[str] = (),
    actions: list[str],
) -> None:
    config = _render(_template("plan-orchestrator.json"), {})
    _write_new(root / "plan-orchestrator.json", config, actions)
    _write_new(root / "docs" / "BUGS.md", _template("BUGS.md"), actions)
    _write_new(root / "docs" / "TEST_LOG.md", _template("TEST_LOG.md"), actions)
    _write_new(root / DECISIONS_PATH, _template("DECISIONS.md"), actions)

    plan_path = root / "PLAN.md"
    managed = plan_path.is_file() and PLAN_START in _read(plan_path)
    work_id: str | None = None
    adoption_document: Path | None = None
    if not managed:
        work_id = _next_work_id(root)
        values = _base_values(root, work_id, adopt)
        if plan_path.exists():
            if not adopt:
                raise PlanCtlError(
                    f"{plan_path} already exists without a managed work table; "
                    "use 'adopt --apply' instead of init."
                )
            block = _render(_template("PLAN_ADOPT_BLOCK.md"), values)
            _append_block(plan_path, block, PLAN_START, actions)
        else:
            plan = _render(_template("PLAN.md"), values)
            _write_new(plan_path, plan, actions)

        work_doc = _render(_template("work-item.md"), values)
        work_path = root / "docs" / "work" / values["WORK_FILE"]
        _write_new(work_path, work_doc, actions)
        if adopt:
            adoption_document = work_path
    else:
        actions.append(f"preserved managed plan in {plan_path}")
        (root / "docs" / "work").mkdir(parents=True, exist_ok=True)

    if adopt:
        _persist_adoption_inventory(
            root,
            adoption_candidates,
            actions,
            document=adoption_document,
        )

    if "codex" in agents:
        _append_block(
            root / "AGENTS.md",
            _template("AGENTS.fragment.md"),
            INSTRUCTION_START,
            actions,
        )
    if "claude" in agents:
        _append_block(
            root / "CLAUDE.md",
            _template("CLAUDE.fragment.md"),
            INSTRUCTION_START,
            actions,
        )

    validator = root / ".project-plan" / "planctl.py"
    _write_new(validator, _read(Path(__file__).resolve()), actions)
    if validator.exists() and os.name != "nt":
        validator.chmod(0o755)
    _write_new(
        root / ".github" / "workflows" / "project-plan.yml",
        _template("project-plan.yml"),
        actions,
    )


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / "PLAN.md"
    if plan_path.is_file() and PLAN_START not in _read(plan_path):
        raise PlanCtlError(
            f"{plan_path} already exists without a managed work table; "
            "use 'adopt --apply' instead of init."
        )
    agents = _normalize_agents(args.agents)
    actions: list[str] = []
    _install_common(root, agents, adopt=False, actions=actions)
    print(f"Initialized Project Plan Orchestrator in {root}")
    for action in actions:
        print(f"- {action}")
    return 0


def _adoption_inventory(root: Path) -> dict[str, list[str] | str | bool]:
    markdown: list[str] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        relative_parts = Path(relative).parts
        if len(relative_parts) > 1 and relative_parts[0].lower() not in {
            "doc",
            "docs",
            "documentation",
        }:
            continue
        if any(
            part
            in {
                ".git",
                ".project-plan",
                ".venv",
                "Library",
                "Logs",
                "Temp",
                "build",
                "dist",
                "node_modules",
                "vendor",
                "venv",
            }
            for part in relative_parts
        ):
            continue
        markdown.append(relative)
    keywords = ("plan", "status", "design", "bug", "test", "roadmap", "实施", "计划", "测试")
    managed_records = {"docs/bugs.md", "docs/test_log.md", DECISIONS_PATH.lower()}
    candidates = [
        path
        for path in markdown
        if any(key in path.lower() for key in keywords)
        and path.lower() not in managed_records
        and not re.fullmatch(r"docs/work/W-\d{3,}.*\.md", path, re.IGNORECASE)
    ]
    return {
        "root": str(root),
        "has_plan": (root / "PLAN.md").is_file(),
        "managed_plan": (root / "PLAN.md").is_file()
        and PLAN_START in _read(root / "PLAN.md"),
        "has_config": (root / "plan-orchestrator.json").is_file(),
        "document_candidates": sorted(candidates),
        "agent_files": sorted(
            name for name in ("AGENTS.md", "CLAUDE.md") if (root / name).is_file()
        ),
    }


def command_adopt(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise PlanCtlError(f"Project root does not exist: {root}")
    inventory = _adoption_inventory(root)
    print(json.dumps(inventory, indent=2, ensure_ascii=False))
    if not args.apply:
        print("Preview only; no files changed. Re-run with --apply to adopt.")
        return 0

    agents = _normalize_agents(args.agents)
    actions: list[str] = []
    _install_common(
        root,
        agents,
        adopt=True,
        adoption_candidates=inventory["document_candidates"],
        actions=actions,
    )
    print("Adoption changes:")
    for action in actions:
        print(f"- {action}")
    print("Next: map the reported document candidates to work items, then run check.")
    return 0


def _load_config(root: Path, errors: list[str]) -> dict:
    path = root / "plan-orchestrator.json"
    if not path.is_file():
        errors.append("missing plan-orchestrator.json")
        return {}
    try:
        config = json.loads(_read(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plan-orchestrator.json: {exc}")
        return {}
    if not isinstance(config, dict):
        errors.append("invalid plan-orchestrator.json: top-level value must be an object")
        return {}
    if config.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"unsupported schema_version {config.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}"
        )
    required = (
        "plan_path",
        "work_globs",
        "bug_log_path",
        "test_log_path",
        "delivery_globs",
        "exempt_globs",
    )
    for key in required:
        if key not in config:
            errors.append(f"configuration missing {key}")
    return config


def _strictness(config: dict, errors: list[str]) -> str:
    raw = config.get("strictness", "normal")
    if not isinstance(raw, str) or raw not in STRICTNESS_ORDER:
        expected = ", ".join(STRICTNESS_VALUES)
        errors.append(f"invalid strictness {raw!r}; expected one of: {expected}")
        return str(raw)
    return raw


def _at_least(strictness: str, level: str) -> bool:
    return STRICTNESS_ORDER.get(strictness, STRICTNESS_ORDER["normal"]) >= STRICTNESS_ORDER[level]


def _table_rows(
    text: str,
    start: str,
    end: str,
    expected_headers: Sequence[str],
    label: str,
    errors: list[str],
) -> list[dict[str, str]]:
    if start not in text or end not in text:
        errors.append(f"{label} is missing managed table markers")
        return []
    block = text.split(start, 1)[1].split(end, 1)[0]
    lines = [line.strip() for line in block.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        errors.append(f"{label} managed table is missing its header")
        return []

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    headers = cells(lines[0])
    if headers != list(expected_headers):
        errors.append(
            f"{label} headers must be {' | '.join(expected_headers)}; "
            f"found {' | '.join(headers)}"
        )
        return []
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(lines[2:], start=1):
        values = cells(line)
        if len(values) != len(headers):
            errors.append(f"{label} row {line_number} has {len(values)} columns")
            continue
        rows.append(dict(zip(headers, values)))
    return rows


def _extract_link(cell: str) -> str | None:
    match = LINK_RE.search(cell)
    if not match:
        return None
    target = match.group(1).strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(" ", 1)[0]
    return target


def _local_target(document: Path, target: str, root: Path) -> Path | None:
    parsed = urlparse(target)
    if parsed.scheme or target.startswith("//"):
        return None
    clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not clean:
        return None
    if clean.startswith("/"):
        return root / clean.lstrip("/")
    return document.parent / clean


def _validate_links(documents: Iterable[Path], root: Path, errors: list[str]) -> None:
    for document in documents:
        if not document.is_file():
            continue
        for target in LINK_RE.findall(_read(document)):
            target = target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1 : target.index(">")]
            elif " " in target:
                target = target.split(" ", 1)[0]
            local = _local_target(document, target, root)
            if local is not None and not local.resolve().exists():
                relative = document.relative_to(root).as_posix()
                errors.append(f"broken local link in {relative}: {target}")


def _parse_tests(path: Path, errors: list[str]) -> dict[str, str]:
    if not path.is_file():
        errors.append(f"missing {path}")
        return {}
    text = _read(path)
    if TEST_START not in text or TEST_END not in text:
        errors.append(f"{path} is missing managed test markers")
    matches = list(re.finditer(r"^## (TR-\d{8}-\d{3,})\s*$", text, re.MULTILINE))
    tests: dict[str, str] = {}
    for index, match in enumerate(matches):
        test_id = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.end() : end]
        result_match = re.search(r"^- Result:\s*(.+?)\s*$", section, re.MULTILINE)
        if test_id in tests:
            errors.append(f"duplicate test ID {test_id}")
            continue
        if not result_match:
            errors.append(f"{test_id} is missing '- Result:'")
            continue
        result = result_match.group(1).strip()
        tests[test_id] = result
        if result not in TEST_RESULTS:
            errors.append(f"{test_id} has invalid result {result}")
        if result in {"NotRun", "N/A"}:
            reason = re.search(r"^- (?:Reason|Evidence):\s*(.+?)\s*$", section, re.MULTILINE)
            if not reason or reason.group(1).strip() in {"", "—", "-"}:
                errors.append(f"{test_id} result {result} requires a concrete reason")
    return tests


def _work_documents(root: Path, config: dict) -> list[Path]:
    found: set[Path] = set()
    for pattern in config.get("work_globs", []):
        found.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(found)


def _work_ids_from_documents(
    documents: Sequence[Path], root: Path, errors: list[str]
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in documents:
        match = re.search(r"^- Work ID:\s*(W-\d{3,})\s*$", _read(path), re.MULTILINE)
        if not match:
            errors.append(f"{path.relative_to(root).as_posix()} is missing a valid Work ID")
            continue
        work_id = match.group(1)
        if work_id in result:
            errors.append(f"duplicate work document ID {work_id}")
        else:
            result[work_id] = path
    return result


def _unchecked_acceptance(path: Path) -> bool:
    text = _read(path)
    match = re.search(
        r"^## Acceptance\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE
    )
    return bool(match and re.search(r"^- \[ \]", match.group(1), re.MULTILINE))


def _has_block_reason(path: Path) -> bool:
    text = _read(path)
    match = re.search(r"(?im)^\s*(?:- )?Block reason:\s*(.+?)\s*$", text)
    return bool(match and match.group(1).strip() not in {"", "—", "-", "None", "TBD"})


def _parse_plan(
    root: Path,
    config: dict,
    tests: dict[str, str],
    strictness: str,
    errors: list[str],
    warnings: list[str],
) -> tuple[list[dict[str, str]], str | None, list[Path]]:
    plan_path = root / config.get("plan_path", "PLAN.md")
    if not plan_path.is_file():
        errors.append(f"missing {plan_path}")
        return [], None, []
    text = _read(plan_path)
    rows = _table_rows(
        text,
        PLAN_START,
        PLAN_END,
        (
            "ID",
            "Priority",
            "Type",
            "Delivery",
            "Verification",
            "Dependencies",
            "Detail",
            "Tests",
            "Bugs",
        ),
        "PLAN.md",
        errors,
    )
    current_match = re.search(r"^- Current work unit:\s*(W-\d{3,})\s*$", text, re.MULTILINE)
    current = current_match.group(1) if current_match else None
    if not current:
        errors.append("PLAN.md is missing a valid Current work unit")

    require_work_docs = _at_least(strictness, "normal")
    documents = _work_documents(root, config) if require_work_docs else []
    document_ids = _work_ids_from_documents(documents, root, errors) if require_work_docs else {}
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        work_id = row["ID"]
        if not re.fullmatch(r"W-\d{3,}", work_id):
            errors.append(f"invalid work ID {work_id}")
            continue
        if work_id in by_id:
            errors.append(f"duplicate PLAN work ID {work_id}")
        by_id[work_id] = row
        if row["Priority"] not in PRIORITIES:
            errors.append(f"{work_id} has invalid priority {row['Priority']}")
        if row["Type"] not in WORK_TYPES:
            errors.append(f"{work_id} has invalid type {row['Type']}")
        if row["Delivery"] not in DELIVERY_STATES:
            errors.append(f"{work_id} has invalid delivery state {row['Delivery']}")
        if row["Verification"] not in VERIFICATION_STATES:
            errors.append(f"{work_id} has invalid verification state {row['Verification']}")

        detail_target = _extract_link(row["Detail"])
        detail_path: Path | None = None
        if require_work_docs:
            if not detail_target:
                errors.append(f"{work_id} is missing a detail link")
            else:
                detail_path = _local_target(plan_path, detail_target, root)
                if detail_path is None or not detail_path.resolve().is_file():
                    errors.append(f"{work_id} detail link does not resolve: {detail_target}")
                else:
                    detail_path = detail_path.resolve()
                    if document_ids.get(work_id, Path()).resolve() != detail_path:
                        errors.append(f"{work_id} detail document does not declare the same Work ID")
        elif detail_target:
            detail_path = _local_target(plan_path, detail_target, root)
            if detail_path is not None and detail_path.resolve().is_file():
                detail_path = detail_path.resolve()

        if row["Delivery"] == "Done":
            test_ids = TEST_ID_RE.findall(row["Tests"])
            if not _at_least(strictness, "normal"):
                if row["Verification"] not in {"Passed", "N/A"} or not test_ids:
                    warnings.append(f"{work_id} Done work has incomplete verification evidence")
            else:
                if row["Verification"] not in {"Passed", "N/A"}:
                    errors.append(f"{work_id} cannot be Done with {row['Verification']} verification")
                if not test_ids:
                    errors.append(f"{work_id} Done work requires a linked test record")
                else:
                    result = tests.get(test_ids[0])
                    if result != row["Verification"]:
                        errors.append(
                            f"{work_id} verification {row['Verification']} does not match "
                            f"{test_ids[0]} result {result or 'missing'}"
                        )
                if detail_path and _unchecked_acceptance(detail_path):
                    errors.append(f"{work_id} is Done with unchecked acceptance items")

        if (
            _at_least(strictness, "strict")
            and row["Delivery"] == "Blocked"
            and row["Priority"] in {"P0", "P1"}
            and detail_path
            and not _has_block_reason(detail_path)
        ):
            errors.append(f"{work_id} P0/P1 blocked work requires a block reason")

    for row in rows:
        work_id = row["ID"]
        raw_dependencies = row["Dependencies"].strip()
        dependencies = [] if raw_dependencies in {"", "—", "-", "None"} else WORK_ID_RE.findall(raw_dependencies)
        if raw_dependencies not in {"", "—", "-", "None"} and not dependencies:
            errors.append(f"{work_id} has invalid dependencies: {raw_dependencies}")
        for dependency in dependencies:
            if dependency == work_id:
                errors.append(f"{work_id} depends on itself")
            elif dependency not in by_id:
                errors.append(f"{work_id} depends on unknown work item {dependency}")
            elif (
                row["Delivery"] in {"Ready", "InProgress", "Implemented", "Done"}
                and by_id[dependency]["Delivery"] != "Done"
            ):
                errors.append(f"{work_id} is active before dependency {dependency} is Done")

    if current and current not in by_id:
        errors.append(f"Current work unit {current} is not in the priority queue")
    return rows, current, documents


def _parse_bugs(
    root: Path,
    config: dict,
    plan_ids: set[str],
    tests: dict[str, str],
    errors: list[str],
) -> Path:
    path = root / config.get("bug_log_path", "docs/BUGS.md")
    if not path.is_file():
        errors.append(f"missing {path}")
        return path
    rows = _table_rows(
        _read(path),
        BUG_START,
        BUG_END,
        ("ID", "Severity", "Status", "Work", "Summary", "Fix", "Verification"),
        "BUGS.md",
        errors,
    )
    seen: set[str] = set()
    for row in rows:
        bug_id = row["ID"]
        if not re.fullmatch(r"BUG-\d{3,}", bug_id):
            errors.append(f"invalid bug ID {bug_id}")
        elif bug_id in seen:
            errors.append(f"duplicate bug ID {bug_id}")
        seen.add(bug_id)
        if row["Status"] not in BUG_STATES:
            errors.append(f"{bug_id} has invalid status {row['Status']}")
        work_ids = WORK_ID_RE.findall(row["Work"])
        for work_id in work_ids:
            if work_id not in plan_ids:
                errors.append(f"{bug_id} links unknown work item {work_id}")
        if row["Status"] in VERIFIED_BUG_STATES:
            test_ids = TEST_ID_RE.findall(row["Verification"])
            if not test_ids or tests.get(test_ids[0]) != "Passed":
                errors.append(
                    f"{bug_id} cannot be {row['Status']} without a Passed test record"
                )
    return path


def _git(
    root: Path, args: Sequence[str], *, text: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=text,
        check=False,
    )


def _valid_ref(root: Path, ref: str) -> bool:
    if re.fullmatch(r"0{40}", ref):
        return False
    return _git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"]).returncode == 0


def _git_changed_paths(
    root: Path, base: str | None, head: str | None, errors: list[str], notices: list[str]
) -> list[str]:
    if _git(root, ["rev-parse", "--is-inside-work-tree"]).returncode != 0:
        notices.append("Git repository not found; skipped change-sync checks")
        return []
    prefix_result = _git(root, ["rev-parse", "--show-prefix"])
    prefix = prefix_result.stdout.strip().replace("\\", "/")

    if base:
        if not _valid_ref(root, base):
            if re.fullmatch(r"0{40}", base):
                notices.append("Initial Git push detected; skipped diff-based sync checks")
                return []
            errors.append(f"invalid Git base ref: {base}")
            return []
        if head and not _valid_ref(root, head):
            errors.append(f"invalid Git head ref: {head}")
            return []
        command = ["diff", "--name-only", "--relative", base]
        if head:
            command.append(head)
        command.extend(["--", "."])
        result = _git(root, command)
        if result.returncode != 0:
            errors.append(f"git diff failed: {result.stderr.strip()}")
            return []
        return sorted(
            {
                _strip_prefix(line.strip().replace("\\", "/"), prefix)
                for line in result.stdout.splitlines()
                if line.strip()
            }
        )

    result = _git(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "."],
        text=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        errors.append(f"git status failed: {stderr}")
        return []
    tokens = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        if len(token) < 4:
            continue
        status = token[:2]
        path = token[3:].replace("\\", "/")
        paths.append(_strip_prefix(path, prefix))
        if "R" in status or "C" in status:
            index += 1
    return sorted(set(paths))


def _strip_prefix(path: str, prefix: str) -> str:
    normalized = path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    if prefix and normalized.startswith(prefix):
        return normalized[len(prefix) :]
    return normalized


def _matches(path: str, patterns: Sequence[str]) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    for pattern in patterns:
        candidate = pattern.replace("\\", "/")
        while candidate.startswith("./"):
            candidate = candidate[2:]
        candidate = candidate.lstrip("/")
        if fnmatch.fnmatchcase(normalized, candidate):
            return True
        if candidate.startswith("**/") and fnmatch.fnmatchcase(normalized, candidate[3:]):
            return True
    return False


def _sync_checks(
    changed: Sequence[str],
    config: dict,
    rows: Sequence[dict[str, str]],
    current: str | None,
    errors: list[str],
    notices: list[str],
) -> None:
    if not changed:
        notices.append("No changed files detected; structural checks only")
        return
    delivery = [
        path
        for path in changed
        if _matches(path, config.get("delivery_globs", []))
        and not _matches(path, config.get("exempt_globs", []))
    ]
    if not delivery:
        notices.append("No changed delivery files detected")
        return

    plan_path = config.get("plan_path", "PLAN.md")
    test_path = config.get("test_log_path", "docs/TEST_LOG.md")
    if plan_path not in changed:
        errors.append(f"delivery changes require synchronized {plan_path}")
    if test_path not in changed:
        errors.append(f"delivery changes require synchronized {test_path}")
    if not any(_matches(path, config.get("work_globs", [])) for path in changed):
        errors.append("delivery changes require at least one synchronized work document")

    current_row = next((row for row in rows if row["ID"] == current), None)
    if (
        current_row
        and current_row["Type"] == "bug"
        and config.get("bug_log_path", "docs/BUGS.md") not in changed
    ):
        errors.append("bug delivery work requires a synchronized bug registry")
    notices.append("Delivery files: " + ", ".join(delivery))


def _check_decisions(root: Path, strictness: str, errors: list[str], warnings: list[str]) -> Path:
    path = root / DECISIONS_PATH
    if path.is_file() or not _at_least(strictness, "normal"):
        return path
    message = f"missing {DECISIONS_PATH}"
    if _at_least(strictness, "strict"):
        errors.append(message)
    else:
        warnings.append(message)
    return path


def _dashboard_plain_text(value: str) -> str:
    value = re.sub(r"!?\[([^\]]+)]\([^)]+\)", r"\1", value)
    value = value.replace("`", "").replace("**", "").replace("__", "")
    return " ".join(value.split())


def _dashboard_field(text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return _dashboard_plain_text(match.group(1)) if match else ""


def _dashboard_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^#{{2,6}}\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^#{{1,6}}\s|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return ""
    lines = [
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith("<!--")
    ]
    return _dashboard_plain_text(" ".join(lines))


def _dashboard_next_action(text: str) -> str:
    return _dashboard_section(text, "Orchestrator next action") or _dashboard_section(
        text, "Next action"
    )


def _dashboard_project_name(root: Path, config: dict, plan_text: str) -> str:
    configured = config.get("project_name")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    heading = re.search(r"^#\s+(.+?)\s*$", plan_text, re.MULTILINE)
    if heading:
        title = heading.group(1).strip()
        if title.lower().endswith(" project plan"):
            title = title[: -len(" Project Plan")].rstrip()
        if title:
            return title
    return root.name


def _dashboard_work_title(detail: str, work_id: str) -> str:
    match = re.search(r"\[([^\]]+)]\([^)]+\)", detail)
    if match:
        return _dashboard_plain_text(match.group(1))
    plain = _dashboard_plain_text(detail)
    return plain if plain not in {"", "—", "-"} else work_id


def _parse_adoption_candidates(text: str) -> tuple[list[dict[str, object]], bool]:
    if ADOPTION_CANDIDATES_START not in text or ADOPTION_CANDIDATES_END not in text:
        return [], False
    block = text.split(ADOPTION_CANDIDATES_START, 1)[1].split(
        ADOPTION_CANDIDATES_END, 1
    )[0]
    candidates: list[dict[str, object]] = []
    for line in block.splitlines():
        match = re.match(r"^- \[([ xX])\]\s+`(.+)`\s*$", line.strip())
        if match:
            candidates.append(
                {
                    "path": match.group(2).replace("``", "`"),
                    "reviewed": match.group(1).lower() == "x",
                }
            )
    return candidates, True


def _adoption_status(
    root: Path,
    plan_path: Path,
    rows: Sequence[dict[str, str]],
) -> dict[str, object]:
    status: dict[str, object] = {
        "incomplete": False,
        "work_id": None,
        "inventory_persisted": False,
        "candidate_count": 0,
        "pending_candidate_count": 0,
        "candidates": [],
        "managed_work_count": len(rows),
    }
    for row in rows:
        detail_target = _extract_link(row["Detail"])
        detail_name = Path(urlparse(detail_target or "").path).name
        title = _dashboard_work_title(row["Detail"], row["ID"])
        if (
            title.casefold() != "Adopt the existing project plan".casefold()
            and not detail_name.endswith("-adopt-project-plan.md")
        ):
            continue

        candidates: list[dict[str, object]] = []
        inventory_persisted = False
        if detail_target:
            document = _local_target(plan_path, detail_target, root)
            if document is not None:
                resolved = document.resolve()
                if resolved.is_relative_to(root) and resolved.is_file():
                    try:
                        candidates, inventory_persisted = _parse_adoption_candidates(
                            _read(resolved)
                        )
                    except (OSError, UnicodeError):
                        pass

        status.update(
            {
                "incomplete": not (
                    row["Delivery"] == "Done"
                    and row["Verification"] in {"Passed", "N/A"}
                ),
                "work_id": row["ID"],
                "inventory_persisted": inventory_persisted,
                "candidate_count": len(candidates),
                "pending_candidate_count": sum(
                    not bool(candidate["reviewed"]) for candidate in candidates
                ),
                "candidates": candidates,
            }
        )
        break
    return status


def _adoption_incomplete_message(status: dict[str, object]) -> str:
    if status["inventory_persisted"]:
        inventory = (
            f"{status['candidate_count']} legacy planning-document candidate(s) "
            f"were detected, and {status['managed_work_count']} work item(s) are managed."
        )
    else:
        inventory = (
            "The legacy document inventory is not persisted; re-run "
            "adopt --apply to backfill the adoption work document."
        )
    return (
        f"Project adoption is incomplete ({status['work_id']}). {inventory} "
        "Dashboard progress represents managed work with verification evidence, "
        "not historical project progress."
    )


def build_dashboard_snapshot(root: Path) -> dict:
    """Build a read-only, JSON-serializable view of the managed project plan."""
    root = root.expanduser().resolve()
    diagnostics: list[str] = []
    config = _load_config(root, diagnostics)
    configured_plan_path = config.get("plan_path", "PLAN.md")
    if not isinstance(configured_plan_path, str) or not configured_plan_path.strip():
        diagnostics.append("configuration plan_path must be a non-empty string")
        configured_plan_path = "PLAN.md"
    plan_path = root / configured_plan_path
    plan_text = ""
    rows: list[dict[str, str]] = []

    if plan_path.is_file():
        try:
            plan_text = _read(plan_path)
            rows = _table_rows(
                plan_text,
                PLAN_START,
                PLAN_END,
                (
                    "ID",
                    "Priority",
                    "Type",
                    "Delivery",
                    "Verification",
                    "Dependencies",
                    "Detail",
                    "Tests",
                    "Bugs",
                ),
                "PLAN.md",
                diagnostics,
            )
        except (OSError, UnicodeError) as exc:
            diagnostics.append(f"cannot read {plan_path.name}: {exc}")
    else:
        diagnostics.append(f"missing {plan_path.name}")

    current_id = _dashboard_field(plan_text, "Current work unit")
    counts = {state: 0 for state in sorted(DELIVERY_STATES)}
    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        work_id = row["ID"]
        delivery = row["Delivery"]
        verification = row["Verification"]
        if not re.fullmatch(r"W-\d{3,}", work_id):
            diagnostics.append(f"invalid work ID {work_id}")
        elif work_id in seen:
            diagnostics.append(f"duplicate work ID {work_id}")
        seen.add(work_id)
        if row["Priority"] not in PRIORITIES:
            diagnostics.append(f"{work_id} has invalid priority {row['Priority']}")
        if row["Type"] not in WORK_TYPES:
            diagnostics.append(f"{work_id} has invalid type {row['Type']}")
        if delivery not in DELIVERY_STATES:
            diagnostics.append(f"{work_id} has invalid delivery state {delivery}")
        else:
            counts[delivery] += 1
        if verification not in VERIFICATION_STATES:
            diagnostics.append(f"{work_id} has invalid verification state {verification}")

        raw_dependencies = row["Dependencies"].strip()
        dependencies = (
            []
            if raw_dependencies in {"", "—", "-", "None"}
            else WORK_ID_RE.findall(raw_dependencies)
        )
        items.append(
            {
                "id": work_id,
                "title": _dashboard_work_title(row["Detail"], work_id),
                "priority": row["Priority"],
                "type": row["Type"],
                "delivery": delivery,
                "verification": verification,
                "dependencies": dependencies,
                "tests": TEST_ID_RE.findall(row["Tests"]),
                "bugs": BUG_ID_RE.findall(row["Bugs"]),
                "current": work_id == current_id,
            }
        )

    current = next((item for item in items if item["current"]), None)
    if not current_id:
        diagnostics.append("PLAN.md is missing a valid Current work unit")
    elif current is None:
        diagnostics.append(f"Current work unit {current_id} is not in the priority queue")

    scope_items = [item for item in items if item["delivery"] != "Cancelled"]
    verified_done = sum(
        item["delivery"] == "Done" and item["verification"] in {"Passed", "N/A"}
        for item in scope_items
    )
    pending = sum(
        item["delivery"] not in {"Done", "Cancelled"}
        for item in items
    )
    scope_total = len(scope_items)
    percent = round(verified_done * 100 / scope_total) if scope_total else 0
    adoption = _adoption_status(root, plan_path, rows)
    if adoption["incomplete"]:
        diagnostics.append(_adoption_incomplete_message(adoption))

    return {
        "api_version": 1,
        "project": {
            "name": _dashboard_project_name(root, config, plan_text),
            "objective": _dashboard_field(plan_text, "Current objective"),
            "updated": _dashboard_field(plan_text, "Updated"),
            "current_work_unit": current_id or None,
            "next_action": _dashboard_next_action(plan_text),
        },
        "summary": {
            "scope_total": scope_total,
            "verified_done": verified_done,
            "pending": pending,
            "percent": percent,
        },
        "counts": counts,
        "current": current,
        "work_items": items,
        "adoption": adoption,
        "diagnostics": list(dict.fromkeys(diagnostics)),
        "refreshed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def _dashboard_host_allowed(value: str | None) -> bool:
    if not value:
        return True
    host = value.strip().lower()
    if host.startswith("[") and "]" in host:
        host = host[1 : host.index("]")]
    elif host.count(":") == 1:
        host = host.rsplit(":", 1)[0]
    return host in {"127.0.0.1", "localhost", "::1"}


def _dashboard_handler(root: Path) -> type[BaseHTTPRequestHandler]:
    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = "ProjectPlanDashboard/1"

        def _send(
            self,
            status: int,
            content_type: str,
            body: bytes,
            *,
            include_body: bool = True,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self'; frame-ancestors 'none'",
            )
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def _route(self, *, include_body: bool) -> None:
            if not _dashboard_host_allowed(self.headers.get("Host")):
                self._send(
                    421,
                    "text/plain; charset=utf-8",
                    b"Local dashboard host rejected.\n",
                    include_body=include_body,
                )
                return
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                body = DASHBOARD_HTML.encode("utf-8")
                self._send(200, "text/html; charset=utf-8", body, include_body=include_body)
            elif path == "/app.css":
                body = DASHBOARD_CSS.encode("utf-8")
                self._send(200, "text/css; charset=utf-8", body, include_body=include_body)
            elif path == "/app.js":
                body = DASHBOARD_JS.encode("utf-8")
                self._send(
                    200,
                    "text/javascript; charset=utf-8",
                    body,
                    include_body=include_body,
                )
            elif path == "/api/status":
                body = json.dumps(
                    build_dashboard_snapshot(root), ensure_ascii=False
                ).encode("utf-8")
                self._send(
                    200,
                    "application/json; charset=utf-8",
                    body,
                    include_body=include_body,
                )
            else:
                self._send(
                    404,
                    "text/plain; charset=utf-8",
                    b"Not found.\n",
                    include_body=include_body,
                )

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._route(include_body=True)

        def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._route(include_body=False)

        def _reject_write(self) -> None:
            self._send(
                405,
                "text/plain; charset=utf-8",
                b"The local dashboard is read-only.\n",
            )

        do_POST = _reject_write
        do_PUT = _reject_write
        do_PATCH = _reject_write
        do_DELETE = _reject_write

        def log_message(self, format: str, *args: object) -> None:
            return

    return DashboardHandler


class LocalDashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def create_dashboard_server(root: Path, port: int = 8765) -> LocalDashboardServer:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise PlanCtlError(f"Project root does not exist: {root}")
    if not 0 <= port <= 65535:
        raise PlanCtlError("Dashboard port must be between 0 and 65535")
    try:
        return LocalDashboardServer(
            ("127.0.0.1", port),
            _dashboard_handler(root),
        )
    except OSError as exc:
        raise PlanCtlError(
            f"Could not start the local dashboard on 127.0.0.1:{port}: {exc}. "
            "Choose another port with --port."
        ) from exc


def command_serve(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    server = create_dashboard_server(root, args.port)
    actual_port = int(server.server_address[1])
    url = f"http://127.0.0.1:{actual_port}/"
    print(f"Project Plan Dashboard: {url}", flush=True)
    print("Read-only and loopback-only. Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        try:
            opened = webbrowser.open(url)
            if not opened:
                print("Browser did not open automatically; use the URL above.", flush=True)
        except Exception as exc:  # pragma: no cover - platform browser integrations vary
            print(f"Browser did not open automatically: {exc}", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


def run_check(root: Path, base: str | None = None, head: str | None = None) -> CheckResult:
    errors: list[str] = []
    notices: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        return CheckResult([f"project root does not exist: {root}"], notices, warnings)
    config = _load_config(root, errors)
    if not config:
        return CheckResult(errors, notices, warnings)
    strictness = _strictness(config, errors)

    test_path = root / config.get("test_log_path", "docs/TEST_LOG.md")
    tests = _parse_tests(test_path, errors) if _at_least(strictness, "normal") else {}
    rows, current, work_documents = _parse_plan(
        root, config, tests, strictness, errors, warnings
    )
    plan_ids = {row["ID"] for row in rows if re.fullmatch(r"W-\d{3,}", row["ID"])}
    bug_path = (
        _parse_bugs(root, config, plan_ids, tests, errors)
        if _at_least(strictness, "strict")
        else root / config.get("bug_log_path", "docs/BUGS.md")
    )
    decisions_path = _check_decisions(root, strictness, errors, warnings)
    plan_path = root / config.get("plan_path", "PLAN.md")
    adoption = _adoption_status(root, plan_path, rows)
    if adoption["incomplete"]:
        warnings.append(_adoption_incomplete_message(adoption))
    if _at_least(strictness, "normal"):
        _validate_links(
            [plan_path, test_path, bug_path, decisions_path, *work_documents],
            root,
            errors,
        )

    if _at_least(strictness, "strict"):
        changed = _git_changed_paths(root, base, head, errors, notices)
        _sync_checks(changed, config, rows, current, errors, notices)
    else:
        notices.append("Change-sync checks require strict mode; skipped")
    return CheckResult(errors, notices, warnings, strictness)


def command_check(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    result = run_check(root, args.base, args.head)
    print("Project Plan Check")
    print(f"Strictness: {result.strictness}")
    for notice in result.notices:
        print(f"NOTICE: {notice}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.ok:
        print(f"OK: project plan is valid in {root}")
        return 0
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"FAILED: {len(result.errors)} error(s)", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize, adopt, validate, and visualize plan-driven project records."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a new project")
    init_parser.add_argument("--root", required=True, help="project root")
    init_parser.add_argument(
        "--agents", default="codex,claude", help="comma-separated: codex,claude"
    )
    init_parser.set_defaults(handler=command_init)

    adopt_parser = subparsers.add_parser("adopt", help="preview or apply safe adoption")
    adopt_parser.add_argument("--root", required=True, help="existing project root")
    adopt_parser.add_argument(
        "--apply", action="store_true", help="create and append managed records"
    )
    adopt_parser.add_argument(
        "--agents", default="codex,claude", help="comma-separated: codex,claude"
    )
    adopt_parser.set_defaults(handler=command_adopt)

    check_parser = subparsers.add_parser("check", help="validate records and Git sync")
    check_parser.add_argument("--root", required=True, help="project root")
    check_parser.add_argument("--base", help="Git base ref")
    check_parser.add_argument("--head", help="Git head ref")
    check_parser.set_defaults(handler=command_check)

    serve_parser = subparsers.add_parser(
        "serve", help="run the read-only local project dashboard"
    )
    serve_parser.add_argument("--root", required=True, help="project root")
    serve_parser.add_argument(
        "--port", type=int, default=8765, help="loopback port (default: 8765)"
    )
    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not open the dashboard in the default browser",
    )
    serve_parser.set_defaults(handler=command_serve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "head", None) and not getattr(args, "base", None):
        parser.error("--head requires --base")
    try:
        return int(args.handler(args))
    except PlanCtlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
