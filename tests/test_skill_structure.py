from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "project-plan-orchestrator"


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter_contains_only_name_and_description(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        lines = [
            line for line in match.group(1).splitlines() if line and not line.startswith(" ")
        ]
        keys = [line.split(":", 1)[0] for line in lines]
        self.assertEqual(["name", "description"], keys)
        self.assertIn("when", text.lower().split("---", 2)[1].lower())
        self.assertNotIn("TODO", text)

    def test_openai_metadata_mentions_the_skill(self) -> None:
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Project Plan Orchestrator"', metadata)
        self.assertIn("$project-plan-orchestrator", metadata)

    def test_required_resources_exist(self) -> None:
        required = [
            "scripts/planctl.py",
            "references/protocol.md",
            "references/adoption.md",
            "references/validation.md",
            "assets/templates/PLAN.md",
            "assets/templates/work-item.md",
            "assets/templates/BUGS.md",
            "assets/templates/TEST_LOG.md",
            "assets/templates/plan-orchestrator.json",
            "assets/templates/AGENTS.fragment.md",
            "assets/templates/CLAUDE.fragment.md",
            "assets/templates/project-plan.yml",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)

    def test_skill_body_stays_compact(self) -> None:
        lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 500)


if __name__ == "__main__":
    unittest.main()
