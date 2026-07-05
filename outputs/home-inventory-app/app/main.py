from __future__ import annotations

import csv
import io
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .categories import HOUSEHOLD_CATEGORIES
from .database import connect, migrate
from .repository import (
    add_detection,
    add_item_to_box,
    add_photo,
    confirm_detection,
    create_box,
    delete_box_item,
    get_box,
    list_boxes,
    move_box_item,
    record_history,
    rows,
    update_box,
    update_box_item,
    update_box_location,
)
from .services.labels import generate_qr
from .services.search import search_items, similar_items
from .services.vision import get_provider
from .settings import APP_NAME, DATA_DIR, LABEL_DIR, PHOTO_DIR, ensure_dirs

migrate()
ensure_dirs()

app = FastAPI(title=APP_NAME)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/media/photos", StaticFiles(directory=PHOTO_DIR), name="photos")
app.mount("/media/labels", StaticFiles(directory=LABEL_DIR), name="labels")


def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, conn=Depends(db)):
    boxes = list_boxes(conn)
    rooms = rows(conn.execute("SELECT room_name, COUNT(*) AS count FROM box_locations GROUP BY room_name ORDER BY room_name"))
    recent = rows(conn.execute("SELECT * FROM edit_history ORDER BY created_at DESC LIMIT 8"))
    return templates.TemplateResponse("dashboard.html", {"request": request, "boxes": boxes, "rooms": rooms, "recent": recent})


@app.get("/boxes", response_class=HTMLResponse)
def boxes_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse("boxes.html", {"request": request, "boxes": list_boxes(conn)})


@app.get("/boxes/new", response_class=HTMLResponse)
def new_box_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse("new_box.html", {"request": request, "containers": list_boxes(conn)})


@app.get("/box/{public_id}", response_class=HTMLResponse)
def public_box_page(public_id: str, request: Request, conn=Depends(db)):
    box = get_box(conn, public_id=public_id)
    if not box:
        raise HTTPException(404, "Container not found")
    all_boxes = list_boxes(conn)
    return templates.TemplateResponse("container_detail.html", {"request": request, "box": box, "boxes": all_boxes, "mobile": True, "categories": HOUSEHOLD_CATEGORIES})


@app.get("/boxes/{box_id}", response_class=HTMLResponse)
def box_detail_page(box_id: int, request: Request, conn=Depends(db)):
    box = get_box(conn, box_id=box_id)
    if not box:
        raise HTTPException(404, "Container not found")
    return templates.TemplateResponse("container_detail.html", {"request": request, "box": box, "boxes": list_boxes(conn), "mobile": False, "categories": HOUSEHOLD_CATEGORIES})


@app.get("/capture", response_class=HTMLResponse)
def capture_page(request: Request, conn=Depends(db)):
    return templates.TemplateResponse("capture.html", {"request": request, "container": None, "containers": list_boxes(conn)})


@app.get("/capture/{public_id}", response_class=HTMLResponse)
def capture_container_page(public_id: str, request: Request, conn=Depends(db)):
    container = get_box(conn, public_id=public_id)
    if not container:
        raise HTTPException(404, "Container not found")
    return templates.TemplateResponse("capture.html", {"request": request, "container": container, "containers": []})


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = "", room: str = "", tag: str = "", category: str = "", min_confidence: float = 0, conn=Depends(db)):
    results = search_items(conn, q, room, tag, category, min_confidence)
    similar = similar_items(conn, q) if q else []
    rooms = rows(conn.execute("SELECT DISTINCT room_name FROM box_locations ORDER BY room_name"))
    return templates.TemplateResponse(
        "search.html",
        {"request": request, "q": q, "room": room, "tag": tag, "category": category, "min_confidence": min_confidence, "results": results, "rooms": rooms, "similar": similar, "categories": HOUSEHOLD_CATEGORIES},
    )


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


@app.post("/api/boxes/{box_id}/photos")
async def api_add_photos(box_id: int, photos: Annotated[list[UploadFile], File()], conn=Depends(db)):
    if not get_box(conn, box_id=box_id):
        raise HTTPException(404, "Container not found")
    suggestions = await save_photos_and_detect(conn, box_id, photos)
    return {"suggestions": suggestions}


async def save_photos_and_detect(conn, box_id: int, photos: list[UploadFile]) -> list[dict]:
    provider = get_provider()
    suggestions = []
    for upload in photos:
        if not upload.filename:
            continue
        suffix = Path(upload.filename).suffix.lower() or ".jpg"
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        destination = PHOTO_DIR / stored_name
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        photo_id = add_photo(conn, box_id, stored_name, upload.filename, upload.content_type or "")
        for item in provider.detect(destination):
            suggestion_id = add_detection(conn, box_id, photo_id, item.name, item.confidence, item.quantity, item.category, item.notes)
            suggestions.append({"id": suggestion_id, "name": item.name, "confidence": item.confidence})
    return suggestions


@app.delete("/api/boxes/{box_id}")
def api_delete_box(box_id: int, conn=Depends(db)):
    box = get_box(conn, box_id=box_id)
    if not box:
        raise HTTPException(404, "Container not found")
    record_history(conn, "container", box_id, "deleted", before={"name": box["name"]})
    conn.execute("DELETE FROM boxes WHERE id = ?", (box_id,))
    return {"ok": True}


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
    return {"item_id": confirm_detection(conn, suggestion_id)}


@app.delete("/api/detections/{suggestion_id}")
def api_dismiss_detection(suggestion_id: int, conn=Depends(db)):
    conn.execute("UPDATE detection_suggestions SET status = 'dismissed' WHERE id = ?", (suggestion_id,))
    record_history(conn, "detection", suggestion_id, "dismissed")
    return {"ok": True}


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
