# Decisions

This file records important project decisions that affect future planning and implementation.

## Format

### D-NNN Decision title

Date:
Status: accepted

Decision:

Reason:

Impact:

Related work:
- W-NNN

### D-001 Keep the local dashboard read-only and repository-backed

Date: 2026-07-15
Status: accepted

Decision:

The first dashboard release will run from `planctl`, bind only to the local loopback interface, use no third-party runtime dependencies, and read the existing repository plan records as its sole source of truth. It may provide browser-side navigation, filtering, and refresh controls, but it will not modify managed records.

Reason:

The dashboard is intended to reduce the time needed to understand project state and find the next action. A separate database, web framework, or direct browser mutation path would add synchronization, security, installation, and maintenance costs that conflict with the project's lightweight delivery-contract role.

Impact:

Dashboard changes appear through short polling without a server restart. Future write controls must call validated, transactional `planctl` state-transition commands rather than editing Markdown directly. Remote access and multi-user coordination remain out of scope.

Related work:
- W-006
