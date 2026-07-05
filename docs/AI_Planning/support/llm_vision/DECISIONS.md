# DECISIONS LOG

## D-001: Local Ollama Is the Primary Vision Backend
- Status: Accepted
- Date: 2026-06-30
- Context: User requires desktop-hosted, privacy-preserving workflow reachable from iPhone.
- Decision: Use Ollama `llama3.2-vision` as the default backend for this flow.
- Rationale: Keeps images local and aligns with existing installed runtime.
- Alternatives considered:
  - OpenAI vision API: potentially higher accuracy but sends data to cloud.
  - Heuristic provider: insufficient for strict inventory extraction.
- Consequences:
  - Need runtime health checks and clear error handling when model/server unavailable.
  - Prompt and parser discipline become critical for consistent JSON output.
- Rollback plan: Fall back to current suggestion flow with heuristic provider for non-blocking usage.
- Validation plan: Execute end-to-end test with iPhone upload and verify item extraction fields.

## D-002: Confirmation Required Before Inventory Persistence
- Status: Accepted
- Date: 2026-06-30
- Context: User wants strict inventory but still needs trustworthy item counts.
- Decision: Keep detections as provisional until user confirms on mobile page.
- Rationale: Prevents polluted inventory from model mistakes and supports user trust.
- Alternatives considered:
  - Auto-save all detections as confirmed: faster but error-prone.
  - Manual-only entry: accurate but defeats AI assistance.
- Consequences:
  - Requires explicit UI actions and clear status labels.
  - Adds one interaction step before persistence.
- Rollback plan: Allow temporary bulk-confirm for debugging only, hidden behind a flag.
- Validation plan: Confirm rejected detections never appear in `box_items`.

## D-003: Strict Detection Contract
- Status: Accepted
- Date: 2026-06-30
- Context: Model output variability can break inventory quality.
- Decision: Enforce normalized detection object shape with required keys: `name`, `quantity`, `confidence`, `category`, `notes`.
- Rationale: Stable shape simplifies UI rendering and persistence logic.
- Alternatives considered:
  - Loose free-text parsing: fragile and hard to test.
  - Schema-free payload passthrough: leaks model inconsistency to UI.
- Consequences:
  - Need parser validation and defaulting strategy.
  - Malformed results must surface as actionable user errors.
- Rollback plan: Temporarily relax parser while logging malformed outputs for fixes.
- Validation plan: Add tests for valid JSON, malformed JSON, and partial fields.

## D-004: Container Type Defaults to `box`
- Status: Accepted
- Date: 2026-06-30
- Context: User requested default type `box` for this implementation phase.
- Decision: New-container-from-capture path sets `container_type=box` unless explicitly changed in later phase.
- Rationale: Minimizes decision load during capture and matches current backend default.
- Alternatives considered:
  - Ask for type each time on mobile: more flexible but slower.
  - Infer type from image: unnecessary complexity and low confidence.
- Consequences:
  - Existing behavior remains consistent across desktop and mobile.
  - Future enhancement can add optional type override.
- Rollback plan: Restore previous create flow only if new path introduces regressions.
- Validation plan: Verify created records always contain `container_type='box'`.

## D-005: iPhone Capture Page Is the Review Surface
- Status: Accepted
- Date: 2026-06-30
- Context: User wants item list returned to the same web page being viewed on iPhone.
- Decision: Render detection list + counts on `capture.html` and support in-place confirmation.
- Rationale: Keeps flow continuous and mobile-first.
- Alternatives considered:
  - Redirect to desktop-oriented container detail page: breaks capture momentum.
  - Separate mobile review page: extra navigation overhead.
- Consequences:
  - `capture.html` grows in complexity and needs stronger state handling.
  - Must keep UI fast and touch-friendly.
- Rollback plan: Keep existing link to container detail review as fallback path.
- Validation plan: Confirm full flow can complete without leaving capture page.
