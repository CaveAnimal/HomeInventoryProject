# TODO PLAN

## Status Legend
- `not-started`
- `in-progress`
- `blocked`
- `done`

## Epic: iPhone Capture -> Strict Vision Inventory -> Confirm -> Persist

| ID | Task | Status | Acceptance Criteria | Depends On |
|----|------|--------|---------------------|------------|
| T1 | Baseline and branch safety check | not-started | Current app flow documented; smoke run succeeds before changes | None |
| T2 | Define strict detection schema contract | not-started | Canonical schema and validation/defaulting rules documented in code comments/tests | T1 |
| T3 | Harden Ollama parsing and error handling | not-started | Malformed/non-JSON outputs handled gracefully with user-safe API responses | T2 |
| T4 | Add/adjust capture endpoint for inline new container creation | not-started | Mobile flow can create a new container and returns `container_id` + `public_id` with default `box` type | T1 |
| T5 | Extend capture UI to show item name + count + confidence + category | not-started | iPhone page renders strict list immediately after upload | T3 |
| T6 | Add mobile confirm action from capture page | not-started | User confirms selected detections without leaving capture page | T5 |
| T7 | Persist confirmed items and dismissed states with history | not-started | Confirmed rows appear in `box_items`; dismissed suggestions tracked | T6 |
| T8 | Add regression tests for end-to-end mobile capture flow | not-started | Tests cover create+upload+detect+confirm+dismiss scenarios | T3, T7 |
| T9 | Validate local-network iPhone flow | not-started | Real device test over desktop IP succeeds for at least 2 containers | T7 |
| T10 | Update user docs and operational checklist | not-started | README and quickstart include Ollama setup and mobile flow | T9 |

## Check-In Cadence
- Check-in A (after T3): Strict JSON reliability validated with test fixtures.
- Check-in B (after T6): iPhone capture page supports full review/confirm loop.
- Check-in C (after T10): End-to-end verified, docs updated, rollout decision made.

## Blockers Watchlist
- Ollama service not running or wrong model tag.
- iPhone camera upload permission/network issues.
- Unexpected schema migration need for confirmation metadata.

## Definition of Completion
- All tasks T1-T10 are `done`.
- GOAL success criteria are checked complete.
- No regression in existing create-box/search/label flows.
