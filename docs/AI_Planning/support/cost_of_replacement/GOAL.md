# PROJECT GOAL

## Primary Objective
Add an opt-in "estimated replacement cost" feature to the home inventory app: for a confirmed item, look up a current market price via a web search API and use a local LLM to extract a structured cost estimate, without ever sending photos or full-inventory context off the device.

## Why This Matters (Business Value)
- Supports insurance documentation (replacement-cost estimates alongside item records).
- Keeps the privacy stance the app was already built on ([DECISIONS.md](../llm_vision/DECISIONS.md) D-001: local Ollama for privacy): only a short item-name query leaves the device, never images or personal notes.
- Builds on the existing local-LLM investment (Ollama) instead of introducing a cloud LLM dependency.

## Success Criteria (Definition of Done)
- [x] User can trigger a cost estimate for a single confirmed item from the container detail page.
- [x] User can trigger cost estimates for a batch of items (e.g. "estimate all" for a container), issued as separate per-item requests, never one bulk request.
- [x] Estimate returned as structured data: `estimated_cost_usd`, `confidence`, `source_title`/`source_url`, timestamp.
- [x] Only item name + category (never photos, box/room location, or notes) are sent to the search provider.
- [x] `Documents & Paper` and `Sentimental / Keepsakes` categories are excluded from lookup by default.
- [x] Feature has a global kill switch (env var) to disable all network egress for this feature.
- [x] Estimates are persisted with history (not just overwritten) so price changes over time are auditable.
- [x] LLM extraction step runs on the local Ollama runtime; no item data is sent to a cloud LLM.

## In Scope
- New `cost_lookup` service module: search provider abstraction + local LLM extraction.
- New `cost_estimates` history table + migration.
- New API endpoints for single-item and batch estimate requests, and reading stored estimates.
- Category-based and per-item opt-out of the lookup.
- App-side rate/budget guard against runaway search API spend.

## Explicitly Out of Scope
- ❌ Automatic/background cost lookups triggered by photo capture (must remain a deliberate user action).
- ❌ Cloud LLM usage for the extraction/reasoning step.
- ❌ Bulk-exporting the whole inventory to a third party in one call.
- ❌ Currency conversion / multi-currency support (USD only for v1).
- ❌ Price-tracking notifications ("alert me when price drops").

## Non-Negotiable Constraints
- Never send photos to any external service as part of this feature.
- Never batch multiple items' identifying info into a single outbound search request.
- Local Ollama model performs all reasoning over search results; no OpenAI/Anthropic/other cloud LLM calls.
- Feature must be fully disable-able via a single env var, matching the existing `VISION_PROVIDER=heuristic` kill-switch precedent.
- Never silently alter item name/category/quantity as a side effect of estimating cost.

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| Search API costs scale unexpectedly (provider has no default spending cap) | Medium | App-side monthly query counter/budget guard; refuse new lookups past a configured cap |
| Item name/category leaks sensitive household detail via search query | Medium | Category-based opt-out list, notes field never included in queries, one item per request |
| Search provider ToS changes or API is discontinued (already happened once with Brave's free tier in Feb 2026) | Medium | Provider abstraction mirrors `VisionProvider` so a new provider can be swapped in without touching callers |
| Local LLM invents a plausible-but-wrong price with no real grounding (hallucination) | High | Require a cited source URL/snippet; reject estimates with no supporting snippet; surface confidence + source for manual review |
| Stale prices shown as current | Low | Store `created_at` per estimate and show age in UI; re-estimate is a manual action |

## Rollback Plan
- Step 1: Set `COST_LOOKUP_PROVIDER=disabled` to stop all network calls immediately.
- Step 2: Cost estimate UI elements degrade to "not available" without affecting existing item/photo/detection flows.
- Step 3: `cost_estimates` table can be dropped without affecting `box_items` (no required columns added to the core item table).
- Time to rollback: under 10 minutes.
