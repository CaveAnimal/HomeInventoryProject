# SPRINT STORY: llm_vision

## Epic
Mobile-first strict inventory capture using iPhone Safari and local Ollama vision.

## Story List

### Story 1: Strict Vision Contract and Parser Reliability
- Jira Summary: Harden local vision output into strict inventory schema
- User Story: As a homeowner, I want AI detections normalized into a strict format so that item review and save are reliable.
- Acceptance Criteria:
  - Ollama responses are parsed into `name`, `quantity`, `confidence`, `category`, `notes`.
  - Invalid outputs produce controlled errors and do not corrupt data.
  - Unit tests cover valid, partial, and malformed responses.
- Story Points: 5
- Priority: High
- Labels/Components: `vision`, `backend`, `data-quality`
- Dependency Links: blocks Story 3, Story 4
- Traceability:
  - TODO: T2, T3
  - DECISIONS: D-001, D-003

### Story 2: Inline Container Creation from Mobile Capture
- Jira Summary: Enable new container creation during iPhone capture flow
- User Story: As a homeowner, I want to create a new container while capturing photos so I do not have to switch screens.
- Acceptance Criteria:
  - Capture flow can create a new container and returns IDs needed by mobile UI.
  - Default `container_type` is `box`.
  - Existing create-container flow remains functional.
- Story Points: 3
- Priority: High
- Labels/Components: `mobile-capture`, `backend`
- Dependency Links: blocks Story 3
- Traceability:
  - TODO: T4
  - DECISIONS: D-004

### Story 3: Mobile Review and Confirmation on Capture Page
- Jira Summary: Show strict item list and confirm from iPhone capture page
- User Story: As a homeowner, I want to review item names and counts immediately and confirm what should become inventory.
- Acceptance Criteria:
  - Capture page displays detected item rows with count/confidence/category.
  - User can confirm or dismiss detections without leaving capture page.
  - UI status clearly distinguishes suggested vs confirmed.
- Story Points: 8
- Priority: High
- Labels/Components: `frontend`, `mobile-capture`, `ux`
- Dependency Links: blocked-by Story 1, Story 2; blocks Story 4
- Traceability:
  - TODO: T5, T6
  - DECISIONS: D-002, D-005

### Story 4: Persistence, Auditability, and E2E Validation
- Jira Summary: Persist confirmed inventory and validate end-to-end iPhone workflow
- User Story: As a homeowner, I want confirmed items saved accurately so my home inventory is trustworthy for future lookup and insurance use.
- Acceptance Criteria:
  - Confirmed detections become `box_items` records with expected fields.
  - Dismissed detections remain non-inventory and auditable.
  - Automated tests and real-device checks pass.
  - Documentation updated with operational steps.
- Story Points: 8
- Priority: High
- Labels/Components: `backend`, `testing`, `documentation`
- Dependency Links: blocked-by Story 3
- Traceability:
  - TODO: T7, T8, T9, T10
  - DECISIONS: D-002, D-003

## Suggested Sprint Ordering
1. Story 1
2. Story 2
3. Story 3
4. Story 4

## Exit Criteria
- All story acceptance criteria met.
- TODO tasks T1-T10 complete.
- GOAL success criteria validated on desktop + iPhone local network.
