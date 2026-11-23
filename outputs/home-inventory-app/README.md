# Home Inventory

A local-first home inventory web app for cataloging physical items in storage boxes, printing QR labels, and finding an item by exact box location.

## What It Does

- Create boxes from one or more photos.
- Suggest items from photos through a modular vision layer.
- Review, confirm, edit, move, merge, and delete items.
- Store exact location for every box: room, north-wall distance, east-wall distance, and elevation.
- Generate one QR code per box. Scanning the QR code opens the mobile-friendly box detail page.
- Print labels one at a time or four per page.
- Search by item name with forgiving partial matching, tags, rooms, category, confidence, and similar-item suggestions.
- Export inventory data as JSON or CSV.
- Keep an edit history for boxes, items, locations, labels, and detections.
- Optionally look up an estimated replacement cost for confirmed items (opt-in, disabled by default).

## Project Structure

```text
home-inventory-app/
  app/
    main.py                 FastAPI routes and HTML pages
    database.py             SQLite connection, migrations, seed support
    repository.py           Data-access helpers
    settings.py             Local paths and runtime settings
    services/
      cost_lookup.py        Opt-in replacement-cost lookup providers
      labels.py             QR code and label generation
      search.py             Search normalization and similar matches
      vision.py             Pluggable image recognition providers
    static/
      app.css
      app.js
    templates/
      *.html
  migrations/
    001_initial.sql
  tests/
    test_core.py
  data/                     Created at runtime; ignored by git in normal use
  requirements.txt
```

## Setup

```powershell
cd C:\Users\jpful\Documents\Codex\2026-05-31\how-much-work-can-we-do\outputs\home-inventory-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.database --seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open [http://localhost:8000](http://localhost:8000).

For iPhone access on your home network, find your computer's local IP address and open `http://YOUR-COMPUTER-IP:8000` on the phone. QR labels are generated using the host that created them, so create/print labels from the network address you want your phone to scan.

## Image Recognition

The app is local-first. The vision module is deliberately swappable:

- `VISION_PROVIDER=bonsai` is the default. It uses Ternary-Bonsai-2-27B (a Qwen port with vision) served by a local llama.cpp `llama-server` with `--mmproj`. Live capture runs with thinking off (~7s per photo); the nightly deep scan reuses the same model with thinking on (~25s, catches more small items). Bonsai also does the cost-lookup extraction step.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BONSAI_URL` | `http://127.0.0.1:1080` | Base URL of the Bonsai llama-server. |
| `BONSAI_VISION_MODEL` | `bonsai2-27b` | Label recorded with each detection (llama-server serves one model and ignores the name). |
| `BONSAI_VISION_THINKING` | `false` | Turn the reasoning pass on for live capture. |
| `BONSAI_VISION_MAX_TOKENS` | `2000` | Response token budget. |
| `BONSAI_REPROCESS_VISION_MODEL` | `bonsai2-27b-thinking` | Deep-scan label; photos are re-scanned once per label. |

- `VISION_PROVIDER=ollama` uses a local Ollama vision model instead (`OLLAMA_VISION_MODEL`, deep scan `OLLAMA_REPROCESS_VISION_MODEL`). `.\start.ps1 -VisionProvider ollama` switches everything back to Ollama.
- `VISION_PROVIDER=lmstudio` points the same OpenAI-compatible client at LM Studio (`LMSTUDIO_URL`, `LMSTUDIO_VISION_MODEL`).
- `VISION_PROVIDER=heuristic` guesses item names from filenames only; the capture endpoints refuse it so it is never mistaken for a real detection pass.

## Estimated Replacement Cost (opt-in)

Confirmed items can get an estimated replacement cost for insurance documentation: a web search finds current prices, and the local Bonsai model extracts a structured estimate (`estimated_cost_usd`, `confidence`, `source_title`, `source_url`). The feature is **disabled by default** and never runs automatically — estimates are always a deliberate user action from the container detail page ("Estimate cost" per item, or "Estimate all" for a container).

### Enabling it

```powershell
$env:COST_LOOKUP_PROVIDER="tavily"
$env:COST_LOOKUP_API_KEY="your-tavily-api-key"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `COST_LOOKUP_PROVIDER` | `disabled` | `tavily` enables the feature. `disabled`, unset, or any unrecognized value resolves to a no-op provider that makes zero network calls (the kill switch). |
| `COST_LOOKUP_API_KEY` | unset | Search-provider API key. Falls back to `TAVILY_API_KEY` if unset. |
| `COST_LOOKUP_MONTHLY_LIMIT` | `50` | App-side monthly budget guard. Once this many lookups have been recorded in the current calendar month, further lookups are refused with a clear error until the month rolls over. |
| `COST_LOOKUP_LLM` | `bonsai` | Local model for the extraction step: `bonsai` (uses `BONSAI_URL`) or `ollama`. |
| `COST_LOOKUP_OLLAMA_MODEL` | `llama3.2` | Extraction model when `COST_LOOKUP_LLM=ollama`. Reuses `OLLAMA_URL`. |

### Privacy guarantees

- Only the item **name and category** ever leave the device — never photos, notes, box or room locations, or any other inventory data.
- Batch requests ("Estimate all") fan out into one outbound search request **per item**; multiple items are never combined into a single request, so the search provider never sees the shape of your inventory.
- All reasoning over search results runs on your **local Bonsai** model (or Ollama if configured); no cloud LLM is involved.
- Estimates must cite a source URL that actually appeared in the search results; anything without a verifiable source is rejected rather than stored.

### Excluded categories and per-item opt-out

- Items in the `Documents & Paper` and `Sentimental / Keepsakes` categories are excluded by default. The exclusion is enforced before any network call — not just hidden in the UI.
- To opt out a single item of any category, add the reserved tag `no-cost-lookup` to the item's tags. Lookups for that item are refused until the tag is removed.

### History

Estimates are insert-only history, never overwritten: re-estimating an item adds a new row so price changes stay auditable over time. The UI shows the latest estimate with its confidence, source link, and age.

### Kill switch and rollback

1. Set `COST_LOOKUP_PROVIDER=disabled` (or unset it) to stop all network egress for this feature immediately.
2. Cost-estimate UI elements degrade to "not available" without affecting existing item/photo/detection flows.
3. If needed, the `cost_estimates` table can be dropped without affecting `box_items` — the feature adds no columns to the core item table.

### Key API endpoints

- `POST /api/items/{id}/cost-estimate` — estimate one item; returns the new estimate, or a 422 with a clear message when the feature is disabled, the category is excluded, the item is opted out, or the monthly limit is reached.
- `POST /api/boxes/{id}/cost-estimates` — "estimate all" for a container; returns `{"estimated": [...], "skipped": [...], "failed": [...]}` with a per-item reason for anything skipped or failed.
- `GET /api/items/{id}/cost-estimates` — returns `{"latest": ..., "history": [...]}` for an item.

## Mobile Capture Flow (llm_vision)

The `/capture` page is the iPhone-first entry point:

1. Open `http://YOUR-COMPUTER-IP:8000/capture` on the phone.
2. Tap **Create & Start Capturing** to make a new container inline (default type `box`, QR label generated automatically), or pick an existing one.
3. Take a photo. The strict detection list appears on the same page with item name, editable count, confidence, and category.
4. Uncheck wrong items, fix counts, then tap **Confirm Selected Items**. Confirmed items are saved to inventory with status `confirmed`; unchecked ones are recorded as `dismissed` and never enter inventory. Both are tracked in edit history.

If the local vision service (Bonsai or Ollama) is unreachable or returns malformed output, the photo is still saved and the page shows an actionable error message.

### Key API endpoints
- `POST /api/capture/containers` — inline container creation; returns `container_id`, `public_id`, `capture_url`.
- `POST /api/boxes/{id}/photos` — returns `{"suggestions": [...], "vision_error": null|"message"}`; each suggestion has `id`, `name`, `quantity`, `confidence`, `category`, `notes`.
- `POST /api/detections/confirm-batch` — body `{"confirm": [{"id": 1, "quantity": 2}], "dismiss": [3]}`.

## Smart Glasses (Ray-Ban Meta) Workflow — Optional

There is no way for a local web app to connect directly to Ray-Ban Meta glasses: the glasses pair with your phone, and photos sync through the Meta AI app. Direct camera access for third-party software requires Meta's Wearables Device Access Toolkit, a native iOS/Android SDK currently in developer preview. This app therefore supports glasses through two import paths that work today, plus a documented hook for a future direct integration.

**Path 1 — Photo Library (iPhone, easiest).** Take photos with the glasses; they sync to your camera roll via the Meta AI app. On the capture page, tap **Choose From Library**, multi-select the glasses shots, and they flow through the normal detect → review → confirm pipeline.

**Path 2 — Import inbox (desktop, batch).** Copy or sync glasses photos into the inbox folder (`data/import-inbox` by default, or set `HOME_INVENTORY_IMPORT`). Open `/import`, select photos, choose an existing container or create a new box inline, and click **Import & Generate Item List**. Detections from all photos are merged into a single deduplicated list — same item seen in multiple photos becomes one entry with summed quantity — which you review and confirm in one pass. Imported files are moved out of the inbox into permanent photo storage.

**Path 3 — Direct integration (future).** A companion mobile app built with Meta's Wearables Device Access Toolkit could capture from the glasses and POST directly to this app's API: `POST /api/capture/containers` to create a box, `POST /api/boxes/{id}/photos` to upload and detect, and `POST /api/detections/confirm-batch` to persist. The endpoints already accept exactly what such an app would send.

### Import API
- `GET /api/import/photos` — list inbox files.
- `POST /api/import` — body `{"filenames": [...], "box_id": 1}` or `{"filenames": [...], "new_container": {"name": "", "room_name": "attic"}}`, optional `"merge": true` (default). Returns merged suggestions where each entry may carry `merge_ids` (duplicate detections resolved together on confirm).
- `POST /api/detections/confirm-batch` — confirm entries may include `merge_ids`; duplicates are marked confirmed-by-merge without creating extra inventory rows.

## Core Flows

- **Create box from photos:** `Create` page, choose single or batch of four, upload photos, fill location, save.
- **Review detections:** box detail page shows suggested items as "likely contains"; confirm, edit, or delete them.
- **Print labels:** box detail for one label, or `Labels` for four-per-page printing.
- **Scan QR:** scan with iPhone camera; it opens the mobile box page with contents and exact location.
- **Find item:** use the dashboard search or Search page. Results show box, room, coordinates, tags, and confidence.
- **Move item:** from a box detail page, choose destination box and move.
- **Update location:** edit the location section on the box detail page.
- **Add more photos:** upload more photos on an existing box; the app creates new suggestions.
- **Backup:** use `Export` links for JSON or CSV.

## Tests

```powershell
pytest
```

## Architectural Notes

- SQLite keeps the app simple and reliable for home use. The schema is normalized enough to upgrade later.
- Migrations are plain SQL and run automatically at startup.
- Photos, QR images, and the generated database stay under the local `data/` directory.
- QR codes point to the box detail URL rather than embedding inventory data, so labels keep working as contents and locations change.
- Image recognition is isolated behind `VisionProvider`, making it easy to switch between local and cloud models without touching the rest of the app.
- Cost lookup follows the same pattern behind `CostLookupProvider`, so the search backend can be swapped (or fully disabled) via `COST_LOOKUP_PROVIDER` without touching callers.
