"""Regression tests for the nightly deep-scan reprocessing pass.

Covers:
- add_detection() records source_model/pass_type (default 'live').
- list_photos_pending_deep_scan()/mark_photo_deep_scanned() track per-model
  reprocessing state, including re-pending on a model change.
- app.nightly_reprocess.run() adds reprocess-tagged suggestions without
  touching the original live suggestions, and is idempotent per model.
- Errors (missing file, provider failure) are recorded, not raised.
- /api/reprocess/status reports the current model and pending count.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["HOME_INVENTORY_DATA"] = str(ROOT / "test-data")
os.environ["HOME_INVENTORY_DB"] = str(ROOT / "test-data" / "test.sqlite3")
os.environ["VISION_PROVIDER"] = "heuristic"

from PIL import Image
from fastapi.testclient import TestClient

from app import nightly_reprocess, scheduler
from app.database import connect, migrate
from app.main import app
from app.repository import (
    add_detection,
    add_photo,
    create_box,
    get_setting,
    list_photos_pending_deep_scan,
    mark_photo_deep_scanned,
    set_setting,
)
from app.services import vision
from app.settings import PHOTO_DIR


def reset_db():
    db_path = Path(os.environ["HOME_INVENTORY_DB"])
    if db_path.exists():
        db_path.unlink()
    migrate(db_path)


def db_conn():
    return connect(Path(os.environ["HOME_INVENTORY_DB"]))


def _make_photo(conn, box_id: int, name: str = "overview.jpg") -> int:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{box_id}-{name}"
    Image.new("RGB", (20, 20), color="blue").save(PHOTO_DIR / filename)
    return add_photo(conn, box_id, filename, name, "image/jpeg")


def _fake_post(payload_text: str):
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"response": payload_text, "choices": [{"message": {"content": payload_text}}]}

    def fake(*args, **kwargs):
        return FakeResponse()

    return fake


def test_add_detection_defaults_to_live_pass():
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    suggestion_id = add_detection(conn, box_id, None, "hammer", 0.8)
    row = conn.execute("SELECT source_model, pass_type FROM detection_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    assert row["source_model"] == ""
    assert row["pass_type"] == "live"
    conn.close()


def test_add_detection_records_reprocess_source():
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    suggestion_id = add_detection(conn, box_id, None, "hammer", 0.8, source_model="qwen3-vl:30b", pass_type="reprocess")
    row = conn.execute("SELECT source_model, pass_type FROM detection_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    assert row["source_model"] == "qwen3-vl:30b"
    assert row["pass_type"] == "reprocess"
    conn.close()


def test_pending_deep_scan_tracks_per_model_and_re_pends_on_model_change():
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    photo_id = _make_photo(conn, box_id)
    conn.commit()

    pending = list_photos_pending_deep_scan(conn, "qwen3-vl:30b")
    assert [p["id"] for p in pending] == [photo_id]

    mark_photo_deep_scanned(conn, photo_id, "qwen3-vl:30b")
    conn.commit()
    assert list_photos_pending_deep_scan(conn, "qwen3-vl:30b") == []

    # Switching the reprocess model makes the photo pending again.
    pending_new_model = list_photos_pending_deep_scan(conn, "qwen3-vl:32b")
    assert [p["id"] for p in pending_new_model] == [photo_id]
    conn.close()


def test_nightly_reprocess_run_adds_suggestions_and_is_idempotent(monkeypatch):
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    photo_id = _make_photo(conn, box_id)
    live_suggestion_id = add_detection(conn, box_id, photo_id, "hammer", 0.6, source_model="qwen3-vl:8b-instruct", pass_type="live")
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        vision.requests, "post",
        _fake_post('{"items":[{"name":"cordless drill","quantity":1,"confidence":0.91,"category":"Tools & Hardware","notes":""}]}'),
    )

    summary = nightly_reprocess.run(model="qwen3-vl:30b")
    assert summary["photos_processed"] == 1
    assert summary["suggestions_added"] == 1
    assert summary["errors"] == []

    conn = db_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM detection_suggestions WHERE box_id = ? ORDER BY id", (box_id,))]
    assert len(rows) == 2, "reprocess must add alongside, not replace, the live suggestion"
    live = next(r for r in rows if r["id"] == live_suggestion_id)
    assert live["pass_type"] == "live" and live["status"] == "suggested"
    deep = next(r for r in rows if r["id"] != live_suggestion_id)
    assert deep["pass_type"] == "reprocess"
    assert deep["source_model"] == "qwen3-vl:30b"
    assert deep["item_name"] == "cordless drill"

    photo = conn.execute("SELECT deep_scan_model FROM box_photos WHERE id = ?", (photo_id,)).fetchone()
    assert photo["deep_scan_model"] == "qwen3-vl:30b"
    conn.close()

    # Running again for the same model is a no-op: nothing left pending.
    second_summary = nightly_reprocess.run(model="qwen3-vl:30b")
    assert second_summary["photos_pending"] == 0
    assert second_summary["photos_processed"] == 0

    conn = db_conn()
    count = conn.execute("SELECT COUNT(*) AS n FROM detection_suggestions WHERE box_id = ?", (box_id,)).fetchone()["n"]
    assert count == 2, "idempotent re-run must not add duplicate suggestions"
    conn.close()


def test_nightly_reprocess_records_missing_file_as_error_without_raising():
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    photo_id = add_photo(conn, box_id, "does-not-exist.jpg", "does-not-exist.jpg", "image/jpeg")
    conn.commit()
    conn.close()

    summary = nightly_reprocess.run(model="qwen3-vl:30b")
    assert summary["photos_processed"] == 0
    assert summary["errors"] == [{"photo_id": photo_id, "error": "file missing on disk"}]


def test_nightly_reprocess_records_vision_error_without_raising(monkeypatch):
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    photo_id = _make_photo(conn, box_id)
    conn.commit()
    conn.close()

    import requests as requests_module

    def boom(*args, **kwargs):
        raise requests_module.exceptions.ConnectionError("refused")

    monkeypatch.setattr(vision.requests, "post", boom)
    summary = nightly_reprocess.run(model="qwen3-vl:30b")
    assert summary["photos_processed"] == 0
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["photo_id"] == photo_id


def test_reprocess_status_endpoint_reports_model_and_pending_count():
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Test-Box", "garage", 0, 0, 0)
    _make_photo(conn, box_id)
    conn.commit()
    conn.close()

    client = TestClient(app)
    response = client.get("/api/reprocess/status")
    assert response.status_code == 200
    body = response.json()
    assert body["pending_count"] == 1
    assert body["model"]
    assert body["armed"] is False
    assert body["last_run_date"] is None


# ---------------------------------------------------------------------------
# Admin-page arm/disarm toggle + in-process scheduler tick
# ---------------------------------------------------------------------------

def test_arm_and_disarm_endpoints_toggle_status():
    reset_db()
    client = TestClient(app)

    assert client.get("/api/reprocess/status").json()["armed"] is False

    armed = client.post("/api/reprocess/arm")
    assert armed.status_code == 200
    assert armed.json()["armed"] is True
    assert client.get("/api/reprocess/status").json()["armed"] is True

    disarmed = client.post("/api/reprocess/disarm")
    assert disarmed.json()["armed"] is False
    assert client.get("/api/reprocess/status").json()["armed"] is False


def test_get_set_setting_roundtrip_and_default():
    reset_db()
    conn = db_conn()
    assert get_setting(conn, "missing_key", "fallback") == "fallback"
    set_setting(conn, "deep_scan_armed", "true")
    conn.commit()
    assert get_setting(conn, "deep_scan_armed") == "true"
    # Upsert overwrites rather than erroring on a duplicate key.
    set_setting(conn, "deep_scan_armed", "false")
    conn.commit()
    assert get_setting(conn, "deep_scan_armed") == "false"
    conn.close()


def test_scheduler_tick_is_noop_when_not_armed(monkeypatch):
    reset_db()
    calls = []
    monkeypatch.setattr(nightly_reprocess, "run", lambda **kwargs: calls.append(kwargs))
    scheduler._tick()
    assert calls == []


def test_scheduler_tick_is_noop_outside_scheduled_hour(monkeypatch):
    reset_db()
    conn = db_conn()
    set_setting(conn, scheduler.ARMED_KEY, "true")
    conn.commit()
    conn.close()

    calls = []
    monkeypatch.setattr(nightly_reprocess, "run", lambda **kwargs: calls.append(kwargs))

    class FakeDatetime:
        @staticmethod
        def now():
            import datetime as real_datetime
            return real_datetime.datetime.now().replace(hour=(scheduler.DEEP_SCAN_HOUR + 12) % 24)

    monkeypatch.setattr(scheduler, "datetime", FakeDatetime)
    scheduler._tick()
    assert calls == []
    conn = db_conn()
    assert get_setting(conn, scheduler.ARMED_KEY) == "true", "must stay armed until it actually runs"
    conn.close()


def test_scheduler_tick_runs_once_during_scheduled_hour_then_disarms(monkeypatch):
    reset_db()
    conn = db_conn()
    set_setting(conn, scheduler.ARMED_KEY, "true")
    conn.commit()
    conn.close()

    calls = []
    monkeypatch.setattr(nightly_reprocess, "run", lambda **kwargs: calls.append(kwargs))

    class FakeDatetime:
        @staticmethod
        def now():
            import datetime as real_datetime
            return real_datetime.datetime.now().replace(hour=scheduler.DEEP_SCAN_HOUR)

    monkeypatch.setattr(scheduler, "datetime", FakeDatetime)
    scheduler._tick()
    assert len(calls) == 1

    conn = db_conn()
    assert get_setting(conn, scheduler.ARMED_KEY) == "false", "one-shot scan disarms itself after running"
    from datetime import date
    assert get_setting(conn, scheduler.LAST_RUN_KEY) == date.today().isoformat()
    conn.close()

    # A second tick within the same hour/day must not run again.
    scheduler._tick()
    assert len(calls) == 1
