"""Regression tests for the llm_vision sprint (T2, T3, T4, T6, T7 / TODO T8).

Covers:
- Strict detection schema normalization (valid, partial, malformed fields).
- Robust JSON extraction from noisy model output.
- Strict-mode error handling for malformed / non-JSON output.
- Inline container creation from the mobile capture flow.
- End-to-end: create -> upload -> detect -> confirm/dismiss -> persist + audit.
- Graceful API response when the vision provider fails.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["HOME_INVENTORY_DATA"] = str(ROOT / "test-data")
os.environ["HOME_INVENTORY_DB"] = str(ROOT / "test-data" / "test.sqlite3")
os.environ["VISION_PROVIDER"] = "heuristic"

import pytest
from fastapi.testclient import TestClient

from app.database import connect, migrate
from app.main import app
from app.repository import confirm_detection, dismiss_detection, get_box
from app.services import vision
from app.services.vision import (
    DetectedItem,
    VisionError,
    extract_json_payload,
    normalize_detection,
    parse_detection_json,
)


def reset_db():
    db_path = Path(os.environ["HOME_INVENTORY_DB"])
    if db_path.exists():
        db_path.unlink()
    migrate(db_path)


def db_conn():
    return connect(Path(os.environ["HOME_INVENTORY_DB"]))


# ---------------------------------------------------------------------------
# T2: strict schema normalization
# ---------------------------------------------------------------------------

def test_normalize_detection_valid_full_item():
    item = normalize_detection(
        {"name": " Winter Gloves ", "quantity": 2, "confidence": 0.87, "category": "Clothing & Accessories", "notes": "left side"}
    )
    assert item == DetectedItem("Winter Gloves", 2, 0.87, "Clothing & Accessories", "left side")


def test_normalize_detection_partial_fields_get_defaults():
    item = normalize_detection({"name": "mystery cable"})
    assert item.quantity == 1
    assert item.confidence == 0.5
    assert item.category == "Unknown / Needs Review"
    assert item.notes == ""


def test_normalize_detection_bad_values_are_clamped():
    item = normalize_detection(
        {"name": "hammer", "quantity": "-3", "confidence": 500, "category": "Made Up Category", "notes": None}
    )
    assert item.quantity == 1
    assert item.confidence == 1.0  # >100 is not a percentage; clamped to [0, 1]
    assert item.category == "Unknown / Needs Review"
    negative = normalize_detection({"name": "hammer", "confidence": -0.3})
    assert negative.confidence == 0.0
    garbage = normalize_detection({"name": "hammer", "quantity": "many", "confidence": "high"})
    assert garbage.quantity == 1 and garbage.confidence == 0.5


def test_normalize_detection_percent_confidence_is_scaled():
    item = normalize_detection({"name": "mug", "confidence": 85})
    assert item.confidence == 0.85


def test_normalize_detection_category_case_insensitive_canonicalized():
    item = normalize_detection({"name": "mug", "category": "kitchen & dining"})
    assert item.category == "Kitchen & Dining"


def test_normalize_detection_rejects_nameless_or_non_dict():
    assert normalize_detection({"quantity": 3}) is None
    assert normalize_detection({"name": "   "}) is None
    assert normalize_detection("not a dict") is None
    assert normalize_detection(None) is None


def test_normalize_detection_truncates_long_fields():
    item = normalize_detection({"name": "x" * 500, "notes": "y" * 2000})
    assert len(item.name) == 120
    assert len(item.notes) == 500


# ---------------------------------------------------------------------------
# T3: robust JSON extraction and strict parsing
# ---------------------------------------------------------------------------

def test_extract_json_from_markdown_fence_and_prose():
    text = 'Sure! Here is the inventory:\n```json\n{"items": [{"name": "lamp"}]}\n```\nHope that helps.'
    payload = extract_json_payload(text)
    assert payload == {"items": [{"name": "lamp"}]}


def test_parse_detection_json_valid():
    items = parse_detection_json('{"items":[{"name":"tent","quantity":1,"confidence":0.9,"category":"Sports & Camping","notes":""}]}')
    assert len(items) == 1
    assert items[0].name == "tent"
    assert items[0].category == "Sports & Camping"


def test_parse_detection_json_accepts_bare_list():
    items = parse_detection_json('[{"name": "book", "quantity": 4}]')
    assert items[0].quantity == 4


def test_parse_detection_json_skips_malformed_entries():
    items = parse_detection_json('{"items": [{"name": "vase"}, {"quantity": 9}, "junk"]}')
    assert [item.name for item in items] == ["vase"]


def test_parse_detection_json_non_strict_returns_empty_on_garbage():
    assert parse_detection_json("total nonsense with no json") == []
    assert parse_detection_json("") == []


def test_parse_detection_json_strict_raises_user_safe_error():
    with pytest.raises(VisionError):
        parse_detection_json("the model rambled and returned no json", strict=True)
    with pytest.raises(VisionError):
        parse_detection_json('{"items": "not-a-list"}', strict=True)


def test_ollama_provider_unreachable_raises_vision_error(monkeypatch):
    import requests as requests_module

    def boom(*args, **kwargs):
        raise requests_module.exceptions.ConnectionError("refused")

    monkeypatch.setattr(vision.requests, "post", boom)
    provider = vision.OllamaVisionProvider()
    image = ROOT / "test-data" / "fake.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"fake")
    with pytest.raises(VisionError) as exc_info:
        provider.detect(image)
    assert "Ollama" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T4: inline container creation from capture
# ---------------------------------------------------------------------------

def test_capture_create_container_returns_ids_and_defaults_to_box():
    reset_db()
    client = TestClient(app)
    response = client.post("/api/capture/containers", data={"name": "", "room_name": "attic"})
    assert response.status_code == 200
    body = response.json()
    assert body["container_id"] == body["box_id"]
    assert body["public_id"]
    assert body["container_type"] == "box"
    assert body["capture_url"] == f"/capture/{body['public_id']}"

    conn = db_conn()
    box = get_box(conn, box_id=body["container_id"])
    assert box["container_type"] == "box"
    assert box["room_name"] == "attic"
    assert box["labels"], "QR label should be generated for the new container"
    conn.close()


def test_capture_page_loads_for_new_container():
    reset_db()
    client = TestClient(app)
    created = client.post("/api/capture/containers", data={"name": "Attic-Box-777", "room_name": "attic"}).json()
    page = client.get(created["capture_url"])
    assert page.status_code == 200
    assert "Attic-Box-777" in page.text


# ---------------------------------------------------------------------------
# T6 + T7: end-to-end capture -> detect -> confirm/dismiss -> persist
# ---------------------------------------------------------------------------

def test_end_to_end_mobile_capture_confirm_and_dismiss():
    reset_db()
    client = TestClient(app)

    created = client.post("/api/capture/containers", data={"name": "", "room_name": "garage"}).json()
    box_id = created["container_id"]

    upload = client.post(
        f"/api/boxes/{box_id}/photos",
        files={"photos": ("hammer_extension_cord.jpg", b"fake image bytes", "image/jpeg")},
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["vision_error"] is None
    suggestions = body["suggestions"]
    assert len(suggestions) >= 2
    for suggestion in suggestions:
        assert set(suggestion) >= {"id", "name", "quantity", "confidence", "category", "notes"}

    keep, drop = suggestions[0], suggestions[1]
    result = client.post(
        "/api/detections/confirm-batch",
        json={"confirm": [{"id": keep["id"], "quantity": 3}], "dismiss": [drop["id"]]},
    ).json()
    assert len(result["confirmed"]) == 1
    assert result["dismissed_count"] == 1

    conn = db_conn()
    box = get_box(conn, box_id=box_id)
    names = {item["item_name"]: item for item in box["items"]}
    assert keep["name"] in names
    assert names[keep["name"]]["status"] == "confirmed"
    assert names[keep["name"]]["quantity"] == 3
    assert drop["name"] not in names, "dismissed suggestions must never enter box_items"

    statuses = {
        row["id"]: row["status"]
        for row in conn.execute("SELECT id, status FROM detection_suggestions WHERE box_id = ?", (box_id,))
    }
    assert statuses[keep["id"]] == "confirmed"
    assert statuses[drop["id"]] == "dismissed"

    history_actions = [
        row["action"]
        for row in conn.execute("SELECT action FROM edit_history WHERE entity_type = 'detection' ORDER BY id")
    ]
    assert "confirmed" in history_actions
    assert "dismissed" in history_actions
    conn.close()


def test_confirm_is_idempotent_and_dismissed_cannot_be_confirmed():
    reset_db()
    client = TestClient(app)
    created = client.post("/api/capture/containers", data={"room_name": "office"}).json()
    box_id = created["container_id"]
    suggestions = client.post(
        f"/api/boxes/{box_id}/photos",
        files={"photos": ("charger_cable.jpg", b"fake", "image/jpeg")},
    ).json()["suggestions"]

    conn = db_conn()
    first = confirm_detection(conn, suggestions[0]["id"], status="confirmed")
    second = confirm_detection(conn, suggestions[0]["id"], status="confirmed")
    assert first is not None and second is None, "double confirm must not duplicate items"

    assert dismiss_detection(conn, suggestions[1]["id"]) is True
    assert confirm_detection(conn, suggestions[1]["id"]) is None, "dismissed suggestion cannot be confirmed"
    conn.commit()

    box = get_box(conn, box_id=box_id)
    assert len(box["items"]) == 1
    conn.close()

    # HTTP guards mirror the repository behavior.
    assert client.post(f"/api/detections/{suggestions[0]['id']}/confirm").status_code == 404
    assert client.delete(f"/api/detections/{suggestions[1]['id']}").status_code == 404


def test_photos_endpoint_reports_vision_error_but_saves_photo(monkeypatch):
    reset_db()

    class ExplodingProvider(vision.VisionProvider):
        def detect(self, image_path, original_name=None):
            raise VisionError("Could not reach the local Ollama service.")

    monkeypatch.setattr("app.main.get_provider", lambda: ExplodingProvider())
    client = TestClient(app)
    created = client.post("/api/capture/containers", data={"room_name": "attic"}).json()
    box_id = created["container_id"]

    response = client.post(
        f"/api/boxes/{box_id}/photos",
        files={"photos": ("tent.jpg", b"fake", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["suggestions"] == []
    assert "Ollama" in body["vision_error"]

    conn = db_conn()
    box = get_box(conn, box_id=box_id)
    assert len(box["photos"]) == 1, "photo must still be saved when vision fails"
    conn.close()


# ---------------------------------------------------------------------------
# Glasses import pipeline: inbox -> container -> merged item list
# ---------------------------------------------------------------------------

def _write_inbox(name: str) -> Path:
    from app.settings import IMPORT_DIR
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = IMPORT_DIR / name
    path.write_bytes(b"fake image bytes")
    return path


def test_import_inbox_to_new_container_with_merged_list():
    reset_db()
    from app.settings import IMPORT_DIR
    for leftover in IMPORT_DIR.glob("*"):
        leftover.unlink()
    _write_inbox("gloves_scarf.jpg")
    _write_inbox("gloves_hat.jpg")

    client = TestClient(app)
    listing = client.get("/api/import/photos").json()
    assert {p["filename"] for p in listing["photos"]} == {"gloves_scarf.jpg", "gloves_hat.jpg"}

    response = client.post(
        "/api/import",
        json={
            "filenames": ["gloves_scarf.jpg", "gloves_hat.jpg"],
            "new_container": {"name": "", "room_name": "closet"},
            "merge": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["merged"] is True
    assert sorted(body["imported"]) == ["gloves_hat.jpg", "gloves_scarf.jpg"]

    # "gloves" is detected in both photos and must be merged into one entry
    # with summed quantity and the duplicate suggestion ids carried along.
    by_name = {entry["name"]: entry for entry in body["suggestions"]}
    assert "gloves" in by_name
    assert by_name["gloves"]["quantity"] == 2
    assert len(by_name["gloves"]["merge_ids"]) == 1

    # Inbox files are moved into permanent photo storage.
    assert not any(IMPORT_DIR.glob("*.jpg"))
    conn = db_conn()
    box = get_box(conn, box_id=body["container_id"])
    assert box["container_type"] == "box"
    assert len(box["photos"]) == 2
    assert box["labels"]
    conn.close()

    # Confirming the merged entry creates ONE inventory row and resolves
    # the duplicate suggestion without creating another.
    merged = by_name["gloves"]
    result = client.post(
        "/api/detections/confirm-batch",
        json={"confirm": [{"id": merged["id"], "quantity": merged["quantity"], "merge_ids": merged["merge_ids"]}]},
    ).json()
    assert result["confirmed"][0]["merged_duplicates"] == 1

    conn = db_conn()
    items = [row for row in conn.execute("SELECT item_name, quantity FROM box_items WHERE box_id = ?", (body["container_id"],))]
    gloves_rows = [item for item in items if item["item_name"] == "gloves"]
    assert len(gloves_rows) == 1
    assert gloves_rows[0]["quantity"] == 2
    statuses = [row["status"] for row in conn.execute(
        "SELECT status FROM detection_suggestions WHERE id IN (?, ?)", (merged["id"], merged["merge_ids"][0])
    )]
    assert statuses == ["confirmed", "confirmed"]
    conn.close()


def test_import_rejects_path_traversal_and_unknown_files():
    reset_db()
    client = TestClient(app)
    created = client.post("/api/capture/containers", data={"room_name": "attic"}).json()
    for bad in ["../secret.jpg", "missing.jpg", "notes.txt"]:
        response = client.post("/api/import", json={"filenames": [bad], "box_id": created["container_id"]})
        assert response.status_code == 400, bad


def test_import_requires_filenames_and_valid_container():
    reset_db()
    client = TestClient(app)
    assert client.post("/api/import", json={"filenames": []}).status_code == 400
    _write_inbox("lamp.jpg")
    assert client.post("/api/import", json={"filenames": ["lamp.jpg"], "box_id": 9999}).status_code == 404


def test_import_page_renders():
    reset_db()
    client = TestClient(app)
    response = client.get("/import")
    assert response.status_code == 200
    assert "Import from inbox" in response.text
