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

## Project Structure

```text
home-inventory-app/
  app/
    main.py                 FastAPI routes and HTML pages
    database.py             SQLite connection, migrations, seed support
    repository.py           Data-access helpers
    settings.py             Local paths and runtime settings
    services/
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

- `VISION_PROVIDER=heuristic` is the default. It extracts likely item names from image filenames and provides useful demo behavior without sending photos anywhere.
- `VISION_PROVIDER=ollama` uses a local Ollama vision model on your computer. Example:

```powershell
ollama pull llama3.2-vision
$env:VISION_PROVIDER="ollama"
$env:OLLAMA_VISION_MODEL="llama3.2-vision"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `VISION_PROVIDER=openai` is available only if you choose to configure `OPENAI_API_KEY`. It sends images to OpenAI, so leave it off if you want photos to remain entirely local.

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
