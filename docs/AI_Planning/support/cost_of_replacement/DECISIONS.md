# DECISIONS LOG

## D-001: Provider Abstraction Mirrors `VisionProvider`
- Status: Accepted
- Date: 2026-07-15
- Context: The app already has a proven provider-abstraction pattern (`services/vision.py`: base class, `get_provider()` factory keyed off an env var, safe fallback) for swapping local-vs-remote backends without touching callers.
- Decision: Implement `app/services/cost_lookup.py` with a `CostLookupProvider` base class, a `get_cost_provider()` factory keyed off `COST_LOOKUP_PROVIDER`, and a `CostLookupError` exception, structurally mirroring `VisionProvider`/`get_provider()`/`VisionError`.
- Rationale: Consistency with an established, working pattern reduces review effort and lets the search provider be swapped later (see D-007) without touching endpoint code.
- Alternatives considered:
  - Ad hoc function with an if/elif provider switch inline in `main.py`: faster to write, but breaks the codebase's established abstraction convention and is harder to test in isolation.
- Consequences:
  - New file `app/services/cost_lookup.py` follows the same shape as `vision.py` (dataclass for the result, `normalize_*()` function, exception type).
  - Unit tests can substitute a fake provider the same way vision tests use `HeuristicVisionProvider`.
- Rollback plan: Delete `cost_lookup.py`; no other module depends on it until the API endpoints (D-004) are wired in.
- Validation plan: `get_cost_provider()` returns a safe no-op provider for any unrecognized `COST_LOOKUP_PROVIDER` value, matching `get_provider()`'s fallback-to-heuristic behavior.

## D-002: Local Ollama Performs All Extraction Reasoning
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md requires the LLM reasoning step to run locally; only the item name + category may leave the device (via the search provider), never via an LLM call.
- Decision: The extraction step (turning raw search results into `estimated_cost_usd`, `confidence`, `source_title`/`source_url`) is a local Ollama text-generation call, using the same `requests.post` pattern as `OllamaVisionProvider`, not a vision model.
- Rationale: Keeps parity with the existing privacy stance ([llm_vision DECISIONS.md](../llm_vision/DECISIONS.md) D-001: local Ollama for privacy) and avoids introducing a second LLM vendor/dependency.
- Alternatives considered:
  - Cloud LLM (OpenAI/Anthropic) for extraction: better structured-output reliability, but sends item data off-device — explicitly out of scope per GOAL.md.
  - No LLM extraction, regex/heuristic parsing of search snippets: cheaper but fragile against varied result formatting.
- Consequences:
  - Requires a text-capable Ollama model available on the host (separate from `llama3.2-vision`); needs a startup/availability check similar to the vision flow.
  - Extraction prompt must require a cited source snippet/URL; estimates without one are rejected (per GOAL.md risk mitigation for hallucination).
- Rollback plan: If local extraction proves unreliable, fall back to returning raw search results without LLM-structured extraction (degraded but still privacy-safe) rather than escalating to a cloud LLM.
- Validation plan: Test with fixture search results confirming rejection of estimates lacking a source snippet/URL.

## D-003: One Item Per Outbound Search Request, No Batching
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md forbids batching multiple items' identifying info into a single outbound request, to avoid leaking full-inventory shape to a third party even when the user requests a batch ("estimate all for this container").
- Decision: A batch UI action (e.g., "estimate all in this box") fans out into N sequential single-item calls to the cost-lookup provider; the provider interface only ever accepts one item at a time.
- Rationale: Directly enforces the GOAL.md non-negotiable constraint; keeps the provider interface simple (single-item request/response) regardless of how many items the API layer processes per user action.
- Alternatives considered:
  - Single batched request with an array of items to the search provider: fewer HTTP calls, faster, but explicitly disallowed by GOAL.md.
- Consequences:
  - Batch endpoint (D-004) must include per-item budget-guard checks (D-006) and can partially succeed (some items estimated, others skipped/failed) without failing the whole batch.
  - Batch requests take proportionally longer than a hypothetical single bulk call.
- Rollback plan: N/A — this is a hard privacy constraint, not a reversible implementation choice.
- Validation plan: Test asserts that a batch request against a container with N eligible items results in exactly N separate outbound calls to the (mocked) search provider, each containing exactly one item's identifying info.

## D-004: Cost Estimates Are Insert-Only History, Never Overwritten
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md requires estimates be auditable over time, not just the most recent value.
- Decision: New `cost_estimates` table (migration `004_cost_estimates.sql`) is append-only; `repository.add_cost_estimate()` always inserts a new row. "Current" estimate for display is a query (`latest_cost_estimate()` — most recent row per `box_items.id`), not a stored/updated column.
- Rationale: Matches the existing `record_history()`-style audit pattern already used elsewhere in `repository.py`; avoids losing price-history data on re-estimate.
- Alternatives considered:
  - Single `estimated_cost_usd` column on `box_items`, overwritten on each lookup: simpler schema, but violates the auditability success criterion in GOAL.md.
- Consequences:
  - `cost_estimates` can grow unbounded over time; acceptable for a local-first single-household app, but worth a pruning/archival note if it ever becomes a concern.
  - No `box_items` schema changes required at all — reduces migration risk.
- Rollback plan: Drop the `cost_estimates` table; `box_items` is completely unaffected since it holds no cost-estimate columns.
- Validation plan: Test that re-estimating the same item twice results in two rows, and `latest_cost_estimate()` returns the more recent one.

## D-005: Feature-Wide Kill Switch via `COST_LOOKUP_PROVIDER=disabled`
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md requires a global env-var kill switch disabling all network egress for this feature, matching the existing `VISION_PROVIDER=heuristic` precedent.
- Decision: `settings.py` adds `COST_LOOKUP_PROVIDER` (default: unset/disabled until a provider is selected — see D-007) following the same `os.environ.get(NAME, default)` pattern as `VISION_PROVIDER`. `get_cost_provider()` returns a `DisabledCostLookupProvider` (raises a user-safe "feature disabled" `CostLookupError`, makes zero network calls) for `"disabled"` or any unrecognized value.
- Rationale: Direct precedent match; operators already know this pattern from `VISION_PROVIDER`.
- Alternatives considered:
  - Separate boolean flag (`COST_LOOKUP_ENABLED=false`) alongside a provider name: more explicit but introduces a second env var where one suffices, inconsistent with the single-var precedent.
- Consequences:
  - UI must handle the "disabled" state gracefully (hide or grey out the "Estimate cost" action rather than erroring loudly).
- Rollback plan: Set `COST_LOOKUP_PROVIDER=disabled` (or unset it) to fully disable; no code rollback needed.
- Validation plan: Test that with the env var unset or set to `"disabled"`, no `requests` calls are made and the API returns a clear "feature disabled" response rather than a 500.

## D-006: App-Side Monthly Budget Guard
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md flags unbounded search-API spend as a Medium-impact risk since the provider has no default spending cap.
- Decision: `cost_lookup.py` (or `repository.py`) tracks a monthly outbound-query counter; a configurable cap (new env var, e.g. `COST_LOOKUP_MONTHLY_LIMIT`) causes new lookup requests to be refused (not silently dropped) once exceeded, with a clear API error so the UI can inform the user.
- Rationale: Directly implements the GOAL.md mitigation for the budget-overrun risk; app-side enforcement works regardless of what caps (if any) the provider itself offers.
- Alternatives considered:
  - Rely solely on the search provider's own dashboard/caps: simpler, but provides no in-app feedback and risks surprise bills before anyone checks the dashboard.
- Consequences:
  - Requires persisting a counter (either a row in `cost_estimates`-adjacent tracking or a derived count query over `cost_estimates.created_at` for the current month) — implementation detail for TODO.md.
- Rollback plan: Remove the cap check (return early without refusing); the counter itself is harmless to leave in place.
- Validation plan: Test that once the configured cap is reached within a calendar month, further lookup attempts are refused with a specific error, and the count resets in a new month.

## D-007: Search Provider Selection — Tavily
- Status: Accepted
- Date: 2026-07-15
- Context: GOAL.md's risk table notes a prior provider casualty (Brave's free tier was discontinued Feb 2026), and CONTEXT.md defers the concrete search-provider choice. The provider abstraction (D-001) makes this a low-risk, swappable decision, but a name must be chosen before Phase 2 implementation. A time-boxed spike (TODO.md T1) evaluated candidate search APIs against: free/low-cost tier availability, ToS compatibility with an automated per-item query pattern, response format suitable for LLM extraction with a citable source URL, and simple REST + API-key auth callable from `requests`. Pricing/tier facts below were verified against current (July 2026) web sources, not memory.
- Decision: Use **Tavily** (`https://api.tavily.com/search`) as the first concrete `CostLookupProvider` search backend.
  - `COST_LOOKUP_PROVIDER` identifier string: `"tavily"`.
  - Required API-key env var: `COST_LOOKUP_API_KEY` (read directly inside `cost_lookup.py`, per the CONTEXT.md "provider-specific vars read in the service module" convention). Tavily's own SDK convention is `TAVILY_API_KEY`; we standardize on the provider-neutral `COST_LOOKUP_API_KEY` so swapping the backend later does not require renaming the secret. If desired, `cost_lookup.py` may fall back to `TAVILY_API_KEY` when `COST_LOOKUP_API_KEY` is unset.
  - Request: `POST https://api.tavily.com/search`, header `Authorization: Bearer <COST_LOOKUP_API_KEY>`, JSON body with `query` = `"<item_name> <category> replacement price"` (built from item name + category only — never notes/box/room). Use `search_depth: "basic"` (1 credit/request) and a small `max_results` (e.g. 5) to keep extraction context tight and spend minimal.
  - Response: JSON with a `results` array; each result object carries `title` (str), `url` (str), and `content` (str — a short snippet), plus a `score` (float). These map directly to the `source_title` / `source_url` / snippet fields the local Ollama extraction (D-002) needs, satisfying GOAL.md's "reject estimates without a cited source URL" hallucination guard. (`raw_content`, `favicon`, `images` are optional and not requested.)
- Rationale: Tavily gives 1,000 free API credits/month with **no credit card required** — comfortably above a single household's low-volume, budget-capped (D-006) usage, so the feature can run indefinitely at zero cost. It is purpose-built as a "web search API for AI agents": the documented Search API IS the sanctioned programmatic path, its snippet-oriented `content` field is ideal for downstream LLM extraction, and auth is a single Bearer API key usable from `requests` with no SDK dependency. Basic search is 1 credit/request; overage (if a paid plan is ever added) bills at $0.008/credit rather than hard-cutting off.
- Alternatives considered:
  - **Exa** (`https://exa.ai/pricing`): strong runner-up. Comparable free tier (~1,000 searches/month + $10 starter credit, no card), REST + API-key auth, returns title/url/text/highlights. Lost narrowly because it is oriented toward neural/semantic search rather than the keyword+snippet pattern that maps most cleanly to short product-price queries, and standard search was repriced up to $7/1,000 in March 2026 vs Tavily's cheaper credit model. Kept as the documented first fallback if Tavily's tier changes.
  - **Brave Search API** (`https://api-dashboard.search.brave.com`): its FREE tier was discontinued Feb 2026 (per GOAL.md risk table); now metered at ~$5/1,000 requests with only $5/month of prepaid credit (~1,000 searches) before the card on file is charged. Cheap in absolute terms, but (a) no true free tier remains, and (b) the credit now requires public attribution of Brave Search on the project's website/about pages — awkward for a local-first, single-household app with no public site. Rejected.
  - **SerpAPI** (`https://serpapi.com/pricing`): Google-SERP scraping model. Free plan shrank in 2026 (reports range 10–250 searches/month) and the first paid tier is $25/month for 1,000 searches — materially more expensive than Tavily/Exa for the same low volume, with no clear benefit for this use case. Rejected on cost.
- ToS / constraint notes:
  - Tavily's Acceptable Use Policy forbids scraping/harvesting "the Services" by automated means "except as expressly permitted by the Services" — this is a standard anti-scraping clause aimed at scraping Tavily's own platform, not at calling the documented Search API, which is expressly the intended programmatic interface. Normal API usage is compliant; commercial use is permitted.
  - No provider-side spending cap is guaranteed; the app-side monthly budget guard (D-006) remains the primary spend control. Staying within the 1,000 free credits/month with `search_depth: "basic"` keeps the feature free for a single household.
  - Provider remains swappable behind `CostLookupProvider` (D-001), so this choice is low-risk/reversible if Tavily's tier or ToS change — matching the churn mitigation in GOAL.md's risk table.
- Consequences: Phase 2 implementation tasks (T5) are unblocked: `cost_lookup.py` wires a Tavily client via `requests.post` to `https://api.tavily.com/search`, reading `COST_LOOKUP_API_KEY`. T15 must document `COST_LOOKUP_PROVIDER=tavily` and the `COST_LOOKUP_API_KEY` secret. Unknown/unset `COST_LOOKUP_PROVIDER` still resolves to the disabled no-op provider (D-005), so an absent key never causes network egress.
- Rollback plan: Set `COST_LOOKUP_PROVIDER=disabled` (or swap to the documented Exa fallback behind the same abstraction) — no schema or caller changes required.
- Validation plan: With `COST_LOOKUP_PROVIDER=tavily` and a valid `COST_LOOKUP_API_KEY`, a single-item lookup issues one `POST https://api.tavily.com/search` carrying only the item name + category, and the parsed `results[].{title,url,content}` feed the Ollama extraction such that an estimate is produced only when a source URL is present (tested with fixture responses, per D-002).
