import json
import re
import sqlite3
import uuid
from typing import Any


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "container"


def rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cur.fetchall()]


def row(cur: sqlite3.Cursor) -> dict[str, Any] | None:
    found = cur.fetchone()
    return dict(found) if found else None


def record_history(conn: sqlite3.Connection, entity_type: str, entity_id: int, action: str, before=None, after=None) -> None:
    conn.execute(
        "INSERT INTO edit_history(entity_type, entity_id, action, before_json, after_json) VALUES (?, ?, ?, ?, ?)",
        (entity_type, entity_id, action, json.dumps(before or {}), json.dumps(after or {})),
    )


def create_box(
    conn: sqlite3.Connection,
    name: str | None,
    room_name: str,
    north_ft: float,
    east_ft: float,
    elevation_ft: float,
    notes: str = "",
    tags: str = "",
    inaccessible: int = 0,
    size: str = "",
    stack_position: str = "",
    container_type: str = "box",
    parent_box_id: int | None = None,
) -> int:
    public_id = uuid.uuid4().hex[:12]
    container_type = normalize_container_type(container_type)
    if not name:
        count = conn.execute("SELECT COUNT(*) AS n FROM boxes").fetchone()["n"] + 1
        base = slugify(room_name).replace("-", " ").title().replace(" ", "-")
        suffix = container_type.replace("_", " ").title().replace(" ", "-")
        name = f"{base}-{suffix}-{count:03d}"
    cur = conn.execute(
        """INSERT INTO boxes(parent_box_id, public_id, name, container_type, notes, tags, inaccessible, size, stack_position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (parent_box_id, public_id, name, container_type, notes, tags, inaccessible, size, stack_position),
    )
    box_id = cur.lastrowid
    conn.execute(
        """INSERT INTO box_locations(box_id, room_name, north_ft, east_ft, elevation_ft)
           VALUES (?, ?, ?, ?, ?)""",
        (box_id, room_name, north_ft, east_ft, elevation_ft),
    )
    record_history(conn, "container", box_id, "created", after={"name": name, "room_name": room_name, "container_type": container_type, "parent_box_id": parent_box_id})
    return int(box_id)


def create_container(
    conn: sqlite3.Connection,
    name: str | None,
    room_name: str,
    north_ft: float,
    east_ft: float,
    elevation_ft: float,
    notes: str = "",
    tags: str = "",
    inaccessible: int = 0,
    size: str = "",
    stack_position: str = "",
    container_type: str = "box",
    parent_box_id: int | None = None,
) -> int:
    return create_box(
        conn,
        name,
        room_name,
        north_ft,
        east_ft,
        elevation_ft,
        notes,
        tags,
        inaccessible,
        size,
        stack_position,
        container_type,
        parent_box_id,
    )


def list_boxes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    containers = rows(
        conn.execute(
            """SELECT b.*, parent.name AS parent_name, l.room_name, l.north_ft, l.east_ft, l.elevation_ft,
                      COUNT(DISTINCT bi.id) AS item_count, COUNT(DISTINCT bp.id) AS photo_count
               FROM boxes b
               LEFT JOIN boxes parent ON parent.id = b.parent_box_id
               JOIN box_locations l ON l.box_id = b.id
               LEFT JOIN box_items bi ON bi.box_id = b.id
               LEFT JOIN box_photos bp ON bp.box_id = b.id
               GROUP BY b.id
               ORDER BY b.updated_at DESC"""
        )
    )
    for container in containers:
        container["path"] = container_path(conn, container["id"])
    return containers


def list_containers(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return list_boxes(conn)


def get_box(conn: sqlite3.Connection, box_id: int | None = None, public_id: str | None = None) -> dict[str, Any] | None:
    where = "b.id = ?" if box_id is not None else "b.public_id = ?"
    value = box_id if box_id is not None else public_id
    found = row(
        conn.execute(
            f"""SELECT b.*, l.room_name, l.north_ft, l.east_ft, l.elevation_ft
                FROM boxes b JOIN box_locations l ON l.box_id = b.id
                WHERE {where}""",
            (value,),
        )
    )
    if not found:
        return None
    found["path"] = container_path(conn, found["id"])
    found["children"] = rows(
        conn.execute(
            """SELECT b.*, l.room_name, l.north_ft, l.east_ft, l.elevation_ft,
                      COUNT(DISTINCT bi.id) AS item_count, COUNT(DISTINCT bp.id) AS photo_count
               FROM boxes b
               JOIN box_locations l ON l.box_id = b.id
               LEFT JOIN box_items bi ON bi.box_id = b.id
               LEFT JOIN box_photos bp ON bp.box_id = b.id
               WHERE b.parent_box_id = ?
               GROUP BY b.id
               ORDER BY b.name""",
            (found["id"],),
        )
    )
    found["items"] = rows(conn.execute("SELECT * FROM box_items WHERE box_id = ? ORDER BY priority DESC, item_name", (found["id"],)))
    found["photos"] = rows(conn.execute("SELECT * FROM box_photos WHERE box_id = ? ORDER BY created_at DESC", (found["id"],)))
    found["suggestions"] = rows(
        conn.execute("SELECT * FROM detection_suggestions WHERE box_id = ? AND status = 'suggested' ORDER BY confidence DESC", (found["id"],))
    )
    found["labels"] = rows(conn.execute("SELECT * FROM labels WHERE box_id = ? ORDER BY created_at DESC", (found["id"],)))
    return found


def get_container(conn: sqlite3.Connection, container_id: int | None = None, public_id: str | None = None) -> dict[str, Any] | None:
    return get_box(conn, box_id=container_id, public_id=public_id)


def container_path(conn: sqlite3.Connection, box_id: int) -> str:
    names: list[str] = []
    current = box_id
    seen: set[int] = set()
    while current and current not in seen:
        seen.add(current)
        found = row(conn.execute("SELECT id, parent_box_id, name FROM boxes WHERE id = ?", (current,)))
        if not found:
            break
        names.append(found["name"])
        current = found["parent_box_id"]
    return " -> ".join(reversed(names))


def update_box_location(conn: sqlite3.Connection, box_id: int, room_name: str, north_ft: float, east_ft: float, elevation_ft: float) -> None:
    before = row(conn.execute("SELECT * FROM box_locations WHERE box_id = ?", (box_id,)))
    conn.execute(
        """UPDATE box_locations
           SET room_name = ?, north_ft = ?, east_ft = ?, elevation_ft = ?, updated_at = CURRENT_TIMESTAMP
           WHERE box_id = ?""",
        (room_name, north_ft, east_ft, elevation_ft, box_id),
    )
    conn.execute("UPDATE boxes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (box_id,))
    record_history(conn, "box", box_id, "location_updated", before=before, after=locals())


def update_box(conn: sqlite3.Connection, box_id: int, **fields: Any) -> None:
    allowed = {k: v for k, v in fields.items() if k in {"name", "notes", "tags", "inaccessible", "size", "stack_position", "container_type", "parent_box_id"}}
    if not allowed:
        return
    if "container_type" in allowed:
        allowed["container_type"] = normalize_container_type(str(allowed["container_type"]))
    if allowed.get("parent_box_id") in {"", "None", None}:
        allowed["parent_box_id"] = None
    before = row(conn.execute("SELECT * FROM boxes WHERE id = ?", (box_id,)))
    assignments = ", ".join(f"{key} = ?" for key in allowed)
    conn.execute(f"UPDATE boxes SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (*allowed.values(), box_id))
    record_history(conn, "container", box_id, "updated", before=before, after=allowed)


def update_container(conn: sqlite3.Connection, container_id: int, **fields: Any) -> None:
    update_box(conn, container_id, **fields)


def add_photo(conn: sqlite3.Connection, box_id: int, filename: str, original_filename: str, content_type: str) -> int:
    cur = conn.execute(
        "INSERT INTO box_photos(box_id, filename, original_filename, content_type) VALUES (?, ?, ?, ?)",
        (box_id, filename, original_filename, content_type),
    )
    record_history(conn, "box", box_id, "photo_added", after={"filename": filename})
    return int(cur.lastrowid)


def add_detection(conn: sqlite3.Connection, box_id: int, photo_id: int | None, item_name: str, confidence: float, quantity: int = 1, category: str = "", notes: str = "") -> int:
    cur = conn.execute(
        """INSERT INTO detection_suggestions(box_id, photo_id, item_name, quantity, confidence, category, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (box_id, photo_id, item_name.strip(), quantity, confidence, category, notes),
    )
    return int(cur.lastrowid)


def add_item_to_box(
    conn: sqlite3.Connection,
    box_id: int,
    item_name: str,
    quantity: int = 1,
    status: str = "confirmed",
    confidence: float = 1.0,
    category: str = "",
    notes: str = "",
    tags: str = "",
    priority: int = 0,
) -> int:
    cur = conn.execute(
        """INSERT INTO box_items(box_id, item_name, normalized_name, quantity, status, confidence, category, notes, tags, priority)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (box_id, item_name.strip(), normalize(item_name), quantity, status, confidence, category, notes, tags, priority),
    )
    conn.execute("UPDATE boxes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (box_id,))
    record_history(conn, "box_item", int(cur.lastrowid), "created", after={"box_id": box_id, "item_name": item_name})
    return int(cur.lastrowid)


def update_box_item(conn: sqlite3.Connection, item_id: int, **fields: Any) -> None:
    allowed = {k: v for k, v in fields.items() if k in {"item_name", "quantity", "status", "confidence", "category", "notes", "tags", "priority"}}
    if "item_name" in allowed:
        allowed["normalized_name"] = normalize(str(allowed["item_name"]))
    before = row(conn.execute("SELECT * FROM box_items WHERE id = ?", (item_id,)))
    assignments = ", ".join(f"{key} = ?" for key in allowed)
    conn.execute(f"UPDATE box_items SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (*allowed.values(), item_id))
    record_history(conn, "box_item", item_id, "updated", before=before, after=allowed)


def delete_box_item(conn: sqlite3.Connection, item_id: int) -> None:
    before = row(conn.execute("SELECT * FROM box_items WHERE id = ?", (item_id,)))
    conn.execute("DELETE FROM box_items WHERE id = ?", (item_id,))
    record_history(conn, "box_item", item_id, "deleted", before=before)


def move_box_item(conn: sqlite3.Connection, item_id: int, target_box_id: int) -> None:
    before = row(conn.execute("SELECT * FROM box_items WHERE id = ?", (item_id,)))
    conn.execute("UPDATE box_items SET box_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (target_box_id, item_id))
    record_history(conn, "box_item", item_id, "moved", before=before, after={"box_id": target_box_id})


def confirm_detection(conn: sqlite3.Connection, suggestion_id: int) -> int:
    suggestion = row(conn.execute("SELECT * FROM detection_suggestions WHERE id = ?", (suggestion_id,)))
    item_id = add_item_to_box(
        conn,
        suggestion["box_id"],
        suggestion["item_name"],
        quantity=suggestion["quantity"],
        status="likely",
        confidence=suggestion["confidence"],
        category=suggestion["category"] or "",
        notes=suggestion["notes"] or "",
    )
    conn.execute("UPDATE detection_suggestions SET status = 'confirmed' WHERE id = ?", (suggestion_id,))
    record_history(conn, "detection", suggestion_id, "confirmed", after={"box_item_id": item_id})
    return item_id


def normalize(value: str) -> str:
    stop = {"a", "an", "the", "of", "for", "and", "with"}
    words = re.findall(r"[a-z0-9]+", value.lower())
    return " ".join(word for word in words if word not in stop)


def normalize_container_type(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", (value or "box").lower()).strip("_")
    return normalized or "box"
