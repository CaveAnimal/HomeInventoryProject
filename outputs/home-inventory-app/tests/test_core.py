import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["HOME_INVENTORY_DATA"] = str(ROOT / "test-data")
os.environ["HOME_INVENTORY_DB"] = str(ROOT / "test-data" / "test.sqlite3")
os.environ["VISION_PROVIDER"] = "heuristic"

from fastapi.testclient import TestClient

from app.database import connect, migrate
from app.main import app
from app.repository import add_item_to_box, create_box, get_box, move_box_item
from app.services.search import search_items


def reset_db():
    db_path = Path(os.environ["HOME_INVENTORY_DB"])
    if db_path.exists():
        db_path.unlink()
    migrate(db_path)


def test_create_search_and_move_item():
    reset_db()
    conn = connect(Path(os.environ["HOME_INVENTORY_DB"]))
    box_a = create_box(conn, "Basement-Box-001", "basement", 3.5, 8, 2)
    box_b = create_box(conn, "Garage-Box-001", "garage", 1, 2, 0)
    item_id = add_item_to_box(conn, box_a, "extension cord", quantity=2, tags="tools,cables")
    conn.commit()

    results = search_items(conn, "cord")
    assert results[0]["box_name"] == "Basement-Box-001"
    assert results[0]["north_ft"] == 3.5

    move_box_item(conn, item_id, box_b)
    conn.commit()
    moved = search_items(conn, "extension cord")[0]
    assert moved["box_name"] == "Garage-Box-001"
    conn.close()


def test_http_create_box_generates_qr_and_suggestions():
    reset_db()
    client = TestClient(app)
    response = client.post(
        "/api/boxes",
        data={"name": "Office-Box-001", "room_name": "office", "north_ft": "4", "east_ft": "5", "elevation_ft": "1"},
        files={"photos": ("charger_cable.jpg", b"fake image bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    box_id = response.json()["box_id"]
    conn = connect(Path(os.environ["HOME_INVENTORY_DB"]))
    box = get_box(conn, box_id=box_id)
    assert box["name"] == "Office-Box-001"
    assert box["labels"]
    assert box["suggestions"]
    conn.close()


def test_search_page_mentions_exact_location():
    reset_db()
    conn = connect(Path(os.environ["HOME_INVENTORY_DB"]))
    create_box(conn, "Basement-Box-014", "basement storage room", 3.5, 8, 2)
    add_item_to_box(conn, 1, "winter gloves", quantity=2)
    conn.commit()
    conn.close()
    client = TestClient(app)
    response = client.get("/search?q=winter+gloves")
    assert response.status_code == 200
    assert "3.5 ft from north wall" in response.text


def test_public_qr_box_page_lists_items():
    reset_db()
    conn = connect(Path(os.environ["HOME_INVENTORY_DB"]))
    box_id = create_box(conn, "Basement-Box-014", "basement storage room", 3.5, 8, 2)
    add_item_to_box(conn, box_id, "winter gloves", quantity=2)
    public_id = get_box(conn, box_id=box_id)["public_id"]
    conn.commit()
    conn.close()

    client = TestClient(app)
    response = client.get(f"/box/{public_id}")
    assert response.status_code == 200
    assert "winter gloves" in response.text
    assert "basement storage room" in response.text
