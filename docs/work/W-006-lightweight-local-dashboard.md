# W-006 - Add a lightweight local dashboard

- Work ID: W-006
- Type: feature
- Priority: P0
- Owner: Codex
- Updated: 2026-07-15

## Outcome

Provide a dependency-free local dashboard that makes the repository's current objective, delivery progress, current work, next action, and pending work visible without opening several Markdown files.

## Non-goals

- Do not introduce Node.js, a frontend framework, a database, an external service, or a Python package dependency.
- Do not create a second project-state store or cache authoritative plan state in the browser.
- Do not let the first dashboard release modify work, bug, test, or decision records.
- Do not expose the server beyond the local loopback interface.

## Dependencies

- W-001.
- W-005.

## Design and interfaces

- Add `planctl serve --root <project>` with optional `--port` and `--no-browser` flags.
- Bind only to `127.0.0.1` and serve an embedded-project static dashboard plus a JSON status endpoint.
- Read `plan-orchestrator.json` and the managed `PLAN.md` table on every status request so the page follows repository changes without synchronization state.
- Use short polling for live updates and provide search, delivery-state filtering, manual refresh, and an automatic-refresh toggle.
- Keep the status snapshot independent from the full guard so refreshing the page does not repeatedly execute Git or complete evidence validation.

## Acceptance

- [x] The dashboard shows project name, objective, progress, current work, next action, and plan items.
- [x] Dashboard data updates after plan files change without restarting the server.
- [x] The UI provides lightweight search/filter/refresh controls and no record mutation controls.
- [x] The server uses only the Python standard library and listens only on loopback.
- [x] Missing or temporarily invalid project records produce a recoverable dashboard error instead of terminating the server.
- [x] Initialization installs every asset needed by the vendored `planctl serve` command.
- [x] English and Chinese README instructions describe purpose, startup, security boundary, and limitations.
- [x] Automated tests and both source and vendored guards pass.

## Implementation notes

- Added `planctl serve --root <project>` with configurable port, default-browser launch, a headless option, clean Ctrl+C shutdown, and user-facing port errors.
- Embedded the HTML, CSS, and JavaScript in the single standard-library CLI so initialized projects require no additional runtime asset or installation step.
- Added a versioned `/api/status` snapshot with project metadata, verified progress, current work, status counts, dependencies, tests, bugs, diagnostics, and fresh reads for every request.
- Added a responsive single-page interface with search, delivery-state filtering, manual refresh, and non-overlapping two-second polling.
- Bound the server exclusively to `127.0.0.1`; limited it to fixed routes; rejected write methods, path traversal, and non-local Host headers; and added no-store, content-type, frame, referrer, and CSP headers.
- Kept full guard and Git checks out of the polling path. The dashboard performs lightweight managed-plan parsing and reports temporary JSON, UTF-8, table, and path-field errors without stopping the server.
- Added coverage for initialized and adopted projects, progress semantics, live plan changes, missing and partially written records, HTTP routes and headers, read-only behavior, path isolation, server shutdown, occupied ports, and vendored command installation.
- Updated English and Chinese README guidance and recorded the durable read-only architecture boundary in D-001.

## Verification

- Passed: [TR-20260715-001](../TEST_LOG.md#tr-20260715-001).

## Known issues

- None recorded.

## Next action

Design transactional `next`, `start`, `record-test`, and `complete` CLI commands before considering any dashboard write controls.
