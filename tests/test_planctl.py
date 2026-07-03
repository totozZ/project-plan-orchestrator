from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "project-plan-orchestrator"
    / "scripts"
    / "planctl.py"
)
SPEC = importlib.util.spec_from_file_location("project_planctl", SCRIPT)
assert SPEC and SPEC.loader
planctl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = planctl
SPEC.loader.exec_module(planctl)


class PlanCtlTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = planctl.main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def init_project(self) -> None:
        code, _, error = self.invoke(
            "init", "--root", str(self.root), "--agents", "codex,claude"
        )
        self.assertEqual(0, code, error)

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def initialize_git_baseline(self) -> None:
        self.assertEqual(0, self.git("init").returncode)
        self.assertEqual(
            0, self.git("config", "user.email", "tests@example.invalid").returncode
        )
        self.assertEqual(0, self.git("config", "user.name", "Plan Tests").returncode)
        self.assertEqual(0, self.git("add", ".").returncode)
        commit = self.git("commit", "-m", "baseline")
        self.assertEqual(0, commit.returncode, commit.stderr)


class InitializationTests(PlanCtlTestCase):
    def test_init_creates_complete_idempotent_project(self) -> None:
        self.init_project()

        expected = [
            "PLAN.md",
            "docs/work/W-001-define-first-delivery.md",
            "docs/BUGS.md",
            "docs/TEST_LOG.md",
            "plan-orchestrator.json",
            "AGENTS.md",
            "CLAUDE.md",
            ".project-plan/planctl.py",
            ".github/workflows/project-plan.yml",
        ]
        for relative in expected:
            self.assertTrue((self.root / relative).exists(), relative)

        original_plan = (self.root / "PLAN.md").read_text(encoding="utf-8")
        code, _, error = self.invoke(
            "init", "--root", str(self.root), "--agents", "codex,claude"
        )
        self.assertEqual(0, code, error)
        self.assertEqual(
            original_plan, (self.root / "PLAN.md").read_text(encoding="utf-8")
        )
        self.assertTrue(planctl.run_check(self.root).ok)

    def test_init_refuses_unmanaged_existing_plan_without_partial_writes(self) -> None:
        (self.root / "PLAN.md").write_text("# Existing\n", encoding="utf-8")

        code, _, error = self.invoke("init", "--root", str(self.root))

        self.assertEqual(2, code)
        self.assertIn("use 'adopt --apply'", error)
        self.assertEqual(
            {"PLAN.md"}, {path.name for path in self.root.iterdir() if path.is_file()}
        )

    def test_adopt_preview_is_read_only_and_apply_preserves_content(self) -> None:
        original = "# Existing project plan\n\nKeep this content.\n"
        (self.root / "PLAN.md").write_text(original, encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "FEATURE_DESIGN.md").write_text(
            "# Feature design\n", encoding="utf-8"
        )
        (self.root / "vendor").mkdir()
        (self.root / "vendor" / "THIRD_PARTY_PLAN.md").write_text(
            "# Not a project plan\n", encoding="utf-8"
        )
        before = sorted(path.relative_to(self.root) for path in self.root.rglob("*"))

        code, output, error = self.invoke("adopt", "--root", str(self.root))

        self.assertEqual(0, code, error)
        self.assertIn("FEATURE_DESIGN.md", output)
        self.assertNotIn("THIRD_PARTY_PLAN.md", output)
        self.assertEqual(
            before, sorted(path.relative_to(self.root) for path in self.root.rglob("*"))
        )

        code, _, error = self.invoke(
            "adopt",
            "--root",
            str(self.root),
            "--apply",
            "--agents",
            "codex,claude",
        )
        self.assertEqual(0, code, error)
        adopted = (self.root / "PLAN.md").read_text(encoding="utf-8")
        self.assertTrue(adopted.startswith(original))
        self.assertIn(planctl.PLAN_START, adopted)
        self.assertTrue((self.root / "docs" / "FEATURE_DESIGN.md").is_file())
        self.assertTrue(planctl.run_check(self.root).ok)


class StructuralValidationTests(PlanCtlTestCase):
    def test_done_with_not_run_is_rejected(self) -> None:
        self.init_project()
        plan = self.root / "PLAN.md"
        text = plan.read_text(encoding="utf-8").replace(
            "| W-001 | P0 | maintenance | Ready | NotRun |",
            "| W-001 | P0 | maintenance | Done | NotRun |",
        )
        plan.write_text(text, encoding="utf-8")

        result = planctl.run_check(self.root)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("cannot be Done" in error for error in result.errors), result.errors
        )
        self.assertTrue(
            any("requires a linked test" in error for error in result.errors),
            result.errors,
        )

    def test_done_with_passed_evidence_and_acceptance_is_valid(self) -> None:
        self.init_project()
        test_id = "TR-20260703-001"
        test_log = self.root / "docs" / "TEST_LOG.md"
        text = test_log.read_text(encoding="utf-8").replace(
            planctl.TEST_END,
            "\n".join(
                [
                    f"## {test_id}",
                    "",
                    "- Date: 2026-07-03",
                    "- Environment: unit test",
                    "- Revision: working tree",
                    "- Procedure: Run the acceptance test.",
                    "- Result: Passed",
                    "- Evidence: All assertions passed.",
                    "- Links: W-001",
                    "",
                    planctl.TEST_END,
                ]
            ),
        )
        test_log.write_text(text, encoding="utf-8")

        plan = self.root / "PLAN.md"
        plan_text = plan.read_text(encoding="utf-8").replace(
            "| W-001 | P0 | maintenance | Ready | NotRun | — | "
            "[Define the first delivery slice](docs/work/W-001-define-first-delivery.md) "
            "| — | — |",
            "| W-001 | P0 | maintenance | Done | Passed | — | "
            "[Define the first delivery slice](docs/work/W-001-define-first-delivery.md) "
            f"| [{test_id}](docs/TEST_LOG.md#{test_id.lower()}) | — |",
        )
        plan.write_text(plan_text, encoding="utf-8")

        work = self.root / "docs" / "work" / "W-001-define-first-delivery.md"
        work.write_text(
            work.read_text(encoding="utf-8").replace("- [ ]", "- [x]"),
            encoding="utf-8",
        )

        result = planctl.run_check(self.root)

        self.assertTrue(result.ok, result.errors)

    def test_closed_bug_without_passed_evidence_is_rejected(self) -> None:
        self.init_project()
        bugs = self.root / "docs" / "BUGS.md"
        text = bugs.read_text(encoding="utf-8").replace(
            planctl.BUG_END,
            "| BUG-001 | High | Closed | W-001 | Crash | Fixed | — |\n"
            + planctl.BUG_END,
        )
        bugs.write_text(text, encoding="utf-8")

        result = planctl.run_check(self.root)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("cannot be Closed" in error for error in result.errors), result.errors
        )

    def test_invalid_state_dependency_and_broken_link_are_rejected(self) -> None:
        self.init_project()
        plan = self.root / "PLAN.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace(
            "| W-001 | P0 | maintenance | Ready | NotRun | — | "
            "[Define the first delivery slice](docs/work/W-001-define-first-delivery.md) "
            "| — | — |",
            "| W-001 | P9 | maintenance | Flying | NotRun | W-999 | "
            "[Define the first delivery slice](docs/work/missing.md) | — | — |",
        )
        plan.write_text(text, encoding="utf-8")

        result = planctl.run_check(self.root)

        self.assertFalse(result.ok)
        joined = "\n".join(result.errors)
        self.assertIn("invalid priority", joined)
        self.assertIn("invalid delivery state", joined)
        self.assertIn("unknown work item W-999", joined)
        self.assertIn("does not resolve", joined)


class GitSynchronizationTests(PlanCtlTestCase):
    def test_delivery_change_requires_plan_work_and_test_updates(self) -> None:
        self.init_project()
        self.initialize_git_baseline()
        source = self.root / "src" / "app.py"
        source.parent.mkdir()
        source.write_text("print('delivery')\n", encoding="utf-8")

        result = planctl.run_check(self.root)

        self.assertFalse(result.ok)
        joined = "\n".join(result.errors)
        self.assertIn("synchronized PLAN.md", joined)
        self.assertIn("synchronized docs/TEST_LOG.md", joined)
        self.assertIn("synchronized work document", joined)

        with (self.root / "PLAN.md").open("a", encoding="utf-8") as handle:
            handle.write("\n")
        with (
            self.root / "docs" / "work" / "W-001-define-first-delivery.md"
        ).open("a", encoding="utf-8") as handle:
            handle.write("\n")
        with (self.root / "docs" / "TEST_LOG.md").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write("\n")

        result = planctl.run_check(self.root)
        self.assertTrue(result.ok, result.errors)

    def test_bug_work_requires_bug_registry_update(self) -> None:
        self.init_project()
        plan = self.root / "PLAN.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "| W-001 | P0 | maintenance |", "| W-001 | P0 | bug |"
            ),
            encoding="utf-8",
        )
        self.initialize_git_baseline()
        (self.root / "src").mkdir()
        (self.root / "src" / "fix.py").write_text("# fix\n", encoding="utf-8")
        for relative in (
            "PLAN.md",
            "docs/work/W-001-define-first-delivery.md",
            "docs/TEST_LOG.md",
        ):
            with (self.root / relative).open("a", encoding="utf-8") as handle:
                handle.write("\n")

        result = planctl.run_check(self.root)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("bug registry" in error for error in result.errors), result.errors
        )

    def test_exempt_document_change_does_not_require_sync(self) -> None:
        self.init_project()
        self.initialize_git_baseline()
        (self.root / "README.md").write_text("Typo fix.\n", encoding="utf-8")

        result = planctl.run_check(self.root)

        self.assertTrue(result.ok, result.errors)
        self.assertIn("No changed delivery files detected", result.notices)


class ConfigurationTests(PlanCtlTestCase):
    def test_configuration_is_valid_json_and_uses_forward_slashes(self) -> None:
        self.init_project()
        config = json.loads(
            (self.root / "plan-orchestrator.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(config)
        self.assertNotIn("\\\\", serialized)
        self.assertEqual(1, config["schema_version"])

    def test_dot_prefixed_delivery_paths_keep_their_name(self) -> None:
        self.assertEqual(
            ".github/workflows/check.yml",
            planctl._strip_prefix(".github/workflows/check.yml", ""),
        )
        self.assertTrue(
            planctl._matches(
                ".github/workflows/check.yml", [".github/**"]
            )
        )


if __name__ == "__main__":
    unittest.main()
