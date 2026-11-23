# PROJECT CONTEXT

> AI AGENT INSTRUCTIONS: This document defines implementation context for the cost_of_repair (estimated replacement cost) workflow. If a change is outside this context, request clarification before implementation.

## Current System Overview

### Purpose
The Home Inventory app is a local-first FastAPI application that stores containers, photos, detections, and confirmed items in SQLite. It already has a provider-abstraction pattern for local vision inference (Ollama) and a privacy-first posture (see [DECISIONS.md](../llm_vision/DECISIONS.md) D-001). This feature adds an opt-in cost-lookup capability without breaking that posture.

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Language | Python | 3.x | Runtime for app and services |
| Framework | FastAPI + Jinja2 | fastapi==0.115.6, jinja2==3.1.5 | Server-rendered pages with JSON APIs |
| Data validation | Pydantic | pydantic==2.10.4 | Request/response models |
| Outbound HTTP client | `requests` | requests==2.32.3 | Used by `OllamaVisionProvider`; reuse for the new search provider (`httpx` is present only as a transitive test-client dependency, not used directly in `app/`) |
| Database | SQLite | file-based | Local-first, migrations in SQL, applied by `app/database.py:migrate()` |
| LLM Runtime | Ollama | local install | `llama3.2-vision` used for image detection today; text-only Ollama model to be used for cost-extraction reasoning |
| Test framework | pytest | pytest==8.3.4 | `tests/test_core.py`, `tests/test_llm_vision.py` establish conventions |

### Architecture Overview
- Route and page orchestration: `outputs/home-inventory-app/app/main.py` (~658 lines, all routes live here, no router/blueprint split)
- Data access and persistence: `outputs/home-inventory-app/app/repository.py` (flat module of functions taking `conn: sqlite3.Connection`, no ORM/classes)
- Config: `outputs/home-inventory-app/app/settings.py` (plain module-level `os.environ.get(NAME, default)` constants)
- Vision provider abstraction (pattern to mirror): `outputs/home-inventory-app/app/services/vision.py`
- In-app inventory search (NOT an external web client, do not confuse with the new search provider): `outputs/home-inventory-app/app/services/search.py`
- Canonical category list: `outputs/home-inventory-app/app/categories.py` (`HOUSEHOLD_CATEGORIES`)
- Migrations: `outputs/home-inventory-app/migrations/*.sql`, applied in sorted filename order, tracked in `schema_migrations` table

Data flow today (vision, for comparison):
1. User uploads photo → `main.py` calls `services.vision.get_provider().detect(...)`.
2. Provider returns detections; `repository.py` stores them as `detection_suggestions`.
3. User confirms suggestions; confirmed rows become `box_items`.

Data flow to be added (cost lookup):
1. User triggers an estimate for one confirmed `box_items` row (or a batch, issued as N separate single-item requests) from the container/item page.
2. `services/cost_lookup.py` provider fetches search results for `item_name` + `category` only (no photos, no box/room, no notes).
3. A local Ollama text model extracts a structured estimate (`estimated_cost_usd`, `confidence`, `source_title`/`source_url`) from the search results.
4. `repository.py` appends a row to `cost_estimates` (history, never overwritten).
5. UI displays the latest estimate with age, confidence, and source link.

### Key Files and Their Roles

| File Path | Purpose | Change Expected? |
|-----------|---------|------------------|
| `outputs/home-inventory-app/app/main.py` | API endpoints and page routes | Yes - add single-item and batch cost-estimate endpoints, read endpoints |
| `outputs/home-inventory-app/app/services/vision.py` | Existing provider abstraction (`VisionProvider`, `get_provider()`, `VisionError`, `normalize_detection()`) | No - reference pattern only, do not modify |
| `outputs/home-inventory-app/app/services/cost_lookup.py` | NEW - `CostLookupProvider` base class, search + local-LLM extraction, `get_cost_provider()` factory, `CostLookupError`, normalize function | Yes - new file |
| `outputs/home-inventory-app/app/settings.py` | Env-driven config | Yes - add `COST_LOOKUP_PROVIDER` (mirrors `VISION_PROVIDER` kill-switch precedent) and a budget-cap setting |
| `outputs/home-inventory-app/app/repository.py` | Persistence helper functions | Yes - add `add_cost_estimate()`, `list_cost_estimates_for_item()`, `latest_cost_estimate()` |
| `outputs/home-inventory-app/app/categories.py` | `HOUSEHOLD_CATEGORIES` list | No - reference only, to build the default exclusion list (`Documents & Paper`, `Sentimental / Keepsakes`) |
| `outputs/home-inventory-app/migrations/004_cost_estimates.sql` | NEW - `cost_estimates` table + index, following `001_initial.sql`'s full-DDL style | Yes - new file |
| `outputs/home-inventory-app/tests/test_cost_lookup.py` | NEW regression tests | Yes - new file, following `test_llm_vision.py` convention (set provider env var to a safe/offline value before import) |

### Current Behavior (Baseline)
Scenario 1: Confirmed item exists with no cost data
- Current behavior: `box_items` has no cost/price concept at all.
- Expected after change: item detail view offers an "Estimate cost" action; absence of an estimate is a normal, non-error state.

Scenario 2: Vision provider selection
- Current behavior: `services/vision.py:get_provider()` reads `VISION_PROVIDER` (default `"ollama"`), returns `OllamaVisionProvider` or `HeuristicVisionProvider`; unrecognized values fall through to heuristic (no network).
- Relevance: `get_cost_provider()` must follow the identical fallback-to-safe-default shape, with `COST_LOOKUP_PROVIDER=disabled` (or an unset/unknown value) resulting in zero network egress.

## Hard Constraints (DO NOT VIOLATE)

| Constraint | Rationale | Impact |
|------------|-----------|--------|
| Never send photos to any external service | Privacy stance ([DECISIONS.md](../llm_vision/DECISIONS.md) D-001) | Search query built ONLY from `item_name` + `category` strings |
| Never batch multiple items into one outbound search request | Prevents leaking full-inventory shape to a third party | Batch UI action fans out to N sequential/individual provider calls |
| Local Ollama performs the extraction/reasoning step; no cloud LLM | Matches existing local-first LLM investment | `cost_lookup.py` calls Ollama the same way `vision.py`'s `OllamaVisionProvider` does (`requests.post` to local Ollama HTTP API) |
| Feature must be disable-able via one env var | Matches `VISION_PROVIDER=heuristic` kill-switch precedent | `COST_LOOKUP_PROVIDER=disabled` must produce a no-op provider, no exceptions raised |
| `Documents & Paper` and `Sentimental / Keepsakes` excluded from lookup by default | Business requirement (privacy-sensitive categories) | Exclusion check happens before any network call is made, not just in the UI |
| Estimates are historical, never overwritten in place | Auditability of price changes over time | `cost_estimates` is insert-only; "latest" is a query, not a column update |
| Existing SQLite data must remain valid | Preserve inventory history | New migration only adds a new table; no changes to `box_items` columns |

## Required Knowledge

### Domain Concepts
| Concept | Description | Why It Matters | Where to Learn |
|---------|-------------|----------------|-----------------|
| `box_items` | Confirmed inventory item row | Cost estimate is keyed to one `box_items.id` | `outputs/home-inventory-app/migrations/001_initial.sql`, `003_item_category_standards.sql` |
| `HOUSEHOLD_CATEGORIES` | Canonical category enum used across the app | Determines default lookup-exclusion set | `outputs/home-inventory-app/app/categories.py` |
| Cost estimate history | Append-only record of a price lookup at a point in time | Source of the "estimated replacement cost" feature | This document + GOAL.md |

### Technical Patterns in This Codebase
| Pattern | Where Used | How It Works | Why We Use It |
|---------|------------|---------------|-----------------|
| Provider abstraction | `services/vision.py` | Base class + `get_provider()` factory keyed off an env var, safe fallback on unknown value | Mirror exactly for `services/cost_lookup.py` / `get_cost_provider()` |
| Flat repository functions | `repository.py` | Plain functions taking `conn: sqlite3.Connection`, returning `int`/`dict`/`list[dict]` via `rows()`/`row()` helpers; `record_history()` used for audit trails elsewhere | New cost-estimate persistence functions append to this same file, reuse `record_history()` idiom if applicable |
| Numbered SQL migrations | `migrations/*.sql` | `NNN_snake_case.sql`, applied in sorted order, tracked in `schema_migrations` | Next file is `004_cost_estimates.sql` |
| Env var config, no `BaseSettings` | `settings.py` | Module-level `os.environ.get(NAME, default)` constants; provider-specific vars (URLs, keys) read directly in the service module, not centralized | Add `COST_LOOKUP_PROVIDER` to `settings.py`; add provider-specific vars (search API key, budget cap) inside `cost_lookup.py` |
| `requests`-based HTTP calls | `services/vision.py` (`OllamaVisionProvider`), `main.py` | `requests.post(...)`, exceptions caught as `requests.exceptions.*` and re-raised as a domain error (`VisionError`) | New search provider and Ollama-extraction call both use `requests`, raise `CostLookupError` on failure |

### Integration Points
| System/Service | Purpose | How We Interact | Constraints |
|----------------|---------|-------------------|-------------|
| Ollama API (`/api/generate`) | Local LLM extraction of structured cost data from search results | HTTP POST via `requests`, same host/pattern as vision calls | Model must be reachable from app host; text-only model, not the vision model |
| External web search API (provider TBD - see DECISIONS.md) | Source of current market price data | HTTP GET/POST via `requests`, query = item name + category only | Provider ToS/pricing may change (mitigation in GOAL.md risk table); abstracted behind `CostLookupProvider` so the provider is swappable |
| SQLite | Persistence of `cost_estimates` history | SQL via `repository.py` helpers | New table only; must preserve migration discipline (insert-only, no destructive changes to `box_items`) |

## Target State (After Project Completion)

### What Will Change
- New `app/services/cost_lookup.py` module with a provider abstraction mirroring `vision.py`.
- New `cost_estimates` table (migration `004_cost_estimates.sql`) storing history, not just latest value.
- New API endpoints for single-item estimate, batch (fan-out) estimate, and reading stored estimates.
- Container/item detail UI gains an "Estimate cost" action and a display of the latest estimate + history.
- `settings.py` gains `COST_LOOKUP_PROVIDER` and a budget-cap env var.

### What Will NOT Change
- Existing vision/capture/confirm flow ([llm_vision](../llm_vision/) docs) remains untouched.
- `box_items` table schema is not modified.
- Vision provider abstraction (`services/vision.py`) is not modified, only referenced as a pattern.
- No cloud LLM is introduced anywhere in the app.

### Migration Path
Current state (no cost data) → Phase 1 provider + config scaffolding → Phase 2 persistence + API → Phase 3 privacy guardrails + budget guard → Phase 4 UI integration → Phase 5 tests + docs → Target state
- Phase 1: `cost_lookup.py` abstraction, `settings.py` additions, `004_cost_estimates.sql`.
- Phase 2: `repository.py` functions, single/batch API endpoints.
- Phase 3: category/item opt-out enforcement, monthly budget guard.
- Phase 4: item/container detail page UI for triggering and displaying estimates.
- Phase 5: `tests/test_cost_lookup.py`, README/operational doc updates.

## Reference Materials

### Internal Documentation
- `docs/AI_Planning/support/cost_of_repair/GOAL.md`: target outcomes, scope boundaries, constraints, risk assessment.
- `docs/AI_Planning/support/llm_vision/DECISIONS.md` D-001: precedent for local-first LLM privacy stance this feature must uphold.
- `outputs/home-inventory-app/app/services/vision.py`: the provider-abstraction pattern to mirror.
- `outputs/home-inventory-app/README.md`: current app behavior and setup.

### External Resources
- Ollama docs for text-generation (non-vision) models: prompt/response shape for structured extraction.
- Chosen search provider's API docs (to be selected in DECISIONS.md; note Brave's free tier was discontinued Feb 2026, informing provider choice).

### Key People/Contacts
- Product owner/user: defines acceptance for privacy guardrails, budget cap defaults, and which categories are excluded.
