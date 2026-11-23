from __future__ import annotations

import csv
import io
import time
import shutil
import uuid
from pathlib import Path
from typing import Annotated

import os
import socket

import requests

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .categories import HOUSEHOLD_CATEGORIES, STANDARD_ROOMS
from .database import connect, migrate
from .repository import (
    add_cost_estimate,
    add_detection,
    add_item_to_box,
    add_photo,
    confirm_detection,
    create_box,
    delete_box_item,
    dismiss_detection,
    get_box,
    get_box_item,
    get_setting,
    latest_cost_estimate,
    list_boxes,
    list_cost_estimates_for_item,
    list_photos_pending_deep_scan,
    move_box_item,
    normalize,
    record_history,
    resolve_merged_detections,
    rows,
    set_setting,
    update_box,
    update_box_item,
    update_box_location,
)
from . import scheduler
from .scheduler import ARMED_KEY, DEEP_SCAN_HOUR, LAST_RUN_KEY
from .services.cost_lookup import (
    EXCLUDED_CATEGORIES,
    CostLookupError,
    ensure_budget_available,
    estimate_replacement_cost,
)
from .services.labels import generate_qr
from .services.search import search_items, similar_items
from .services.vision import VisionError, bonsai_base_url, bonsai_vision_model, get_provider
from .settings import APP_NAME, DATA_DIR, IMPORT_DIR, IMPORT_EXTENSIONS, LABEL_DIR, PHOTO_DIR, ensure_dirs, reprocess_vision_model

# Vision providers that actually call a model. The alternative is the offline
# "heuristic" provider, which these endpoints deliberately refuse so a silent
# downgrade never looks like a real detection pass. "bonsai" (the default)
# is the local Bonsai llama.cpp server; "lmstudio" is the same
# OpenAI-compatible client pointed at LM Studio.
LLM_VISION_PROVIDERS = {"bonsai", "ollama", "lmstudio"}


def _not_an_llm_provider_message(provider_name: str) -> str:
    expected = ", ".join(sorted(LLM_VISION_PROVIDERS))
    return f"LLM vision not used: VISION_PROVIDER is '{provider_name}', expected one of: {expected}."


def _active_vision_model(provider_name: str) -> str:
    """Report the model of whichever provider is configured, for response meta."""
    if provider_name == "bonsai":
        return bonsai_vision_model()
    if provider_name == "lmstudio":
        return os.environ.get("LMSTUDIO_VISION_MODEL", "qwen3.8-27b")
    return os.environ.get("OLLAMA_VISION_MODEL", "qwen3-vl:8b-instruct")


migrate()
ensure_dirs()
scheduler.start()

app = FastAPI(title=APP_NAME)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/media/photos", StaticFiles(directory=PHOTO_DIR), name="photos")
app.mount("/media/labels", StaticFiles(directory=LABEL_DIR), name="labels")
app.mount("/media/inbox", StaticFiles(directory=IMPORT_DIR), name="inbox")


def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# COST LOOKUP UI/OPT-OUT HELPERS (T10-T13)
# ==========================================
# box_items has no dedicated cost-lookup opt-out column (schema changes are
# disallowed -- see docs/AI_Planning/support/cost_of_replacement/DECISIONS.md).
# Per-item opt-out instead reuses the existing free-text ``tags`` column
# (comma-separated, same convention as add_item_to_box(..., tags="tools,cables"))
# with a reserved tag: "no-cost-lookup". The endpoint layer (here) owns this
# check and passes the resulting boolean into estimate_replacement_cost()'s
# ``opt_out`` parameter; the service layer never reads ``tags`` itself.
COST_LOOKUP_OPT_OUT_TAG = "no-cost-lookup"


def item_opted_out_of_cost_lookup(tags: str) -> bool:
    return COST_LOOKUP_OPT_OUT_TAG in {value.strip().lower() for value in (tags or "").split(",")}


def cost_lookup_enabled() -> bool:
    """Live-read COST_LOOKUP_PROVIDER rather than trusting settings.py's cached constant.

    settings.py computes COST_LOOKUP_PROVIDER once at import time; in a
    process where the module was already imported before a test/operator
    sets the env var, that cached value would be stale. services/cost_lookup.py's
    own get_cost_provider() has the identical issue and already works around
    it by reading os.environ directly instead of settings.COST_LOOKUP_PROVIDER
    (see cost_lookup.py); this mirrors that same pattern for the UI check.
    """
    return os.environ.get("COST_LOOKUP_PROVIDER", "disabled").lower() != "disabled"


def attach_cost_lookup_info(conn, box: dict) -> dict:
    """Annotate each item in ``box["items"]`` with cost-lookup display state (T13)."""
    for item in box.get("items", []):
        item["latest_cost_estimate"] = latest_cost_estimate(conn, item["id"])
        item["cost_lookup_opted_out"] = item_opted_out_of_cost_lookup(item.get("tags") or "")
        item["cost_lookup_excluded_category"] = (item.get("category") or "") in EXCLUDED_CATEGORIES
    return box


def _bonsai_ready() -> bool:
    try:
        response = requests.get(f"{bonsai_base_url()}/v1/models", timeout=2)
        response.raise_for_status()
        return bool(response.json().get("data"))
    except Exception:
        return False


def _ollama_ready(requested: str) -> bool:
    generate_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    base_url = generate_url.split("/api/", 1)[0].rstrip("/")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = {(entry.get("name") or "").strip() for entry in models if isinstance(entry, dict)}
    except Exception:
        return False
    requested = requested.strip()
    requested_base = requested.split(":", 1)[0]
    return requested in names or any(name.split(":", 1)[0] == requested_base for name in names)


def llm_status() -> dict:
    """Dashboard readiness for the vision model and the cost-extraction model."""
    vision_provider = os.environ.get("VISION_PROVIDER", "bonsai").lower()
    vision_model = _active_vision_model(vision_provider)
    if vision_provider == "ollama":
        vision_ready = _ollama_ready(vision_model)
    elif vision_provider == "bonsai":
        vision_ready = _bonsai_ready()
    else:
        vision_ready = False

    if os.environ.get("COST_LOOKUP_LLM", "bonsai").lower() == "ollama":
        cost_model = os.environ.get("COST_LOOKUP_OLLAMA_MODEL", "llama3.2")
        cost_ready = _ollama_ready(cost_model)
    else:
        cost_model = bonsai_vision_model()
        cost_ready = vision_ready if vision_provider == "bonsai" else _bonsai_ready()

    return {
        "vision_model": vision_model,
        "vision_ready": vision_ready,
        "cost_model": cost_model,
        "cost_ready": cost_ready,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, conn=Depends(db)):
    boxes = list_boxes(conn)
    rooms = rows(conn.execute("SELECT room_name, COUNT(*) AS count FROM box_locations GROUP BY room_name ORDER BY room_name"))
    # Build an external URL that a phone on the same LAN can use.
    # Host/port can be overridden with env vars HOME_INVENTORY_HOST and HOME_INVENTORY_PORT.
    host_env = os.environ.get("HOME_INVENTORY_HOST", "127.0.0.1")
    port_env = os.environ.get("HOME_INVENTORY_PORT", "1800")
    display_host = host_env
    if host_env in ("0.0.0.0", "::", ""):
        # detect a likely local LAN IP without sending traffic
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                display_host = s.getsockname()[0]
        except Exception:
            display_host = "127.0.0.1"
    external_url = f"http://{display_host}:{port_env}"

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "boxes": boxes, "rooms": rooms, "external_url": external_url, "llm_status": llm_status()},
    )


@app.get("/boxes", response_class=HTMLResponse)
def boxes_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse("boxes.html", {"request": request, "boxes": list_boxes(conn)})


@app.get("/boxes/new", response_class=HTMLResponse)
def new_box_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse(
        "new_box.html",
        {"request": request, "containers": list_boxes(conn), "room_options": room_options(conn)},
    )


@app.get("/box/{public_id}", response_class=HTMLResponse)
def public_box_page(public_id: str, request: Request, conn=Depends(db)):
    box = get_box(conn, public_id=public_id)
    if not box:
        raise HTTPException(404, "Container not found")
    attach_cost_lookup_info(conn, box)
    all_boxes = list_boxes(conn)
    return templates.TemplateResponse(
        "container_detail.html",
        {
            "request": request,
            "box": box,
            "boxes": all_boxes,
            "mobile": True,
            "categories": HOUSEHOLD_CATEGORIES,
            "room_options": room_options(conn),
            "cost_lookup_enabled": cost_lookup_enabled(),
        },
    )


@app.get("/boxes/{box_id}", response_class=HTMLResponse)
def box_detail_page(box_id: int, request: Request, conn=Depends(db)):
    box = get_box(conn, box_id=box_id)
    if not box:
        raise HTTPException(404, "Container not found")
    attach_cost_lookup_info(conn, box)
    return templates.TemplateResponse(
        "container_detail.html",
        {
            "request": request,
            "box": box,
            "boxes": list_boxes(conn),
            "mobile": False,
            "categories": HOUSEHOLD_CATEGORIES,
            "room_options": room_options(conn),
            "cost_lookup_enabled": cost_lookup_enabled(),
        },
    )


def room_options(conn) -> list[str]:
    """STANDARD_ROOMS plus any room names already used, deduped case-insensitively."""
    options = list(STANDARD_ROOMS)
    seen = {name.lower() for name in options}
    for entry in rows(conn.execute("SELECT DISTINCT room_name FROM box_locations ORDER BY room_name")):
        name = (entry["room_name"] or "").strip()
        if name and name.lower() not in seen and name.lower() != "unassigned":
            options.append(name)
            seen.add(name.lower())
    return options


@app.get("/capture", response_class=HTMLResponse)
def capture_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse(
        "capture.html",
        {"request": request, "container": None, "containers": list_boxes(conn), "room_options": room_options(conn)},
    )


@app.get("/capture/{public_id}", response_class=HTMLResponse)
def capture_container_page(public_id: str, request: Request, conn=Depends(db)):
    container = get_box(conn, public_id=public_id)
    if not container:
        raise HTTPException(404, "Container not found")
    attach_cost_lookup_info(conn, container)
    return templates.TemplateResponse(
        "capture.html",
        {"request": request, "container": container, "containers": [], "room_options": room_options(conn)},
    )


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = "", room: str = "", tag: str = "", category: str = "", min_confidence: float = 0, conn=Depends(db)):
    results = search_items(conn, q, room, tag, category, min_confidence)
    similar = similar_items(conn, q) if q else []
    rooms = rows(conn.execute("SELECT DISTINCT room_name FROM box_locations ORDER BY room_name"))
    return templates.TemplateResponse(
        "search.html",
        {"request": request, "q": q, "room": room, "tag": tag, "category": category, "min_confidence": min_confidence, "results": results, "rooms": rooms, "similar": similar, "categories": HOUSEHOLD_CATEGORIES},
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/labels", response_class=HTMLResponse)
def labels_page(request: Request, ids: str = "", conn=Depends(db)):
    selected = [int(value) for value in ids.split(",") if value.strip().isdigit()]
    boxes = [get_box(conn, box_id=box_id) for box_id in selected] if selected else list_boxes(conn)[:4]
    boxes = [ensure_box_label(conn, request, box) for box in boxes if box]
    return templates.TemplateResponse("labels.html", {"request": request, "boxes": boxes})


def ensure_box_label(conn, request: Request, box: dict) -> dict:
    if box.get("labels"):
        return box
    target_url = str(request.url_for("public_box_page", public_id=box["public_id"]))
    filename = generate_qr(box["public_id"], box["name"], target_url)
    conn.execute("INSERT INTO labels(box_id, filename, target_url) VALUES (?, ?, ?)", (box["id"], filename, target_url))
    record_history(conn, "label", box["id"], "generated", after={"filename": filename, "target_url": target_url})
    return get_box(conn, box_id=box["id"])


@app.post("/api/boxes")
async def api_create_box(
    request: Request,
    name: Annotated[str, Form()] = "",
    room_name: Annotated[str, Form()] = "unassigned",
    north_ft: Annotated[float, Form()] = 0,
    east_ft: Annotated[float, Form()] = 0,
    elevation_ft: Annotated[float, Form()] = 0,
    notes: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    inaccessible: Annotated[int, Form()] = 0,
    size: Annotated[str, Form()] = "",
    stack_position: Annotated[str, Form()] = "",
    container_type: Annotated[str, Form()] = "box",
    parent_box_id: Annotated[str, Form()] = "",
    photos: Annotated[list[UploadFile], File()] = [],
    conn=Depends(db),
):
    parent_id = int(parent_box_id) if parent_box_id.strip().isdigit() else None
    box_id = create_box(conn, name, room_name, north_ft, east_ft, elevation_ft, notes, tags, inaccessible, size, stack_position, container_type, parent_id)
    await save_photos_and_detect(conn, box_id, photos)
    box = get_box(conn, box_id=box_id)
    target_url = str(request.url_for("public_box_page", public_id=box["public_id"]))
    filename = generate_qr(box["public_id"], box["name"], target_url)
    conn.execute("INSERT INTO labels(box_id, filename, target_url) VALUES (?, ?, ?)", (box_id, filename, target_url))
    record_history(conn, "label", box_id, "generated", after={"filename": filename})
    return {"box_id": box_id, "container_id": box_id, "public_id": box["public_id"], "url": f"/boxes/{box_id}", "label_url": f"/media/labels/{filename}"}


@app.post("/api/capture/containers")
async def api_capture_create_container(
    request: Request,
    name: Annotated[str, Form()] = "",
    room_name: Annotated[str, Form()] = "unassigned",
    conn=Depends(db),
):
    """Create a new container inline from the mobile capture flow (T4/D-004).

    Always creates ``container_type='box'`` in this phase and returns the ids
    the mobile UI needs to continue capturing without leaving the page.
    """
    box_id = create_box(conn, name.strip() or None, room_name.strip() or "unassigned", 0, 0, 0, container_type="box")
    box = get_box(conn, box_id=box_id)
    target_url = str(request.url_for("public_box_page", public_id=box["public_id"]))
    filename = generate_qr(box["public_id"], box["name"], target_url)
    conn.execute("INSERT INTO labels(box_id, filename, target_url) VALUES (?, ?, ?)", (box_id, filename, target_url))
    record_history(conn, "label", box_id, "generated", after={"filename": filename, "target_url": target_url})
    return {
        "container_id": box_id,
        "box_id": box_id,
        "public_id": box["public_id"],
        "name": box["name"],
        "container_type": box["container_type"],
        "capture_url": f"/capture/{box['public_id']}",
    }


@app.get("/import", response_class=HTMLResponse)
def import_page(request: Request, conn=Depends(db)):
    """Batch import photos synced from smart glasses (e.g. Ray-Ban Meta)."""
    return templates.TemplateResponse(
        "import.html",
        {"request": request, "photos": list_inbox_photos(), "containers": list_boxes(conn), "inbox_dir": str(IMPORT_DIR)},
    )


def list_inbox_photos() -> list[dict]:
    photos = []
    for path in sorted(IMPORT_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in IMPORT_EXTENSIONS:
            photos.append({"filename": path.name, "size_kb": round(path.stat().st_size / 1024, 1)})
    return photos


@app.get("/api/import/photos")
def api_import_photos():
    return {"photos": list_inbox_photos(), "inbox_dir": str(IMPORT_DIR)}


@app.post("/api/import")
async def api_import(request: Request, conn=Depends(db)):
    """Attach inbox photos to a container and generate an item list.

    Body: {"filenames": [...], "box_id": 1}  or
          {"filenames": [...], "new_container": {"name": "", "room_name": "attic"}}
    Optional: "merge": true (default) — deduplicate detections across photos
    into one list entry per item with summed quantities.
    Photos are moved out of the inbox into permanent photo storage.
    """
    data = await request.json()
    filenames = data.get("filenames") or []
    if not filenames:
        raise HTTPException(400, "No filenames provided")

    if data.get("box_id"):
        box = get_box(conn, box_id=int(data["box_id"]))
        if not box:
            raise HTTPException(404, "Container not found")
        box_id = box["id"]
    else:
        new_container = data.get("new_container") or {}
        box_id = create_box(
            conn,
            (new_container.get("name") or "").strip() or None,
            (new_container.get("room_name") or "").strip() or "unassigned",
            0, 0, 0,
            container_type="box",
        )
        box = get_box(conn, box_id=box_id)
        target_url = str(request.url_for("public_box_page", public_id=box["public_id"]))
        filename = generate_qr(box["public_id"], box["name"], target_url)
        conn.execute("INSERT INTO labels(box_id, filename, target_url) VALUES (?, ?, ?)", (box_id, filename, target_url))
        record_history(conn, "label", box_id, "generated", after={"filename": filename, "target_url": target_url})

    provider = get_provider()
    suggestions: list[dict] = []
    vision_error: str | None = None
    imported: list[str] = []
    for name in filenames:
        # Reject anything that isn't a plain file directly inside the inbox.
        safe_name = Path(name).name
        source = IMPORT_DIR / safe_name
        if safe_name != name or not source.is_file() or source.suffix.lower() not in IMPORT_EXTENSIONS:
            raise HTTPException(400, f"Invalid inbox file: {name}")
        stored_name = f"{uuid.uuid4().hex}{source.suffix.lower()}"
        destination = PHOTO_DIR / stored_name
        shutil.move(str(source), str(destination))
        photo_id = add_photo(conn, box_id, stored_name, safe_name, "")
        imported.append(safe_name)
        try:
            detected = provider.detect(destination, original_name=safe_name)
        except VisionError as exc:
            vision_error = str(exc)
            continue
        for item in detected:
            suggestion_id = add_detection(
                conn, box_id, photo_id, item.name, item.confidence, item.quantity, item.category, item.notes,
                source_model=_active_vision_model(os.environ.get("VISION_PROVIDER", "bonsai").lower()), pass_type="live",
            )
            suggestions.append(
                {
                    "id": suggestion_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "confidence": item.confidence,
                    "category": item.category,
                    "notes": item.notes,
                }
            )

    merge = data.get("merge", True)
    payload = merge_suggestions(suggestions) if merge else suggestions
    return {
        "container_id": box_id,
        "public_id": box["public_id"],
        "container_name": box["name"],
        "imported": imported,
        "merged": bool(merge),
        "suggestions": payload,
        "vision_error": vision_error,
    }


def merge_suggestions(suggestions: list[dict]) -> list[dict]:
    """Deduplicate detections across photos into one entry per item.

    Groups by normalized name; sums quantities; keeps the highest confidence
    and its category.  ``id`` is the primary suggestion; ``merge_ids`` are the
    duplicates to resolve alongside it on confirm.
    """
    grouped: dict[str, dict] = {}
    for suggestion in suggestions:
        key = normalize(suggestion["name"])
        entry = grouped.get(key)
        if entry is None:
            grouped[key] = {**suggestion, "merge_ids": []}
            continue
        entry["quantity"] += suggestion["quantity"]
        entry["merge_ids"].append(suggestion["id"])
        if suggestion["confidence"] > entry["confidence"]:
            entry["confidence"] = suggestion["confidence"]
            entry["category"] = suggestion["category"]
            entry["name"] = suggestion["name"]
    return list(grouped.values())


@app.post("/api/boxes/{box_id}/photos")
async def api_add_photos(box_id: int, photos: Annotated[list[UploadFile], File()], conn=Depends(db)):
    if not get_box(conn, box_id=box_id):
        raise HTTPException(404, "Container not found")
    suggestions, vision_error = await save_photos_and_detect(conn, box_id, photos)
    return {"suggestions": suggestions, "vision_error": vision_error}


async def save_photos_and_detect(conn, box_id: int, photos: list[UploadFile]) -> tuple[list[dict], str | None]:
    """Store uploads and record strict detections.

    Photos are always persisted.  If the vision provider fails (T3), the
    user-safe error message is returned instead of raising, so the API
    response stays actionable and no data is corrupted.
    """
    provider_name = os.environ.get("VISION_PROVIDER", "bonsai").lower()
    if provider_name not in LLM_VISION_PROVIDERS:
        return [], _not_an_llm_provider_message(provider_name)
    provider = get_provider()
    suggestions: list[dict] = []
    vision_error: str | None = None
    for upload in photos:
        if not upload.filename:
            continue
        suffix = Path(upload.filename).suffix.lower() or ".jpg"
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        destination = PHOTO_DIR / stored_name
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        photo_id = add_photo(conn, box_id, stored_name, upload.filename, upload.content_type or "")
        t0 = time.perf_counter()
        try:
            detected = provider.detect(destination, original_name=upload.filename)
        except VisionError as exc:
            vision_error = str(exc)
            continue
        duration_ms = int((time.perf_counter() - t0) * 1000)
        for item in detected:
            suggestion_id = add_detection(
                conn, box_id, photo_id, item.name, item.confidence, item.quantity, item.category, item.notes,
                source_model=_active_vision_model(os.environ.get("VISION_PROVIDER", "bonsai").lower()), pass_type="live",
            )
            suggestions.append(
                {
                    "id": suggestion_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "confidence": item.confidence,
                    "category": item.category,
                    "notes": item.notes,
                    "provider": provider_name,
                    "llm_used": True,
                    "model": _active_vision_model(provider_name),
                    "duration_ms": duration_ms,
                }
            )
    return suggestions, vision_error


def detect_existing_photo(conn, box_id: int, photo_id: int) -> tuple[list[dict], str | None, dict]:
    """Run vision on an already-saved photo and refresh suggestions for it.

    Existing unresolved suggestions from the same photo are marked dismissed
    before adding a fresh detection batch.
    """
    photo = conn.execute("SELECT * FROM box_photos WHERE id = ? AND box_id = ?", (photo_id, box_id)).fetchone()
    if not photo:
        raise HTTPException(404, "Photo not found")

    image_path = PHOTO_DIR / photo["filename"]
    if not image_path.exists():
        raise HTTPException(404, "Photo file not found")

    conn.execute(
        "UPDATE detection_suggestions SET status = 'dismissed' WHERE photo_id = ? AND status = 'suggested'",
        (photo_id,),
    )

    provider_name = os.environ.get("VISION_PROVIDER", "bonsai").lower()
    meta = {
        "provider": provider_name,
        "llm_used": False,
        "model": _active_vision_model(provider_name),
        "duration_ms": 0,
    }
    if provider_name not in LLM_VISION_PROVIDERS:
        return [], _not_an_llm_provider_message(provider_name), meta

    provider = get_provider()
    suggestions: list[dict] = []
    vision_error: str | None = None
    t0 = time.perf_counter()
    try:
        detected = provider.detect(image_path, original_name=photo["original_filename"])
    except VisionError as exc:
        vision_error = str(exc)
        meta["duration_ms"] = int((time.perf_counter() - t0) * 1000)
        return suggestions, vision_error, meta
    meta["duration_ms"] = int((time.perf_counter() - t0) * 1000)
    meta["llm_used"] = True

    for item in detected:
        suggestion_id = add_detection(
            conn, box_id, photo_id, item.name, item.confidence, item.quantity, item.category, item.notes,
            source_model=meta["model"], pass_type="live",
        )
        suggestions.append(
            {
                "id": suggestion_id,
                "name": item.name,
                "quantity": item.quantity,
                "confidence": item.confidence,
                "category": item.category,
                "notes": item.notes,
                "provider": provider_name,
                "llm_used": True,
                "model": meta["model"],
                "duration_ms": meta["duration_ms"],
            }
        )
    return suggestions, vision_error, meta


@app.delete("/api/boxes/{box_id}")
def api_delete_box(box_id: int, conn=Depends(db)):
    box = get_box(conn, box_id=box_id)
    if not box:
        raise HTTPException(404, "Container not found")
    record_history(conn, "container", box_id, "deleted", before={"name": box["name"]})
    conn.execute("DELETE FROM boxes WHERE id = ?", (box_id,))
    return {"ok": True}


@app.post("/api/boxes/{box_id}/photos/{photo_id}/reprocess")
def api_reprocess_photo(box_id: int, photo_id: int, conn=Depends(db)):
    if not get_box(conn, box_id=box_id):
        raise HTTPException(404, "Container not found")
    suggestions, vision_error, meta = detect_existing_photo(conn, box_id, photo_id)
    return {
        "suggestions": suggestions,
        "vision_error": vision_error,
        "provider": meta["provider"],
        "llm_used": meta["llm_used"],
        "model": meta["model"],
        "duration_ms": meta["duration_ms"],
    }


@app.get("/api/reprocess/status")
def api_reprocess_status(conn=Depends(db)):
    """Status for the nightly deep-scan pass (app/nightly_reprocess.py + app/scheduler.py).

    Reports how many stored photos have not yet been reprocessed by the
    current deep-scan model label, whether a one-shot scan is armed
    for the next nightly window, and when it last ran -- everything the
    admin page needs without triggering anything itself.
    """
    model = reprocess_vision_model()
    pending = list_photos_pending_deep_scan(conn, model)
    return {
        "model": model,
        "pending_count": len(pending),
        "armed": get_setting(conn, ARMED_KEY, "false") == "true",
        "scheduled_hour": DEEP_SCAN_HOUR,
        "last_run_date": get_setting(conn, LAST_RUN_KEY, "") or None,
    }


@app.post("/api/reprocess/arm")
def api_reprocess_arm(conn=Depends(db)):
    """Arm a one-shot deep scan: runs once during the next nightly window, then disarms itself."""
    set_setting(conn, ARMED_KEY, "true")
    return {"armed": True}


@app.post("/api/reprocess/disarm")
def api_reprocess_disarm(conn=Depends(db)):
    set_setting(conn, ARMED_KEY, "false")
    return {"armed": False}


@app.patch("/api/boxes/{box_id}")
async def api_update_box(box_id: int, request: Request, conn=Depends(db)):
    update_box(conn, box_id, **await request.json())
    return {"ok": True}


@app.patch("/api/boxes/{box_id}/location")
async def api_update_location(box_id: int, request: Request, conn=Depends(db)):
    data = await request.json()
    update_box_location(conn, box_id, data["room_name"], float(data["north_ft"]), float(data["east_ft"]), float(data["elevation_ft"]))
    return {"ok": True}


@app.post("/api/boxes/{box_id}/items")
async def api_add_item(box_id: int, request: Request, conn=Depends(db)):
    data = await request.json()
    item_id = add_item_to_box(
        conn,
        box_id,
        data["item_name"],
        int(data.get("quantity") or 1),
        data.get("status") or "confirmed",
        float(data.get("confidence") or 1),
        data.get("category") or "",
        data.get("notes") or "",
        data.get("tags") or "",
        int(data.get("priority") or 0),
    )
    return {"id": item_id}


@app.patch("/api/box-items/{item_id}")
async def api_update_item(item_id: int, request: Request, conn=Depends(db)):
    update_box_item(conn, item_id, **await request.json())
    return {"ok": True}


@app.delete("/api/box-items/{item_id}")
async def api_delete_item(item_id: int, conn=Depends(db)):
    delete_box_item(conn, item_id)
    return {"ok": True}


@app.post("/api/box-items/{item_id}/move")
async def api_move_item(item_id: int, request: Request, conn=Depends(db)):
    data = await request.json()
    move_box_item(conn, item_id, int(data["target_box_id"]))
    return {"ok": True}


@app.post("/api/detections/{suggestion_id}/confirm")
def api_confirm_detection(suggestion_id: int, conn=Depends(db)):
    item_id = confirm_detection(conn, suggestion_id)
    if item_id is None:
        raise HTTPException(404, "Suggestion not found or already resolved")
    return {"item_id": item_id}


@app.delete("/api/detections/{suggestion_id}")
def api_dismiss_detection(suggestion_id: int, conn=Depends(db)):
    if not dismiss_detection(conn, suggestion_id):
        raise HTTPException(404, "Suggestion not found or already resolved")
    return {"ok": True}


@app.post("/api/detections/confirm-batch")
async def api_confirm_detections_batch(request: Request, conn=Depends(db)):
    """Mobile capture confirm action (T6/T7/D-002).

    Body: {"confirm": [{"id": 1, "quantity": 2}, ...], "dismiss": [3, 4]}
    Confirm entries may also be plain ids.  A confirm entry may include
    "merge_ids": duplicate suggestions (same item seen in other photos) that
    are resolved as confirmed-by-merge without creating extra inventory rows.
    User-confirmed items persist to ``box_items`` with status 'confirmed';
    dismissed suggestions never enter inventory but stay auditable via
    detection status + edit history.
    """
    data = await request.json()
    confirmed_items: list[dict] = []
    for entry in data.get("confirm", []) or []:
        if isinstance(entry, dict):
            suggestion_id = int(entry.get("id", 0))
            quantity = entry.get("quantity")
            quantity = int(quantity) if quantity is not None else None
            merge_ids = [int(value) for value in (entry.get("merge_ids") or [])]
        else:
            suggestion_id, quantity, merge_ids = int(entry), None, []
        item_id = confirm_detection(conn, suggestion_id, status="confirmed", quantity=quantity)
        if item_id is not None:
            merged = resolve_merged_detections(conn, merge_ids, item_id, suggestion_id) if merge_ids else 0
            confirmed_items.append({"suggestion_id": suggestion_id, "item_id": item_id, "merged_duplicates": merged})
    dismissed = sum(1 for suggestion_id in (data.get("dismiss", []) or []) if dismiss_detection(conn, int(suggestion_id)))
    return {"confirmed": confirmed_items, "dismissed_count": dismissed}


@app.post("/api/items/merge")
async def api_merge_items(request: Request, conn=Depends(db)):
    data = await request.json()
    source_id = int(data["source_item_id"])
    target_id = int(data["target_item_id"])
    source = conn.execute("SELECT * FROM box_items WHERE id = ?", (source_id,)).fetchone()
    target = conn.execute("SELECT * FROM box_items WHERE id = ?", (target_id,)).fetchone()
    if not source or not target:
        raise HTTPException(404, "Item not found")
    conn.execute("UPDATE box_items SET quantity = quantity + ? WHERE id = ?", (source["quantity"], target_id))
    delete_box_item(conn, source_id)
    record_history(conn, "box_item", target_id, "merged", after={"source_item_id": source_id})
    return {"ok": True}


@app.post("/api/items/{item_id}/cost-estimate")
def api_estimate_item_cost(item_id: int, conn=Depends(db)):
    """T10: single-item estimated-replacement-cost lookup.

    Runs the category-exclusion, per-item opt-out, and monthly-budget guards
    (via estimate_replacement_cost()) before any network call. Never bypasses
    that entry point to call the provider directly. Never touches item_name/
    category/quantity as a side effect (GOAL.md non-negotiable). On any
    CostLookupError (including the disabled-provider case, D-005) this
    returns a clean JSON error, never a 500.
    """
    item = get_box_item(conn, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    opt_out = item_opted_out_of_cost_lookup(item.get("tags") or "")
    try:
        estimate = estimate_replacement_cost(conn, item["item_name"], item.get("category") or "", opt_out=opt_out)
    except CostLookupError as exc:
        raise HTTPException(422, str(exc)) from exc
    add_cost_estimate(
        conn,
        item_id,
        estimate.estimated_cost_usd,
        estimate.confidence,
        estimate.source_title,
        estimate.source_url,
        quantity=int(item.get("quantity") or 1),
    )
    return latest_cost_estimate(conn, item_id)


@app.post("/api/boxes/{box_id}/cost-estimates")
def api_estimate_box_costs(box_id: int, conn=Depends(db)):
    """T11: batch "estimate all" for a container.

    Fans out into N sequential single-item calls through
    estimate_replacement_cost() (D-003: never one bulk provider request).
    Partial success: each item lands in exactly one of estimated/skipped/
    failed, and the whole batch never fails just because some items are
    excluded, opted out, or hit the budget cap. Once the monthly budget cap
    is hit mid-batch, every remaining item is reported skipped with that
    reason rather than attempting (and failing) a lookup for it.
    """
    box = get_box(conn, box_id=box_id)
    if not box:
        raise HTTPException(404, "Container not found")

    estimated: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    budget_exhausted = False

    for item in box["items"]:
        summary = {"item_id": item["id"], "item_name": item["item_name"]}
        if budget_exhausted:
            skipped.append({**summary, "reason": "monthly budget reached"})
            continue

        opt_out = item_opted_out_of_cost_lookup(item.get("tags") or "")
        category = item.get("category") or ""
        if opt_out:
            skipped.append({**summary, "reason": "opted out for this item (tag: no-cost-lookup)"})
            continue
        if category in EXCLUDED_CATEGORIES:
            skipped.append({**summary, "reason": f'category "{category}" is excluded by default'})
            continue

        try:
            ensure_budget_available(conn)
        except CostLookupError:
            budget_exhausted = True
            skipped.append({**summary, "reason": "monthly budget reached"})
            continue

        try:
            estimate = estimate_replacement_cost(conn, item["item_name"], category, opt_out=False)
        except CostLookupError as exc:
            failed.append({**summary, "error": str(exc)})
            continue

        add_cost_estimate(
            conn,
            item["id"],
            estimate.estimated_cost_usd,
            estimate.confidence,
            estimate.source_title,
            estimate.source_url,
            quantity=int(item.get("quantity") or 1),
        )
        estimated.append({**summary, **latest_cost_estimate(conn, item["id"])})

    return {"estimated": estimated, "skipped": skipped, "failed": failed}


@app.get("/api/items/{item_id}/cost-estimates")
def api_list_item_cost_estimates(item_id: int, conn=Depends(db)):
    """T12: latest estimate + full history for one item."""
    item = get_box_item(conn, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return {
        "latest": latest_cost_estimate(conn, item_id),
        "history": list_cost_estimates_for_item(conn, item_id),
    }


@app.get("/api/search")
def api_search(q: str = "", room: str = "", tag: str = "", category: str = "", min_confidence: float = 0, conn=Depends(db)):
    return {"results": search_items(conn, q, room, tag, category, min_confidence)}


@app.get("/export.json")
def export_json(conn=Depends(db)):
    data = {
        "containers": list_boxes(conn),
        "boxes": list_boxes(conn),
        "items": rows(conn.execute("SELECT * FROM box_items")),
        "photos": rows(conn.execute("SELECT * FROM box_photos")),
        "locations": rows(conn.execute("SELECT * FROM box_locations")),
        "history": rows(conn.execute("SELECT * FROM edit_history")),
    }
    return JSONResponse(data)


@app.get("/export.csv")
def export_csv(conn=Depends(db)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["item", "quantity", "status", "confidence", "box", "room", "north_ft", "east_ft", "elevation_ft", "tags", "notes"])
    for item in search_items(conn):
        writer.writerow([item["item_name"], item["quantity"], item["status"], item["confidence"], item["box_name"], item["room_name"], item["north_ft"], item["east_ft"], item["elevation_ft"], item["tags"], item["notes"]])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=home-inventory.csv"})
