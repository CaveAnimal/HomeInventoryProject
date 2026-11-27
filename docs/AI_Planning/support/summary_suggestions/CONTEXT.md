# PROJECT CONTEXT — summary_suggestions

> AI AGENT INSTRUCTIONS: This document describes the system the summary_suggestions program changes, as it actually is on 2026-11-26, and what each workstream changes. Pillar 2 of GOAL → CONTEXT → DECISIONS → TODO. Goals and scope live in [GOALS.md](GOALS.md) (APPROVED 2026-11-26). If a change is outside this context or contradicts it, stop and ask; don't improvise.

- **Status:** **APPROVED** by owner on 2026-11-26 (with DECISIONS.md).
- **Verified against:** the code on branch `docs/summary-suggestions-plan` (same app code as `main` at `c35d181`), the live database (read-only), and a test run, all on 2026-11-26.
- **Paths below** are relative to `outputs/home-inventory-app/` unless they start with the repository root.

---

## 1. Current System Overview

### Purpose
Home Inventory is a local-first FastAPI web app for one household. The user photographs containers (boxes, shelves, drawers), a **local** vision model suggests the items it sees, and the user confirms the suggestions into the inventory. Containers get QR labels that open a mobile page listing their contents. An opt-in cost lookup estimates replacement values. Everything runs on the owner's Windows PC and is used from an iPhone over the home LAN.

### Size today (measured 2026-11-26)

| Measure | Value |
|---|---|
| Python in `app/` | 2,859 lines (`main.py` 947, `vision.py` 543, `repository.py` 462, `cost_lookup.py` 459) |
| HTTP routes | 37 (HTML pages + JSON API, all in `main.py`) |
| Tests | 57: **51 pass, 6 fail** (known Windows baseline, see §4 Scenario 7) |
| Live data | 9 containers, 9 photos, 56 items, 62 detection suggestions, 3 cost estimates, 9 labels; `data/` is 47 MB |
| Migrations applied | `001_initial` … `007_app_settings` |

### Technology Stack

| Component | Technology | Version | Notes |
|---|---|---|---|
| Language | Python | 3.11 / 3.12 | `.venv` at the repository root, created by `start.ps1` |
| Web | FastAPI + Uvicorn + Jinja2 | fastapi 0.115.6, uvicorn 0.34.0, jinja2 3.1.5 | Server-rendered pages plus JSON API. No router split |
| Front end | HTML, CSS, vanilla JS | — | `app/static/` (`app.js`, `capture.css`). No build step |
| Validation | Pydantic | 2.10.4 | Request models |
| Database | SQLite | stdlib | `data/inventory.sqlite3`, foreign keys on, SQL migrations applied at startup |
| Imaging | Pillow, qrcode | 11.1.0, 8.0 | EXIF transpose + downscale **for the model only**; QR PNGs |
| Local AI (vision) | Bonsai (Ternary-Bonsai-2-27B on llama.cpp `llama-server`, OpenAI-compatible, `:1080`) | — | Default. Alternatives: Ollama (`qwen3-vl`), LM Studio, heuristic (tests only) |
| Cost lookup | Tavily search + local Bonsai/Ollama extraction | — | Off by default (`COST_LOOKUP_PROVIDER=disabled`) |
| HTTP client | `requests` | 2.32.3 | All outbound calls |
| Tests | pytest + httpx TestClient | 8.3.4, 0.28.1 | Tests use `test-data/`, never `data/` |

### Architecture

```text
iPhone / browser ──HTTP :1800──▶ app/main.py (all routes)
                                   │
         ┌─────────────────────────┼──────────────────────────┐
         ▼                         ▼                          ▼
  repository.py             services/vision.py        services/cost_lookup.py
  (flat SQL functions)      (VisionProvider,          (CostLookupProvider,
         │                   normalize_detection)      guardrails, budget)
         ▼                         │                          │
  data/inventory.sqlite3           ▼                          ▼
  data/photos/  data/labels/   llama-server :1080        Tavily API (opt-in)
                               (or Ollama / LM Studio)    + local LLM extraction

  scheduler.py ─(in-process thread, DEEP_SCAN_HOUR=2)─▶ nightly_reprocess.py
```

### Data flows today

**Capture (phone or desktop upload)**, `POST /api/boxes/{id}/photos` → `save_photos_and_detect()` ([main.py:532](../../../../outputs/home-inventory-app/app/main.py#L532)):
1. The **full-size upload is written to `data/photos/<uuid>.<ext>` unchanged** ([main.py:551-553](../../../../outputs/home-inventory-app/app/main.py#L551-L553)). iPhone originals average 5.35 MB.
2. `vision.prepare_image_bytes()` makes an upright, 1280 px JPEG **in memory** for the model. Nothing resized is saved.
3. The provider returns JSON → `normalize_detection()` enforces the strict contract → rows land in `detection_suggestions` (`pass_type='live'`).
4. The user confirms or dismisses (`POST /api/detections/confirm-batch`). Only confirmation creates `box_items`.

**Import inbox**, `/import` page → `POST /api/import…` ([main.py:458-466](../../../../outputs/home-inventory-app/app/main.py#L458-L466)):
- Files in `data/import-inbox/` are **moved** (`shutil.move`) into `data/photos/`, so they leave the inbox. Then detection runs as above.

**Deep scan**: `scheduler.py` runs `nightly_reprocess.py` once at `DEEP_SCAN_HOUR` when armed. It re-detects each stored photo once per model label (Bonsai with thinking on), **adding** `pass_type='reprocess'` suggestions without replacing live ones.

**QR labels**: `target_url = request.url_for("public_box_page", public_id=…)` ([main.py:331](../../../../outputs/home-inventory-app/app/main.py#L331)). The label encodes **whatever host and port the request that created it used**, plus `/box/{public_id}`.

**Cost estimate**: one item per request; query built from `item_name` + `category` only; excluded categories are blocked before any network call; results are appended to `cost_estimates` (insert-only).

**Backup (owner's install only, outside the app)**: [backup-data.ps1](../../../../backup-data.ps1) at the repository root runs weekly (Sunday 3 AM scheduled task). It snapshots the DB with SQLite's online backup API, runs `PRAGMA integrity_check`, copies photos/labels/inbox, skips the run if nothing changed, and keeps the newest 30 snapshots in `D:\HomeInventoryBackups`. **Not encrypted; same media type (HDD); no off-site copy.**

### Data model (as in the live database)

```text
boxes                 id, public_id (QR), name, container_type, parent_box_id → boxes,
                      notes, tags, size, stack_position, inaccessible
box_locations         box_id (1:1), room_name, north_ft, east_ft, elevation_ft
box_photos            box_id, filename, original_filename, content_type,
                      deep_scan_model, deep_scanned_at
detection_suggestions box_id, photo_id → box_photos, item_name, quantity, confidence,
                      category, notes, status (suggested|confirmed|dismissed),
                      source_model, pass_type (live|reprocess)
box_items             id, box_id, item_name, normalized_name, quantity,
                      status (confirmed|likely = AI certainty), confidence, category,
                      notes, tags, priority, created_at, updated_at,
                      standard_system, standard_code, standard_label
                      ── no lifecycle status, no photo link, no brand/model/serial
cost_estimates        box_item_id, estimated_cost_usd, quantity, confidence,
                      source_title, source_url, created_at   (insert-only)
labels                box_id, filename, target_url, format
edit_history          entity_type, entity_id, action, before_json, after_json
app_settings          key/value (deep-scan armed flag, last run date)
schema_migrations     version, applied_at
```

There is **no household concept, no user table and no authentication**. Every route is open to anyone on the LAN.

---

## 2. Key Files and Their Roles

| File | Purpose | Changed by |
|---|---|---|
| `app/main.py` | All 37 routes, upload handling, QR generation, CSV/JSON export, dashboard | WS-0 (CSV, totals), WS-1, WS-2, WS-3, WS-4, WS-10 (status), WS-11 (upload + import paths) |
| `app/repository.py` | Flat SQL helper functions; `record_history()` | Every feature workstream |
| `app/database.py` | `connect()`, `migrate()` (sorted `migrations/*.sql`, tracked in `schema_migrations`), demo seed | WS-4 if per-household files are chosen (PD-3) |
| `app/settings.py` | Paths and env config (`HOME_INVENTORY_DATA`, `HOME_INVENTORY_DB`, `VISION_PROVIDER`, `COST_LOOKUP_*`) | WS-7 (read cost limit at call time), WS-10, WS-11 settings |
| `app/services/vision.py` | Provider classes, `normalize_detection()`, image prep, tiling | WS-11 reuses its EXIF/resize code for the normalizer; **detection contract must not change** |
| `app/services/cost_lookup.py` | Cost providers, guardrails, budget guard | WS-0 QW-5 (count attempts), WS-5 (resale reuse), WS-7 |
| `app/services/search.py` | Filtered search with SQL `LIKE`, synonyms, difflib similar items | WS-1 (status filter), WS-7 (FTS5) |
| `app/services/labels.py` | QR PNG generation | WS-4 (portable label scheme, PD-4) |
| `app/scheduler.py`, `app/nightly_reprocess.py` | Deep scan | WS-11 (must run on working copies); possibly WS-10 (backup schedule pattern) |
| `app/templates/*.html` | `dashboard`, `capture`, `import`, `container_detail`, `search`, `labels`, `admin`, `boxes`, `new_box`, `base` | WS-0, WS-1, WS-3, WS-10, WS-11 |
| `migrations/001…007` | Schema history | New files `008_…` onward, additive only |
| `tests/test_core.py`, `test_llm_vision.py`, `test_cost_lookup.py`, `test_nightly_reprocess.py` | Test suite; each sets `HOME_INVENTORY_DATA` to `test-data/` before import | WS-0 QW-4 (teardown fix); new tests per workstream |
| `scripts/vision_eval/` | Golden-set accuracy harness (`eval_vision.py`, `golden_set.json`) | SP-2, SP-7, SP-10, WS-11 acceptance |
| `README.md` | App setup | WS-0 QW-3 (still says port 8000 and the old path) |
| Repo root: `start.ps1`, `stop.ps1`, `start.cmd`, `stop.cmd` | Create `.venv`, install, migrate, start on `0.0.0.0:1800`; boot task runs as SYSTEM | WS-9 (replaced by an installer) |
| Repo root: `backup-data.ps1`, `backup-e-drive.ps1` | Owner's backup scripts (tracked since 2026-11-26) | WS-0 QW-6, then replaced by WS-10 |

---

## 3. Hard Constraints (DO NOT VIOLATE)

Inherited and program constraints from [GOALS.md §1](GOALS.md). Restated here because they decide how code is written.

| Constraint | Source | Practical effect |
|---|---|---|
| Photos and inventory never leave hardware the household controls; vision is local | llm_vision D-001 | No cloud vision, rendering, OCR or backup service that can read data |
| AI output is a suggestion until a person confirms it | llm_vision D-002 | New AI-read fields (WS-2) go into suggestions, never straight into `box_items` |
| Every vision result passes `normalize_detection()` | llm_vision D-003 | Don't loosen or bypass the contract |
| Cost lookup rules (provider abstraction, local extraction, one item per request, kill switch, budget guard, excluded categories) | cost_of_replacement D-001…D-007 | WS-5 resale lookup reuses the same pipeline and rules |
| `cost_estimates` is insert-only | cost_of_replacement D-004 | "Latest" is a query, never an update |
| **Migrations are additive only** | Pattern 001–007 | New tables, or new columns with defaults. No drops, renames or type changes on existing columns |
| **Back up `outputs/home-inventory-app/data/` before any branch switch, checkout, reset or migration** | Incident 2026-11-23 | Every TODO task that migrates or touches git state includes this step |
| Every user-visible change writes `edit_history` | `record_history()` pattern | Status, loan, verify, settings and backup-config changes included |
| No telemetry and no phone-home | PD-10 | Licensing, updates and health checks work offline |
| **Every backup copy is encrypted** (no opt-out in the first release) | PD-11; owner decision 2026-11-26, [BL-007](../../backlog/BL-007-optional-local-backup-encryption.md) | WS-10 has no "encryption off" setting |
| **The app keeps working copies, never full-size uploads** | PD-13 | After WS-11, no code path may write the uploaded bytes to disk |
| Wording never says the app deletes or discards user photos | [USER_OWNED_ORIGINALS.md §6](USER_OWNED_ORIGINALS.md) | Say "never saves the full-size file; your original stays with you" |
| Tests must never touch `data/` | Existing test convention | New test files set `HOME_INVENTORY_DATA` / `HOME_INVENTORY_DB` to `test-data/` before importing the app |

---

## 4. Current Behavior (Baseline Scenarios)

These are the "before" pictures that workstream acceptance tests compare against.

| # | Scenario | Today | After |
|---|---|---|---|
| 1 | Export CSV | Columns: item, quantity, status, confidence, box, room, north/east/elevation, tags, notes ([main.py:943](../../../../outputs/home-inventory-app/app/main.py#L943)). No category, container path or cost | QW-1 appends category, container path, latest estimate + date; existing column order kept |
| 2 | Value of a container or the house | Estimates shown per item only; no totals | QW-2 totals with child rollup and unestimated count; WS-3 report totals by room and category |
| 3 | "Is it still here?" | No lifecycle field. `status` means AI certainty (`confirmed`/`likely`) | WS-1 adds `lifecycle_status` (ten values), loans, last verified, verify mode |
| 4 | Upload a photo | Full-size original saved to `data/photos/` | WS-11: only a 2,400 px working copy is saved (GPS removed, date taken and filename recorded) |
| 5 | Import from inbox | File **moved** out of the inbox into `data/photos/` | WS-11: inbox file left in place, marked imported by name + fingerprint, working copy saved |
| 6 | QR label after an IP change or a move to another install | Breaks: the label holds the creating request's host, e.g. `http://192.168.x.x:1800/box/<public_id>` | WS-4 portable scheme (PD-4), bulk regenerate |
| 7 | Test suite on Windows | 51 pass, 6 fail, with **two different causes** (re-checked 2026-11-26; the summary called them all teardown noise). **(a) 3 real test/code mismatches:** `save_photos_and_detect()` now refuses non-LLM providers ([main.py:539-541](../../../../outputs/home-inventory-app/app/main.py#L539-L541)), but these tests run with `VISION_PROVIDER=heuristic` and expect suggestions: `test_http_create_box_generates_qr_and_suggestions` (`test_core.py:60`), `test_photos_endpoint_reports_vision_error_but_saves_photo` (`test_llm_vision.py:217`), `test_end_to_end_mobile_capture_confirm_and_dismiss` (`test_llm_vision.py:266`). **(b) 3 SQLite file-lock `PermissionError`s** on `test-data/test.sqlite3` (`test_search_page_mentions_exact_location`, `test_public_qr_box_page_lists_items`, `test_confirm_is_idempotent_and_dismissed_cannot_be_confirmed`); some may be knock-on effects of (a) leaving connections open | QW-4: fix (a) with a test-only provider path or updated tests (a decision, not a mask), fix (b) by closing connections; 0 failures, or only failures with a written, accepted reason |
| 8 | Failed cost lookup | Uses a search credit but isn't counted toward `COST_LOOKUP_MONTHLY_LIMIT` | QW-5 counts attempts |
| 9 | Backup | Owner's weekly script to `D:` (HDD → HDD, unencrypted, local only). Customers would have nothing | QW-6 adds an encrypted off-site copy for the owner; WS-10 builds the in-app backup for everyone |
| 10 | Access control | None; anyone on the LAN can edit or delete | WS-4 logins and roles |
| 11 | Item → photo evidence | Item links to its container only. `detection_suggestions.photo_id` exists, but confirming doesn't carry it into `box_items` | WS-2 keeps the link; WS-7 backfills where SP-1 shows it's unambiguous |

---

## 5. Required Knowledge

### Domain concepts

| Concept | Meaning | Where to learn |
|---|---|---|
| Container (`boxes`) | Anything that holds items: box, shelf, drawer, room-level spot. Can nest (`parent_box_id`) | `migrations/001_initial.sql`, `002_container_hierarchy.sql` |
| Suggestion vs item | AI output (`detection_suggestions`) vs confirmed inventory (`box_items`) | llm_vision DECISIONS D-002 |
| AI certainty vs lifecycle | `box_items.status` = how sure the AI was. `lifecycle_status` (WS-1) = where the thing physically is | PD-2 |
| Live vs deep scan | Fast pass at capture time vs slow nightly pass that adds suggestions | `nightly_reprocess.py` |
| Working copy vs original | 2,400 px JPEG the app keeps vs the user's own full-size photo | [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) |
| Household | One family's inventory; today the whole database. Becomes an explicit owner of every row in WS-4 | PD-3, SP-4 |
| 3-2-1 backup | 3 copies, 2 media types, 1 off-site | [DATA_PROTECTION.md](DATA_PROTECTION.md) |

### Code patterns to follow

| Pattern | Where | Rule for new code |
|---|---|---|
| Provider abstraction | `vision.py`, `cost_lookup.py` | Base class + `get_*_provider()` from an env var, unknown value falls back to a safe no-network default. Use it for any new pluggable piece (PDF renderer, backup engine) |
| Flat repository functions | `repository.py` | Plain functions taking `conn`, returning dicts via `rows()`/`row()`. No ORM |
| Numbered SQL migrations | `migrations/` | Next file is `008_<name>.sql`. Additive, idempotent where possible |
| Env config read at call time | `settings.reprocess_vision_model()` | Prefer reading env when needed (the cached `COST_LOOKUP_MONTHLY_LIMIT` is a known gap, WS-7) |
| User-safe errors | `VisionError`, `CostLookupError` | Catch transport errors, re-raise a domain error with a message safe to show |
| History | `record_history(conn, entity, id, action, before, after)` | Call it on every user-visible change |
| Test isolation | top of each test file | Set data/DB env vars to `test-data/` and the provider to a safe value **before** importing `app` |

### Integration points

| System | Use | Constraint |
|---|---|---|
| llama.cpp `llama-server` `:1080` (Bonsai) | Vision, deep scan, cost extraction | Local only. Needs a strong GPU (SP-7 tests smaller models) |
| Ollama `:11434`, LM Studio `:1234` | Alternative local providers | Local only |
| Tavily API | Cost lookup search | Opt-in, one item per request, budget-capped |
| iPhone Safari over LAN | Capture, QR pages | HTTP on `:1800`. Camera behavior is tested in SP-10 |
| Windows Task Scheduler | App start at boot (SYSTEM), weekly backup | WS-10 must work under the SYSTEM account (SP-9 item 4) |
| restic + rclone (proposed) | Encrypted backup engine | Not installed yet. SP-9 confirms |

---

## 6. Target State (After the Program)

### What changes, by workstream

| WS | Phase | Schema | Code / UI | Notes |
|---|---|---|---|---|
| WS-0 Quick wins | 1 | None (QW-5 may use `cost_estimates` or a small attempts table) | CSV columns, value totals, README, test teardown fix, attempt counting, encrypted off-site copy in `backup-data.ps1` | **QW-6 first** (owner decision, 2026-11-26) |
| WS-1 Status + loans | 2 | `box_items.lifecycle_status` (default `in_home`), `last_verified` on items and containers, new `loans` table | Status UI, Lent-out panel, search filter, QR page status, verify mode | PD-1, PD-2 |
| WS-11 Working copies | 3 | `box_photos`: date taken, fingerprint, `is_working_copy` (or similar); imported-file register for the inbox | One normalizer for all upload paths; capture page Library-first; Quick Photo prompt; inbox no longer moved; optional compaction tool | PD-13…15, SP-10 |
| WS-10 Data protection | 4 | Backup config/status in `app_settings` or a new table | Bundled engine, USB + off-site repositories, Credential Manager key, Recovery Sheet, dashboard status, restore wizard; owner's install migrates off `backup-data.ps1` | PD-11, PD-12, SP-9; encryption always on |
| WS-3 Client report | 5 | None expected | Local HTML → PDF report (insurance, quick-find), adjuster CSV/XLSX | PD-7, SP-3 |
| WS-2 Insurance records | 6 | Item fields (brand, model, serial, purchase, condition, high-value), item → photo link, evidence photos | AI-read suggestions for stickers | SP-1, SP-2 |
| WS-4 Households + accounts | 7 | Households and users (column or per-file, PD-3) | Login, roles, transfer package, portable QR | PD-3, PD-4, PD-8, SP-4 |
| WS-5 Downsizing | 8 | Disposition, recipient, resale estimates | Downsizing views and report variant | PD-6 |
| WS-6 Field efficiency | 9 | Capture queue | Offline queue, smaller model or remote inference, room progress | SP-6, SP-7 |
| WS-9 Licensing + distribution | 10 | License state (local) | Installer, first-run, offline license, safe updates, user guide | PD-10, SP-7, SP-8 |
| WS-7 Hardening | alongside | FTS5 index | Search on FTS5, config fixes, photo-link backfill | — |
| WS-8 Business readiness | parallel | — | Owner checklist, not code | — |

### What will NOT change
- Local-only AI and the confirm-before-inventory flow.
- `normalize_detection()` and the detection contract.
- Existing tables keep their columns and meaning. In particular `box_items.status` keeps meaning AI certainty.
- Existing photo files, unless the owner runs the PD-15 compaction tool after a verified backup.
- The provider-abstraction, flat-repository and numbered-migration patterns.
- SQLite as the database.

### Migration path

`Phase 0` (this document, DECISIONS.md, TODO.md; spikes SP-1, SP-3, SP-7) → `WS-0` → `WS-1` → `WS-11` (SP-10 first) → `WS-10` (SP-9 first) → `WS-3` → `WS-2` → `WS-4` → `WS-5` → `WS-6` → `WS-9`, with WS-7 alongside and WS-8 in parallel. Each phase is refined in TODO.md at the end of the previous one.

---

## 7. Open Questions for Owner Review

1. ~~**QW-6 first?**~~ **Yes** (owner, 2026-11-26).
2. ~~**Track the backup scripts?**~~ **Both committed** (owner, 2026-11-26).
3. **Photo count:** the docs mention 11 photos in the owner's install; the database has 9 today. No action needed unless that's unexpected.

---

## 8. Reference Materials

- [GOALS.md](GOALS.md): approved goals, constraints, workstreams, PD-1…PD-15, spikes.
- [DATA_PROTECTION.md](DATA_PROTECTION.md): PD-11/12 analysis. [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md): PD-13…15 analysis and capture workflow diagram.
- [docs/notes/summary/README.md](../../../notes/summary/README.md): the 2026-11-23 application review this program comes from.
- [llm_vision/DECISIONS.md](../llm_vision/DECISIONS.md) (D-001…D-003) and [cost_of_replacement/DECISIONS.md](../cost_of_replacement/DECISIONS.md) (D-001…D-007): inherited decisions.
- [llm_vision/abstract_goal_context_decisions_todo.md](../llm_vision/abstract_goal_context_decisions_todo.md): the framework.
- [Backlog](../../backlog/README.md): BL-001…BL-007.
