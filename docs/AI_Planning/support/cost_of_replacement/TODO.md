# TODO PLAN

## Status Legend
- `not-started`
- `in-progress`
- `blocked`
- `done`

## Epic: Opt-In Cost Lookup -> Local LLM Extraction -> Persisted History -> UI Display

| ID | Task | Status | Acceptance Criteria | Depends On |
|----|------|--------|---------------------|------------|
| T1 | SPIKE: Select search provider (time-boxed) | done | Tavily selected (`COST_LOOKUP_PROVIDER=tavily`, key `COST_LOOKUP_API_KEY`); Tavily/Exa/Brave/SerpAPI evaluated for tier/ToS/response shape; D-007 updated from Proposed to Accepted | None |
| T2 | Add `COST_LOOKUP_PROVIDER` and budget-cap env vars to `settings.py` | done | `settings.py` gains `COST_LOOKUP_PROVIDER` (mirrors `VISION_PROVIDER` pattern) and `COST_LOOKUP_MONTHLY_LIMIT`; unset/unrecognized value resolves to disabled | None |
| T3 | Create `migrations/004_cost_estimates.sql` | done | New `cost_estimates` table (fields: id, box_item_id FK, estimated_cost_usd, confidence, source_title, source_url, created_at) + index on `box_item_id`; migration applies cleanly via `database.py:migrate()`; `box_items` schema untouched | None |
| T4 | Scaffold `app/services/cost_lookup.py` provider abstraction | done | `CostLookupProvider` base class, `CostLookupError` exception, `get_cost_provider()` factory keyed off `COST_LOOKUP_PROVIDER`, `DisabledCostLookupProvider` returning a safe no-op; structurally mirrors `services/vision.py` | T2 |
| T5 | Implement real search-provider client | done | Provider from T1 wired into `cost_lookup.py` via `requests`; outbound query built ONLY from item name + category (never notes/box/room); one item per request enforced at the function signature level | T1, T4 |
| T6 | Implement local Ollama extraction step | done | Search results passed to a local text-generation Ollama call (same `requests.post` pattern as `OllamaVisionProvider`); returns normalized `estimated_cost_usd`/`confidence`/`source_title`/`source_url`; estimates with no cited source snippet/URL are rejected, not returned | T5 |
| T7 | Add `repository.py` persistence functions | done | `add_cost_estimate()`, `list_cost_estimates_for_item()`, `latest_cost_estimate()` added; insert-only (no update/overwrite path exists); unit-testable against a temp SQLite connection | T3 |
| T8 | Add category and per-item lookup opt-out enforcement | done | `Documents & Paper` and `Sentimental / Keepsakes` excluded by default before any network call is attempted (not just hidden in UI); per-item opt-out flag respected; attempting a lookup on an excluded item returns a clear, specific error | T4 |
| T9 | Add app-side monthly budget guard | done | Query count for the current calendar month tracked; requests refused with a specific error once `COST_LOOKUP_MONTHLY_LIMIT` is reached; counter resets in a new month | T7 |
| T10 | Add single-item cost-estimate API endpoint | done | `POST /api/items/{item_id}/cost-estimate` triggers lookup+extraction+persist for one confirmed `box_items` row; respects T8 and T9 guards; returns the new estimate | T6, T7, T8, T9 |
| T11 | Add batch cost-estimate API endpoint | done | `POST /api/boxes/{box_id}/cost-estimates` fans out into N sequential single-item calls (never one bulk provider request); partial success supported (some items estimated, some skipped/failed, response reports both) | T10 |
| T12 | Add read endpoint(s) for stored estimates | done | `GET` endpoint returns latest estimate + history for a given item, used by the UI | T7 |
| T13 | Add "Estimate cost" UI on item/container detail page | done | Single-item and batch ("estimate all") trigger actions; displays latest estimate with confidence, source link, and age; disabled/greyed-out state when `COST_LOOKUP_PROVIDER` is disabled; excluded-category items show why lookup is unavailable rather than a raw error | T10, T11, T12 |
| T14 | Add `tests/test_cost_lookup.py` | done | Tests cover: disabled provider makes zero network calls, malformed/no-source extraction is rejected, category exclusion blocks network calls, per-item opt-out, budget cap refusal + monthly reset, batch endpoint issues exactly N single-item calls | T8, T9, T11 |
| T15 | Update README / operational checklist | done | New env vars (`COST_LOOKUP_PROVIDER`, budget cap, any provider API key) documented; kill-switch and rollback steps documented; excluded-category list documented | T13, T14 |

## Check-In Cadence
- Check-in A (after T4): Provider abstraction scaffolding compiles/imports cleanly with kill switch verified.
- Check-in B (after T9): Privacy guardrails (category/item opt-out, budget cap) verified in isolation before any endpoint wires them together.
- Check-in C (after T15): End-to-end verified (single + batch, UI, docs), rollout decision made.

## Blockers Watchlist
- T1 spike stalls or finds no viable low-cost provider with acceptable ToS — escalate per the Decision Validation Loop (see [abstract framework](../llm_vision/abstract_goal_context_decisions_todo.md)) rather than picking one under time pressure.
- Local Ollama host has no text-generation model available (only the vision model) — needs a startup/availability check before T6 depends on it.
- Search provider response format doesn't cleanly map to source-URL citation, undermining the hallucination mitigation in GOAL.md's risk table.

## Definition of Completion
- All tasks T1-T15 are `done`.
- GOAL.md success criteria are checked complete.
- No regression in existing capture/confirm/search/label flows.
- `COST_LOOKUP_PROVIDER=disabled` (or unset) verified to produce zero network egress for this feature.
