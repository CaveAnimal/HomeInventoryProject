# PROJECT GOAL

## Primary Objective
Deliver an iPhone-first capture workflow in the local home inventory app where a user takes a photo from Safari, uploads it, gets a new container identifier with default type `box`, receives a strict AI-generated item inventory with counts on the same mobile page, confirms results, and then saves confirmed items into the permanent home inventory.

## Why This Matters (Business Value)
- Reduces friction so inventory can be captured at the moment a container is opened.
- Improves insurance readiness by producing explicit item names and counts per container.
- Keeps sensitive household images local by using the Ollama vision stack on the desktop host.

## Success Criteria (Definition of Done)
- [ ] On iPhone Safari, a user can capture and upload at least one photo without leaving the app.
- [ ] The workflow can create a new container during capture and returns both numeric `container_id` and `public_id`.
- [ ] New containers created through this flow default to `container_type=box` unless user overrides in a later enhancement.
- [ ] Vision output is parsed from strict JSON into item rows containing at minimum: `name`, `quantity`, `confidence`, `category`, `notes`.
- [ ] The iPhone capture page shows detected items and quantities before final save.
- [ ] User confirmation action persists accepted items to inventory (`box_items`) and marks source detections as confirmed.
- [ ] Rejected items are not added to inventory and are tracked as dismissed for auditability.
- [ ] End-to-end flow works on local network using desktop-hosted app + iPhone browser.

## In Scope
- Mobile web capture UX for iPhone Safari.
- Create-container-from-capture path with default `box` type.
- Ollama `llama3.2-vision` integration for strict inventory extraction.
- On-page review and confirmation of item list and counts.
- Persist confirmed inventory items to existing app schema and history.
- Validation and error handling for malformed or non-JSON model responses.

## Explicitly Out of Scope
- ❌ Native iOS app development or App Store distribution.
- ❌ Cloud vision processing as a default path.
- ❌ Automatic barcode/serial OCR pipeline beyond current model text interpretation.
- ❌ Full autonomous acceptance without user confirmation.
- ❌ Multi-user auth/permissions redesign.

## Non-Negotiable Constraints
- Keep deployment local-first on desktop host; no mandatory cloud dependency.
- Use existing FastAPI + SQLite architecture unless a critical blocker is discovered.
- Preserve current inventory data model compatibility with existing records.
- Ensure iPhone flow remains usable on home Wi-Fi via desktop IP address.
- Keep `box` as the default container type in this phase.

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| Vision model returns non-strict JSON or noisy content | High | Add robust JSON extraction, schema validation, retries, and fallback messaging |
| Poor photo quality causes missed items or wrong counts | Medium | Add capture guidance, confidence display, and mandatory user confirmation |
| Mobile UX too slow on large image uploads | Medium | Compress/resample images server-side and show clear progress states |
| User confuses suggestions with confirmed inventory | High | Explicit two-step review/confirm UI and status labels |
| Local Ollama runtime unavailable | Medium | Health-check model on startup and show actionable setup errors |

## Rollback Plan
If this flow causes critical usability or data issues:
- Step 1: Disable strict mobile-confirm path behind feature flag and revert to existing detection review on container detail page.
- Step 2: Keep uploaded photos but stop auto-suggestion persistence from capture endpoint.
- Step 3: Validate existing create-box and add-photo flows still function.
- Time to rollback: 15-30 minutes.
