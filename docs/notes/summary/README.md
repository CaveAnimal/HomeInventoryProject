# Home Inventory (HIP-001): Application Summary

*Reviewed 2026-11-23, against `main` at commit `c35d181`.*

---

## 1. Executive Summary

**What it is.** Home Inventory is a local-first web application that turns phone photos into a searchable record of everything in a home. You photograph a box, drawer, shelf or room. A local AI vision model lists the items it sees, with counts and categories. You confirm the list, the app prints a QR label for the container, and from then on any item can be found by searching for it. The result shows the item's room, its nested location ("Garage → Tool chest → Top drawer") and its position measured in feet from the walls. If the web search option is turned on, confirmed items can also get an estimated replacement cost with a cited source, for insurance records.

**What makes it different.**

| Advantage | Why it matters |
|---|---|
| **Private by design** | Photos never leave the house. Item recognition runs on a local AI model (Bonsai 27B through llama.cpp, or Ollama). The optional cost lookup sends only an item's name and category, one item per request. This is a strong selling point for families wary of putting the contents of their home in someone else's cloud. |
| **Photo → item list in seconds** | Live capture takes about 7 s per photo. An optional overnight "deep scan" re-reads every photo with a slower, more thorough setting to catch small items. |
| **Human-in-the-loop accuracy** | The AI only *suggests*. Nothing enters the inventory until a person confirms it, and dismissed suggestions are kept for audit. |
| **Find anything, fast** | Forgiving search with partial matches, synonyms ("cord" also finds "cable") and similar-name suggestions. Filters for room, tag, category and confidence. Results show the full container path and coordinates. |
| **Works from any phone, no app install** | The capture page opens the phone's camera straight from Safari. Photos synced from Ray-Ban Meta smart glasses can be imported in batches. |
| **QR labels** | Every container gets a QR code. Scanning it opens a mobile page showing what's inside and where the container lives. Labels print one at a time or four per page. |
| **Nested containers** | House → room → shelf → tote, or tool chest → drawer. This matches how people actually store things. |
| **Insurance-grade evidence trail** | Photos are kept as evidence. Every create, edit, move and merge is recorded in an edit history. Cost estimates are insert-only history with source URLs, never overwritten. |
| **Data ownership** | One SQLite file plus a photos folder. JSON/CSV export. A weekly backup script with integrity checks and retention. |

**Fit with the side-hustle idea.** The suggested business is to photograph a family's belongings and use AI to catalog and value them into a report, for insurance, for downsizing, and (your addition) for finding things and tracking loans. The current application already covers most of the *capture → catalog → find* engine. That is the hard, differentiating part.

What it does **not** yet have is the *service-business* layer:

1. **A separate inventory per client household.** Today it holds one household.
2. **A polished, client-ready PDF report** with photos, totals by room and category, and replacement values.
3. **Item status and loan tracking:** in home / loaned to X / donated / sold / given to heir / missing.
4. **Insurance-specific fields:** brand, model, serial number, purchase date and price, receipts.
5. **Login and access control**, so data is not open to anyone on the network.
6. **Labels that survive moving between homes.** QR codes currently encode the host machine's LAN address.

**Recommendation.** The core is sound and the privacy story is a real market differentiator, so it is worth pursuing. Roughly **4–6 focused development sprints** (outlined in §4) would turn it from a personal tool into something you could deliver to a paying client: client workspaces, item status and loans, insurance fields, PDF reports, auth, and portable labels. Start with the **PDF report** and **status/loan tracking**. Those are what a client actually sees and pays for, and both can be built on the existing schema without disruption.

---

## 2. Features in Detail (User View)

### 2.1 Capture
- **Mobile capture (`/capture`)**: create a container inline (a QR label is generated automatically) or choose an existing one. Take a photo, see the AI's item list on the same page, uncheck wrong items, fix counts, then tap **Confirm Selected Items**.
- **Desktop create (`/boxes/new`)**: create a container from one or more photos, set its location, and choose a parent container.
- **Batch import (`/import`)**: drop photos into an inbox folder (for example from smart glasses or a camera roll export). Select them, attach them to an existing or new container, and get **one deduplicated list**: the same item seen in three photos becomes one entry with a summed quantity.
- **Add more photos later**: each new photo produces new suggestions for that container.
- **Graceful failure**: if the AI server is down or returns garbage, the photo is still saved and the user sees an actionable message.

### 2.2 Organize
- **Containers of any type**: box, room, shelf, drawer, tool chest, bag, safe, vehicle, and so on, nested to any depth.
- **Location for every container**: room name, distance from the north wall, distance from the east wall, and elevation (feet). Also a size, a stack position ("floor, behind tool chest") and an **inaccessible** flag.
- **Items**: name, quantity, status (`confirmed` / `likely`), AI confidence, category, tags, notes and priority. Optional hidden mapping to public product standards (UNSPSC / GS1).
- **15 practical household categories**, including *Donate / Sell* and *Sentimental / Keepsakes*, plus 20 standard room names. Rooms you add yourself are remembered.
- **Item operations**: edit, move to another container, merge duplicates, delete. All are recorded in history.

### 2.3 Find
- **Search (`/search`, dashboard search bar)**: partial and normalized matching (ignores words like "the", "of" and "for"), a synonym list, and "did you mean" similar items. Filters for room, tag, category and minimum confidence. Results rank priority and confirmed items first.
- **QR scan**: an iPhone camera scan opens `/box/{public_id}`, a mobile-friendly page showing the container's contents, photos and exact location.
- **Dashboard**: container counts per room, recent containers, the phone URL to use on the LAN, and live AI model status.

### 2.4 Value (opt-in)
- **Estimate cost** for one item, or **Estimate all** for a container. A Tavily web search finds current prices. The local model extracts a structured estimate with a confidence score and a source link. Estimates without a verifiable source URL are rejected.
- **Privacy guardrails**, enforced before any network call: *Documents & Paper* and *Sentimental / Keepsakes* are excluded, and a per-item `no-cost-lookup` tag opts an item out. Each request carries one item. A monthly budget cap applies (default 50 lookups).
- **Kill switch**: unset `COST_LOOKUP_PROVIDER` and the feature makes zero network calls.

### 2.5 Protect
- **Export**: JSON (containers, items, photos, locations, history) and CSV (items with location).
- **Backups**: `backup-data.ps1` takes a consistent SQLite online backup, runs an integrity check, copies photos, labels and the inbox, creates a snapshot only when something changed, and keeps the last 30. It runs as a weekly scheduled task to `D:\HomeInventoryBackups`. `backup-e-drive.ps1` covers the drive as a whole.
- **Edit history** for boxes, items, locations, labels and detections.

### 2.6 Operate
- `start.ps1` / `stop.ps1` (plus `.cmd` wrappers) set up the virtualenv, run migrations, start the server on `0.0.0.0:1800`, and choose the vision provider (`-VisionProvider bonsai|ollama`). The app runs at boot as a SYSTEM scheduled task.
- **Admin page (`/admin`)**: export buttons, and an "arm tonight's deep scan" toggle with status (model, photos pending, last run).

---

## 3. Technical Details

### 3.1 Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.115 + Uvicorn, server-rendered Jinja2 templates |
| Front end | Plain HTML/CSS/vanilla JS (`app.js`, `capture.css`). No build step |
| Database | SQLite (`data/inventory.sqlite3`), foreign keys on, plain-SQL migrations applied automatically at startup |
| Imaging | Pillow (EXIF rotation fix, downscale to 1280 px, JPEG re-encode), `qrcode` for labels |
| AI: vision | Local LLM behind a `VisionProvider` interface: **Bonsai** (Ternary-Bonsai-2-27B through llama.cpp `llama-server` with `--mmproj`, OpenAI-compatible API on `:1080`), **Ollama** (qwen3-vl), **LM Studio**, or **heuristic** (filename-based, test only) |
| AI: cost | `CostLookupProvider` interface: **Tavily** search + local Bonsai/Ollama extraction, or **Disabled** |
| Tests | pytest + httpx TestClient |

Size: about 2,400 lines of Python in `app/`, about 1,100 lines of templates, about 730 lines of CSS/JS, and about 1,300 lines of tests.

### 3.2 Code layout (`outputs/home-inventory-app/`)

```text
app/
  main.py               FastAPI routes: HTML pages + JSON API (~45 routes)
  repository.py         Data access: containers, items, detections, history, settings, cost estimates
  database.py           Connection, migration runner, demo seed (--seed)
  settings.py           Paths and env-driven config
  categories.py         Household categories, standard rooms
  scheduler.py          In-process thread: runs the armed deep scan once at DEEP_SCAN_HOUR (default 2 AM)
  nightly_reprocess.py  Deep-scan pass, also runnable as `python -m app.nightly_reprocess`
  services/
    vision.py           Provider classes, strict detection contract, image prep, optional 2x2 tiling
    cost_lookup.py      Provider classes, privacy guardrails, budget guard, source-URL verification
    search.py           Query normalization, synonyms, filtered search, difflib similar-items
    labels.py           QR generation
  templates/            dashboard, capture, import, container_detail, search, labels, admin, ...
migrations/001..007     Schema evolution (see 3.3)
tests/                  test_core, test_llm_vision, test_cost_lookup, test_nightly_reprocess
scripts/vision_eval/    Golden-set evaluation harness for vision accuracy
```

### 3.3 Data model

```text
boxes (containers)    id, public_id (QR), name, container_type, parent_box_id -> boxes,
                      notes, tags, size, stack_position, inaccessible
box_locations         box_id (1:1), room_name, north_ft, east_ft, elevation_ft
box_photos            box_id, filename, original_filename, deep_scan_model, deep_scanned_at
detection_suggestions box_id, photo_id, item_name, quantity, confidence, category, notes,
                      status (suggested|confirmed|dismissed), source_model, pass_type (live|reprocess)
box_items             box_id, item_name, normalized_name, quantity, status (confirmed|likely),
                      confidence, category, tags, notes, priority,
                      standard_system/code/label
cost_estimates        box_item_id, estimated_cost_usd, quantity, confidence,
                      source_title, source_url, created_at  (insert-only history)
labels                box_id, filename, target_url, format
edit_history          entity_type, entity_id, action, before_json, after_json
app_settings          key/value (deep-scan armed flag, last run date)
```

Design choices worth keeping:
- **Suggestions are separate from inventory.** AI output lands in `detection_suggestions`. Only confirmation creates `box_items`. This is what makes the human-in-the-loop guarantee hold.
- **Cost estimates live in their own table.** No columns were added to `box_items`, so the feature can be dropped cleanly.
- **QR codes encode a URL, not data.** Labels keep working as contents change.

### 3.4 AI pipeline

1. **Image prep**: EXIF transpose, downscale to `VISION_MAX_IMAGE_DIMENSION` (1280), JPEG at quality 85. This fixes sideways iPhone photos and prevents context-window overflow. Optional 2×2 overlapping tiling (`VISION_TILING_ENABLED`) gives cluttered photos more pixels per object.
2. **Detection**: the provider prompts the model for strict JSON.
3. **Strict contract** (`normalize_detection`): name required (≤120 chars), quantity an int ≥1, confidence clamped to 0–1, category coerced to a known household category (otherwise *Unknown / Needs Review*), notes ≤500 chars. Results below `VISION_MIN_CONFIDENCE` (0.3) are dropped. Malformed output raises `VisionError` with a message safe to show the user.
4. **Review/confirm**: `POST /api/detections/confirm-batch` confirms (with edited quantities) and dismisses in one call. Merged duplicates from a batch import resolve together.
5. **Deep scan**: re-runs each photo once per model label with thinking on (about 25 s per photo). New results are *added* as `pass_type='reprocess'` suggestions and never replace live ones.

### 3.5 Key API surface

| Area | Endpoints |
|---|---|
| Containers | `POST /api/boxes`, `POST /api/capture/containers`, `PATCH /api/boxes/{id}`, `PATCH /api/boxes/{id}/location`, `DELETE /api/boxes/{id}` |
| Photos/AI | `POST /api/boxes/{id}/photos`, `POST /api/boxes/{id}/photos/{pid}/reprocess`, `GET/POST /api/import…`, `GET /api/reprocess/status`, `POST /api/reprocess/arm \| disarm` |
| Items | `POST /api/boxes/{id}/items`, `PATCH/DELETE /api/box-items/{id}`, `POST /api/box-items/{id}/move`, `POST /api/items/merge` |
| Detections | `POST /api/detections/{id}/confirm`, `DELETE /api/detections/{id}`, `POST /api/detections/confirm-batch` |
| Cost | `POST /api/items/{id}/cost-estimate`, `POST /api/boxes/{id}/cost-estimates`, `GET /api/items/{id}/cost-estimates` |
| Search/export | `GET /api/search`, `GET /export.json`, `GET /export.csv` |

The API already accepts exactly what a future native companion app, such as a smart-glasses capture app, would send.

### 3.6 Quality and testing
- 57 tests: **51 pass, 6 fail**. All 6 failures are a known, pre-existing Windows baseline: SQLite file-lock `PermissionError` during test teardown, plus one heuristic-provider test broken by image preprocessing of fake image bytes. None are caused by recent features.
- The vision golden-set harness (`scripts/vision_eval/`) measures detection accuracy when models or prompts change.
- Planning discipline: each epic has GOAL / CONTEXT / DECISIONS / TODO documents under `docs/AI_Planning/support/`.

### 3.7 Current limitations and technical debt

| Issue | Impact | Notes |
|---|---|---|
| **No authentication** | Anyone on the LAN can view, edit or delete | Acceptable at home. Not acceptable for client data |
| **Single household per database** | Cannot serve multiple clients cleanly | Could run one data folder per client (via `HOME_INVENTORY_DATA`) as a stopgap |
| **QR labels encode the host LAN URL** | Labels break if the IP changes or the inventory moves to another home or a server | Encode a stable domain or a `public_id`-only scheme |
| **No item-level photo link** | Items link to a container, not to the specific photo or crop that shows them | Weakens the per-item insurance evidence |
| **No value totals or report** | Estimates are visible per item only, with no rollup by room or category and no PDF | Core deliverable for insurance and downsizing |
| **CSV export omits category, cost and container path** | Less useful to insurers and adjusters | Easy fix |
| **No item lifecycle status** | Cannot record loaned, sold, donated or missing | Needed for the "is it still here?" use case |
| **Search uses SQL `LIKE`** | Fine for thousands of items, slower at large scale | SQLite FTS5 is a drop-in upgrade |
| **Heavy local AI requirement** | Bonsai 27B needs a capable GPU machine | A field laptop needs a smaller model, or a home-base server reached over VPN (Tailscale is already in use) |
| **README setup section stale** | Points to an old path and port 8000; the app actually runs on 1800 | Docs fix |
| **Cost guard counts successes, not attempts** | Failed lookups use search credits without being counted | Known accepted gap |
| **Backups are local drives only** | Fire or theft could take both the PC and `D:` | The `insurance-evidence-and-backup` note proposes off-site zips |

---

## 4. Suggested Further Development

### 4.1 Sprint roadmap toward a service product

**Sprint 1: "Where is it, and is it still here?"** *(your added use case)*
- Add an item `lifecycle_status`: `in_home`, `loaned`, `in_storage_offsite`, `donated`, `sold`, `given_away`, `discarded`, `missing`.
- Add a **loans** table: item, borrower name and contact, date out, expected return, date returned, notes. Add a "Lent out" dashboard panel with overdue highlighting.
- Add a "Last seen / last verified" date on items and containers, plus a **verify mode**: scan a container's QR, tick off items that are still there, and flag the rest as missing.
- Make search show status ("Loaned to Dave, 2026-10-02") alongside location.

**Sprint 2: Insurance-grade records**
- Add item fields: brand, model, serial number, purchase date, purchase price, condition, and an `owned_by_date` that defaults to the photo date.
- Attach receipt and close-up photos per item, and link each item to the photo (or crop region) it was detected in.
- Have the vision prompt read brand, model and serial numbers from close-up shots. Mark those values "AI-read, verify".
- Mark high-value items (jewelry, electronics, art, firearms, collectibles) for close-up documentation and possible insurance scheduling.

**Sprint 3: The client report** *(the product the client pays for)*
- A PDF/HTML report with a cover page and household summary, total estimated replacement value by room and by category, and per-item rows with thumbnails, quantity, condition, value and source. Add a high-value appendix and a photo evidence appendix.
- Report variants:
  - **Insurance**: the full list with values and evidence.
  - **Downsizing**: grouped Keep / Sell / Donate / Gift / Discard, with heir or recipient assignments and a sale-value subtotal.
  - **Quick-find**: a printable index of items to locations.
- An adjuster-friendly CSV/XLSX export with a stable column layout.

**Sprint 4: Multi-client and security**
- **Households/workspaces**: one app hosting many client inventories, with the `household_id` boundary enforced everywhere.
- **Login**: owner (you), client (view, and optionally edit), and a read-only share link for family members or an adjuster.
- Portable QR labels: `https://<your-domain>/q/<public_id>`, or labels that work offline and resolve once the inventory is hosted.
- Encrypted off-site backup per client (dated zip → OneDrive/Drive/S3), plus a "hand over the data" export so the client owns their copy.

**Sprint 5: Downsizing workflow**
- A disposition field on items (Keep / Sell / Donate / Gift / Discard / Undecided), a family-member assignment ("Grandma's clock → Sarah"), and a voting or claiming view for family members.
- Resale value estimates (used-market prices) kept separate from replacement cost. The current Tavily lookup can be prompted for "used price".
- Donation receipt summaries for tax purposes, and a moving-box packing list per destination.

**Sprint 6: Field efficiency**
- A field-capture mode for a laptop plus phone at a client's house: works offline, queues photos, and syncs to the home server for the deep scan overnight.
- A smaller or quantized vision model option for laptops, or remote inference to the home GPU over Tailscale.
- Room-by-room progress tracking ("Kitchen 80% documented") and a walkthrough checklist so nothing is missed.

### 4.2 Business considerations for the side hustle

- **Lead with privacy.** "Your photos never go to the cloud; AI runs on equipment I own" is a genuine differentiator over cloud inventory apps and a reason to hire a person rather than download an app.
- **Present values honestly.** Label AI valuations as *estimated replacement cost with cited sources*, not appraisals. Recommend a certified appraiser for jewelry, art and antiques, and consider partnering with one for referrals. Carry professional liability (E&O) insurance before selling reports that people will use in claims.
- **Natural referral partners**: insurance agents, estate attorneys, senior move managers, realtors, estate-sale companies, and assisted-living communities.
- **Packaging ideas**: a one-time "home documentation" visit plus report; an annual refresh; a downsizing package (inventory, disposition plan, family claiming); and a lighter self-service tier where clients take their own photos and you run the AI and produce the report.
- **Client data handling**: a written data-retention and deletion policy, encrypted storage, and giving each client their own export. These matter as soon as you hold other families' household data.

### 4.3 Quick wins (hours, not sprints)
1. Add category, container path and latest cost estimate to the CSV export.
2. Add a "Total estimated value" figure on the container detail page and dashboard (a `SUM` over the latest estimates).
3. Update the README setup section (current path, port 1800, `start.ps1`).
4. Fix the Windows SQLite file-lock teardown in the tests so the suite runs green.
5. Count failed cost lookups against the monthly budget.
6. Add an off-site copy step to `backup-data.ps1`.

---

## 5. Bottom Line

The application already does the hardest part of the proposed business well: turning photos into a confirmed, searchable, located inventory, with privacy and audit trails built in from the start. The gap to a sellable service is mostly packaging and business features: client separation, item status and loans, insurance fields, a professional report, and security. These are well understood and fit the existing architecture without rework.
