#!/usr/bin/env python3
"""Initialize, adopt, and validate Project Plan Orchestrator repositories."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
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
BUG_STATES = {"Open", "Diagnosed", "FixedUnverified", "Closed", "Deferred"}
TEST_RESULTS = {"Passed", "Failed", "Blocked", "NotRun", "N/A"}

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"


class PlanCtlError(RuntimeError):
    """A user-facing CLI error."""


@dataclass
class CheckResult:
    errors: list[str]
    notices: list[str]

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


def _install_common(
    root: Path,
    agents: Sequence[str],
    *,
    adopt: bool,
    actions: list[str],
) -> None:
    config = _render(_template("plan-orchestrator.json"), {})
    _write_new(root / "plan-orchestrator.json", config, actions)
    _write_new(root / "docs" / "BUGS.md", _template("BUGS.md"), actions)
    _write_new(root / "docs" / "TEST_LOG.md", _template("TEST_LOG.md"), actions)

    plan_path = root / "PLAN.md"
    managed = plan_path.is_file() and PLAN_START in _read(plan_path)
    work_id: str | None = None
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
        _write_new(root / "docs" / "work" / values["WORK_FILE"], work_doc, actions)
    else:
        actions.append(f"preserved managed plan in {plan_path}")
        (root / "docs" / "work").mkdir(parents=True, exist_ok=True)

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
    candidates = [path for path in markdown if any(key in path.lower() for key in keywords)]
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
    _install_common(root, agents, adopt=True, actions=actions)
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
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plan-orchestrator.json: {exc}")
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


def _parse_plan(
    root: Path,
    config: dict,
    tests: dict[str, str],
    errors: list[str],
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

    documents = _work_documents(root, config)
    document_ids = _work_ids_from_documents(documents, root, errors)
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

        if row["Delivery"] == "Done":
            if row["Verification"] not in {"Passed", "N/A"}:
                errors.append(f"{work_id} cannot be Done with {row['Verification']} verification")
            test_ids = TEST_ID_RE.findall(row["Tests"])
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
        if row["Status"] == "Closed":
            test_ids = TEST_ID_RE.findall(row["Verification"])
            if not test_ids or tests.get(test_ids[0]) != "Passed":
                errors.append(f"{bug_id} cannot be Closed without a Passed test record")
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


def run_check(root: Path, base: str | None = None, head: str | None = None) -> CheckResult:
    errors: list[str] = []
    notices: list[str] = []
    if not root.is_dir():
        return CheckResult([f"project root does not exist: {root}"], notices)
    config = _load_config(root, errors)
    if not config:
        return CheckResult(errors, notices)

    test_path = root / config.get("test_log_path", "docs/TEST_LOG.md")
    tests = _parse_tests(test_path, errors)
    rows, current, work_documents = _parse_plan(root, config, tests, errors)
    plan_ids = {row["ID"] for row in rows if re.fullmatch(r"W-\d{3,}", row["ID"])}
    bug_path = _parse_bugs(root, config, plan_ids, tests, errors)
    plan_path = root / config.get("plan_path", "PLAN.md")
    _validate_links([plan_path, test_path, bug_path, *work_documents], root, errors)

    changed = _git_changed_paths(root, base, head, errors, notices)
    _sync_checks(changed, config, rows, current, errors, notices)
    return CheckResult(errors, notices)


def command_check(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    result = run_check(root, args.base, args.head)
    for notice in result.notices:
        print(f"NOTICE: {notice}")
    if result.ok:
        print(f"OK: project plan is valid in {root}")
        return 0
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"FAILED: {len(result.errors)} error(s)", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize, adopt, and validate plan-driven project records."
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
