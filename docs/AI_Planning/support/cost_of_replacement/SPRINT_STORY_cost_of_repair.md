# SPRINT STORY: cost_of_repair

## Epic
Opt-in, privacy-preserving estimated replacement cost lookup: local search-provider abstraction, local Ollama extraction, persisted history, and container/item UI display.

## Story List

### Story 1: Search Provider Spike & Config Scaffolding
- Jira Summary: Select cost-lookup search provider and add kill-switch config
- User Story: As a developer, I want a validated search-provider choice and a disable-by-default config scaffold so the feature can be built on solid ground and turned off instantly if needed.
- Acceptance Criteria:
  - Candidate search APIs evaluated for tier/ToS/response shape; DECISION-007 updated to Accepted.
  - `settings.py` gains `COST_LOOKUP_PROVIDER` and `COST_LOOKUP_MONTHLY_LIMIT`, mirroring the `VISION_PROVIDER` pattern.
  - Unset or unrecognized provider value resolves to fully disabled (zero network egress).
- Story Points: 3
- Priority: High
- Labels/Components: `spike`, `config`, `backend`
- Dependency Links: blocks Story 2, Story 3
- Traceability:
  - TODO: T1, T2
  - DECISIONS: D-005, D-007

### Story 2: Cost Lookup Provider Abstraction
- Jira Summary: Build CostLookupProvider abstraction mirroring VisionProvider
- User Story: As a developer, I want a provider abstraction consistent with the existing vision-provider pattern so the search/extraction backend can be swapped without touching endpoint code.
- Acceptance Criteria:
  - `CostLookupProvider` base class, `CostLookupError`, `get_cost_provider()` factory, `DisabledCostLookupProvider` implemented in `app/services/cost_lookup.py`.
  - Structurally mirrors `services/vision.py`'s `VisionProvider`/`get_provider()`/`VisionError`.
- Story Points: 3
- Priority: High
- Labels/Components: `backend`, `cost-lookup`
- Dependency Links: blocked-by Story 1; blocks Story 3
- Traceability:
  - TODO: T4
  - DECISIONS: D-001, D-005

### Story 3: Search Client and Local LLM Extraction
- Jira Summary: Implement search-provider client and local Ollama cost extraction
- User Story: As a homeowner, I want the app to look up a current market price and extract a structured estimate locally so I get useful data without my images or notes ever leaving my device.
- Acceptance Criteria:
  - Search client sends only item name + category, one item per request, never batched.
  - Local Ollama text-generation call extracts `estimated_cost_usd`, `confidence`, `source_title`/`source_url`.
  - Estimates lacking a cited source snippet/URL are rejected, not returned.
- Story Points: 8
- Priority: High
- Labels/Components: `backend`, `cost-lookup`, `llm`
- Dependency Links: blocked-by Story 1, Story 2; blocks Story 5
- Traceability:
  - TODO: T5, T6
  - DECISIONS: D-002, D-003

### Story 4: Persisted Estimate History
- Jira Summary: Persist cost estimates as append-only history
- User Story: As a homeowner, I want every price lookup saved to history so I can see how an item's estimated value has changed over time.
- Acceptance Criteria:
  - `cost_estimates` table added via `migrations/004_cost_estimates.sql`; `box_items` schema untouched.
  - `add_cost_estimate()`, `list_cost_estimates_for_item()`, `latest_cost_estimate()` added to `repository.py`; insert-only, no overwrite path.
- Story Points: 3
- Priority: High
- Labels/Components: `backend`, `data`, `migration`
- Dependency Links: blocks Story 6
- Traceability:
  - TODO: T3, T7
  - DECISIONS: D-004

### Story 5: Privacy Guardrails and Budget Guard
- Jira Summary: Enforce category exclusions, per-item opt-out, and monthly spend cap
- User Story: As a homeowner, I want sensitive item categories excluded from lookup by default and a hard cap on monthly lookups so my privacy is protected and costs stay predictable.
- Acceptance Criteria:
  - `Documents & Paper` and `Sentimental / Keepsakes` excluded by default before any network call is attempted.
  - Per-item opt-out flag respected.
  - Monthly query counter enforces `COST_LOOKUP_MONTHLY_LIMIT`, refusing new lookups with a specific error once reached, resetting each calendar month.
- Story Points: 5
- Priority: High
- Labels/Components: `backend`, `privacy`, `cost-lookup`
- Dependency Links: blocked-by Story 3; blocks Story 6
- Traceability:
  - TODO: T8, T9
  - DECISIONS: D-006

### Story 6: Single and Batch Cost-Estimate API Endpoints
- Jira Summary: Add API endpoints for single-item and batch cost estimates
- User Story: As a homeowner, I want to estimate the cost of one item or all items in a container so I can build out replacement-cost data at my own pace.
- Acceptance Criteria:
  - `POST /api/items/{item_id}/cost-estimate` triggers lookup+extraction+persist for one item, respecting privacy and budget guards.
  - `POST /api/boxes/{box_id}/cost-estimates` fans out into N sequential single-item calls, never one bulk request; partial success is reported.
  - `GET` endpoint(s) return latest estimate + history for an item.
- Story Points: 5
- Priority: High
- Labels/Components: `backend`, `api`, `cost-lookup`
- Dependency Links: blocked-by Story 4, Story 5; blocks Story 7
- Traceability:
  - TODO: T10, T11, T12
  - DECISIONS: D-003

### Story 7: Cost Estimate UI on Item/Container Pages
- Jira Summary: Show estimate-cost action and results on item/container detail pages
- User Story: As a homeowner, I want to trigger and see cost estimates directly on the item or container page so I don't need a separate workflow.
- Acceptance Criteria:
  - Single-item and "estimate all" batch trigger actions available on the detail page.
  - Latest estimate displayed with confidence, source link, and age.
  - Feature shows a disabled/unavailable state (not a raw error) when `COST_LOOKUP_PROVIDER` is disabled or the item's category is excluded.
- Story Points: 5
- Priority: Medium
- Labels/Components: `frontend`, `cost-lookup`, `ux`
- Dependency Links: blocked-by Story 6; blocks Story 8
- Traceability:
  - TODO: T13
  - DECISIONS: D-005, D-006

### Story 8: Testing and Documentation
- Jira Summary: Add regression tests and update operational documentation
- User Story: As a developer, I want automated coverage and updated docs so the feature is verifiable and operable without tribal knowledge.
- Acceptance Criteria:
  - `tests/test_cost_lookup.py` covers disabled provider, rejected extraction without source, category/item exclusion, budget cap + reset, and batch fan-out call count.
  - README/operational checklist documents new env vars, kill switch, rollback steps, and excluded-category list.
- Story Points: 5
- Priority: Medium
- Labels/Components: `testing`, `documentation`
- Dependency Links: blocked-by Story 7
- Traceability:
  - TODO: T14, T15
  - DECISIONS: D-005, D-006

## Suggested Sprint Ordering
1. Story 1
2. Story 2
3. Story 3
4. Story 4
5. Story 5
6. Story 6
7. Story 7
8. Story 8

## Exit Criteria
- All story acceptance criteria met.
- TODO tasks T1-T15 complete.
- GOAL success criteria validated, including verified zero network egress when `COST_LOOKUP_PROVIDER` is disabled.
