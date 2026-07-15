# Test Log

Append one record for every delivery work unit. Allowed results: `Passed`, `Failed`, `Blocked`, `NotRun`, `N/A`.

<!-- project-plan-orchestrator:tests:start -->
<!-- Append new test records above the end marker. -->
## TR-20260715-002

- Date: 2026-07-15
- Environment: Windows, Python 3.14.5, Node.js 18.20.8, Git 2.54.0
- Revision: Uncommitted W-007 incomplete-adoption diagnostics implementation
- Procedure: Compile both planctl copies; run `python -m unittest discover -s tests -v`; syntax-check the embedded Dashboard JavaScript with `node --check -`; compare SHA-256 hashes of the source and vendored planctl copies; run both source and vendored project-plan guards.
- Result: Passed
- Evidence: Both Python files compiled; 32/32 automated tests passed, including adoption inventory persistence, legacy-install backfill/idempotence, non-blocking guard warnings, Dashboard incomplete-adoption diagnostics, legacy completion wording remaining at 0%, and verified mapping reaching 100%; embedded JavaScript syntax passed; source and vendored planctl hashes matched; both guards passed.
- Links: W-007, BUG-001

## TR-20260715-001

- Date: 2026-07-15
- Environment: Windows, Python 3.14.5, Node.js 18.20.8, Git 2.54.0
- Revision: Uncommitted W-006 lightweight local dashboard implementation
- Procedure: Compile both planctl copies; run `python -m unittest discover -s tests -v`; syntax-check the embedded dashboard JavaScript with `node --check -`; compare SHA-256 hashes of the source and vendored planctl copies; run both project-plan guards; start the vendored dashboard on an ephemeral loopback port, request `/api/status` and `/`, then stop it with Ctrl+C.
- Result: Passed
- Evidence: Both Python files compiled; 31/31 automated tests passed; embedded JavaScript syntax passed; source and vendored planctl hashes matched; both guards passed; the runtime API reported Project Plan Orchestrator, W-006, 80% progress, one pending item, and zero diagnostics; the HTML route returned HTTP 200 with UTF-8 content, no-store caching, and restrictive security headers; Ctrl+C shut down cleanly.
- Links: W-006

## TR-20260703-004

- Date: 2026-07-03
- Environment: Windows, Python 3.14.5
- Revision: Uncommitted strictness, decisions, and generated-files update
- Procedure: Compile both planctl copies; run `python -m unittest discover -s tests -v`; run both source and vendored project-plan guards.
- Result: Passed
- Evidence: Both planctl copies compiled; 23/23 automated tests passed; both guard commands passed and displayed `Strictness: normal`.
- Links: W-005

## TR-20260703-003

- Date: 2026-07-03
- Environment: Windows, Python 3.14.5
- Revision: Uncommitted project-specific content cleanup
- Procedure: Search tracked content for the removed project and work-item references; compile both CLI copies; run `python -m unittest discover -s tests -v`; run `python .project-plan/planctl.py check --root .`.
- Result: Passed
- Evidence: No removed project or work-item references remained; both CLI copies compiled; 16/16 automated tests passed; the repository guard passed with the generic adoption reference detected as the delivery change.
- Links: W-004

## TR-20260703-002

- Date: 2026-07-03
- Environment: Windows, Python 3.14.5
- Revision: Uncommitted bilingual README documentation update
- Procedure: Run the full unit test suite; run the vendored project-plan guard; inspect both README quick starts against the current `init`, `adopt`, and `check` CLI help.
- Result: Passed
- Evidence: 16/16 automated tests passed; the repository guard passed; both language versions contain reciprocal links and matching initialization, adoption, and verification commands.
- Links: W-003

## TR-20260703-001

- Date: 2026-07-03
- Environment: Windows, Python 3.14.5, Git 2.54.0
- Revision: Initial uncommitted repository working tree
- Procedure: Run `python -m unittest discover -s tests -v`; validate the Skill with `quick_validate.py`; compile both CLI copies with `py_compile`; run the vendored plan guard.
- Result: Passed
- Evidence: 16/16 unit and integration tests passed; Skill validation passed; both CLI copies compiled; the repository guard passed.
- Links: W-001

<!-- project-plan-orchestrator:tests:end -->
