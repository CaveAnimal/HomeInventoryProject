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
    record_history(
        conn,
        "box",
        box_id,
        "location_updated",
        before=before,
        after={"room_name": room_name, "north_ft": north_ft, "east_ft": east_ft, "elevation_ft": elevation_ft},
    )


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


def add_detection(
    conn: sqlite3.Connection,
    box_id: int,
    photo_id: int | None,
    item_name: str,
    confidence: float,
    quantity: int = 1,
    category: str = "",
    notes: str = "",
    source_model: str = "",
    pass_type: str = "live",
) -> int:
    cur = conn.execute(
        """INSERT INTO detection_suggestions(box_id, photo_id, item_name, quantity, confidence, category, notes, source_model, pass_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (box_id, photo_id, item_name.strip(), quantity, confidence, category, notes, source_model, pass_type),
    )
    return int(cur.lastrowid)


def list_photos_pending_deep_scan(conn: sqlite3.Connection, model: str) -> list[dict[str, Any]]:
    """Photos not yet reprocessed by ``model`` (the nightly deep-scan pass).

    A photo previously scanned by a *different* model (e.g. after upgrading
    OLLAMA_REPROCESS_VISION_MODEL) is treated as pending again, so switching
    models naturally re-scans everything with the new one.
    """
    return rows(
        conn.execute(
            "SELECT * FROM box_photos WHERE deep_scan_model != ? ORDER BY created_at",
            (model,),
        )
    )


def mark_photo_deep_scanned(conn: sqlite3.Connection, photo_id: int, model: str) -> None:
    conn.execute(
        "UPDATE box_photos SET deep_scan_model = ?, deep_scanned_at = CURRENT_TIMESTAMP WHERE id = ?",
        (model, photo_id),
    )


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


def get_box_item(conn: sqlite3.Connection, item_id: int) -> dict[str, Any] | None:
    return row(conn.execute("SELECT * FROM box_items WHERE id = ?", (item_id,)))


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


def confirm_detection(conn: sqlite3.Connection, suggestion_id: int, status: str = "likely", quantity: int | None = None) -> int | None:
    """Promote a suggested detection into ``box_items``.

    Returns the new item id, or ``None`` when the suggestion does not exist
    or is no longer in 'suggested' state (already confirmed/dismissed), so
    double-taps never create duplicate inventory rows.
    """
    suggestion = row(conn.execute("SELECT * FROM detection_suggestions WHERE id = ?", (suggestion_id,)))
    if not suggestion or suggestion["status"] != "suggested":
        return None
    final_quantity = max(1, int(quantity)) if quantity is not None else suggestion["quantity"]
    item_id = add_item_to_box(
        conn,
        suggestion["box_id"],
        suggestion["item_name"],
        quantity=final_quantity,
        status=status,
        confidence=suggestion["confidence"],
        category=suggestion["category"] or "",
        notes=suggestion["notes"] or "",
    )
    conn.execute("UPDATE detection_suggestions SET status = 'confirmed' WHERE id = ?", (suggestion_id,))
    record_history(conn, "detection", suggestion_id, "confirmed", after={"box_item_id": item_id, "quantity": final_quantity})
    return item_id


def dismiss_detection(conn: sqlite3.Connection, suggestion_id: int) -> bool:
    """Mark a suggestion dismissed (auditable; never enters box_items).

    Returns False when the suggestion does not exist or was already resolved.
    """
    suggestion = row(conn.execute("SELECT * FROM detection_suggestions WHERE id = ?", (suggestion_id,)))
    if not suggestion or suggestion["status"] != "suggested":
        return False
    conn.execute("UPDATE detection_suggestions SET status = 'dismissed' WHERE id = ?", (suggestion_id,))
    record_history(conn, "detection", suggestion_id, "dismissed", before={"item_name": suggestion["item_name"]})
    return True


def resolve_merged_detections(conn: sqlite3.Connection, duplicate_ids: list[int], item_id: int, primary_id: int) -> int:
    """Mark duplicate suggestions as confirmed-by-merge (no extra box_items).

    Used when several photos of the same container detect the same item and
    the user confirms them as one row.  Keeps the audit trail accurate:
    each duplicate is recorded as merged into the primary suggestion's item.
    Returns how many duplicates were resolved.
    """
    resolved = 0
    for duplicate_id in duplicate_ids:
        suggestion = row(conn.execute("SELECT * FROM detection_suggestions WHERE id = ?", (duplicate_id,)))
        if not suggestion or suggestion["status"] != "suggested" or duplicate_id == primary_id:
            continue
        conn.execute("UPDATE detection_suggestions SET status = 'confirmed' WHERE id = ?", (duplicate_id,))
        record_history(conn, "detection", duplicate_id, "merged", after={"box_item_id": item_id, "merged_into_suggestion": primary_id})
        resolved += 1
    return resolved


def add_cost_estimate(
    conn: sqlite3.Connection,
    box_item_id: int,
    estimated_cost_usd: float | None,
    confidence: float = 0.5,
    source_title: str = "",
    source_url: str = "",
    quantity: int = 1,
) -> int:
    """Append a cost-estimate history row for ``box_item_id``.

    Insert-only: cost estimates are never updated or overwritten in place,
    so price history stays auditable. Use ``latest_cost_estimate()`` to read
    the current value. ``quantity`` snapshots the item's on-hand quantity at
    estimate time; the estimated cost is per unit.
    """
    cur = conn.execute(
        """INSERT INTO cost_estimates(box_item_id, estimated_cost_usd, confidence, source_title, source_url, quantity)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (box_item_id, estimated_cost_usd, confidence, source_title, source_url, quantity),
    )
    record_history(
        conn,
        "box_item",
        box_item_id,
        "cost_estimated",
        after={
            "estimated_cost_usd": estimated_cost_usd,
            "confidence": confidence,
            "source_url": source_url,
            "quantity": quantity,
        },
    )
    return int(cur.lastrowid)


def list_cost_estimates_for_item(conn: sqlite3.Connection, box_item_id: int) -> list[dict[str, Any]]:
    return rows(
        conn.execute(
            "SELECT * FROM cost_estimates WHERE box_item_id = ? ORDER BY created_at DESC, id DESC",
            (box_item_id,),
        )
    )


def latest_cost_estimate(conn: sqlite3.Connection, box_item_id: int) -> dict[str, Any] | None:
    return row(
        conn.execute(
            "SELECT * FROM cost_estimates WHERE box_item_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (box_item_id,),
        )
    )


def count_cost_estimates_this_month(conn: sqlite3.Connection) -> int:
    """Count cost-estimate lookups recorded in the current UTC calendar month.

    Derived query over ``cost_estimates.created_at`` (D-006) rather than a
    separate counter table/row -- ``created_at`` is populated by SQLite's
    ``CURRENT_TIMESTAMP`` (UTC), so comparing its year-month against
    ``strftime('%Y-%m', 'now')`` (also UTC) gives a counter that resets
    naturally at each month boundary with no extra bookkeeping.
    """
    found = row(
        conn.execute(
            "SELECT COUNT(*) AS n FROM cost_estimates "
            "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        )
    )
    return int(found["n"]) if found else 0


def record_cost_lookup_attempt(conn: sqlite3.Connection) -> None:
    """Record one outbound cost-lookup attempt (QW-5), whatever its outcome."""
    conn.execute("INSERT INTO cost_lookup_attempts DEFAULT VALUES")


def count_cost_lookup_attempts_this_month(conn: sqlite3.Connection) -> int:
    """Outbound lookup attempts (successes and failures) in the current UTC month.

    This is what the monthly budget guard counts (QW-5). Migration 008 copied
    earlier estimates in as attempts, so the count is continuous across the upgrade.
    """
    found = row(
        conn.execute(
            "SELECT COUNT(*) AS n FROM cost_lookup_attempts "
            "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        )
    )
    return int(found["n"]) if found else 0


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    found = row(conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)))
    return found["value"] if found else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """INSERT INTO app_settings(key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP""",
        (key, value),
    )


def normalize(value: str) -> str:
    stop = {"a", "an", "the", "of", "for", "and", "with"}
    words = re.findall(r"[a-z0-9]+", value.lower())
    return " ".join(word for word in words if word not in stop)


def normalize_container_type(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", (value or "box").lower()).strip("_")
    return normalized or "box"



# ---------------------------------------------------------------------------
# WS-1: lifecycle status, loans and verification (PD-1, PD-2)
# ---------------------------------------------------------------------------

LIFECYCLE_STATUSES = (
    "in_home",
    "loaned",
    "in_repair",
    "in_vehicle",
    "in_storage_offsite",
    "donated",
    "sold",
    "given_away",
    "discarded",
    "missing",
)
LIFECYCLE_LABELS = {
    "in_home": "In home",
    "loaned": "Loaned",
    "in_repair": "In repair",
    "in_vehicle": "In vehicle",
    "in_storage_offsite": "In off-site storage",
    "donated": "Donated",
    "sold": "Sold",
    "given_away": "Given away",
    "discarded": "Discarded",
    "missing": "Missing",
}
# Statuses meaning the item has left the household for good.
GONE_STATUSES = ("donated", "sold", "given_away", "discarded")
# Statuses meaning the item still belongs to the household but isn't in the house.
OUT_OF_HOUSE_STATUSES = ("loaned", "in_repair", "in_vehicle", "in_storage_offsite")


class LifecycleError(ValueError):
    """A status or loan change that isn't allowed. The message is safe to show."""


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def get_open_loan(conn: sqlite3.Connection, item_id: int) -> dict[str, Any] | None:
    return row(conn.execute("SELECT * FROM loans WHERE box_item_id = ? AND returned_at IS NULL", (item_id,)))


def set_lifecycle_status(conn: sqlite3.Connection, item_id: int, status: str, note: str = "") -> None:
    """Change an item's physical status. ``loaned`` is only set by ``open_loan``.

    If the item is currently loaned, its open loan is closed first (with a
    note), so status and loans never disagree. ``box_items.status`` (AI
    certainty) is never touched.
    """
    status = (status or "").strip()
    note = (note or "").strip()
    if status not in LIFECYCLE_STATUSES:
        raise LifecycleError(f"Unknown status '{status}'.")
    if status == "loaned":
        raise LifecycleError("Use Lend to record who has the item; that sets the status to Loaned.")
    item = get_box_item(conn, item_id)
    if not item:
        raise LifecycleError("Item not found.")
    current_loan = get_open_loan(conn, item_id)
    if current_loan:
        _close_loan(conn, current_loan, _today(), f"Closed when status changed to {LIFECYCLE_LABELS[status]}.")
    conn.execute(
        """UPDATE box_items SET lifecycle_status = ?, status_note = ?, status_changed_at = CURRENT_TIMESTAMP,
                  updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (status, note, item_id),
    )
    record_history(
        conn,
        "box_item",
        item_id,
        "lifecycle_changed",
        before={"lifecycle_status": item.get("lifecycle_status"), "status_note": item.get("status_note")},
        after={"lifecycle_status": status, "status_note": note},
    )


def open_loan(
    conn: sqlite3.Connection,
    item_id: int,
    borrower_name: str,
    borrower_contact: str = "",
    loaned_at: str | None = None,
    due_at: str | None = None,
    notes: str = "",
) -> int:
    item = get_box_item(conn, item_id)
    if not item:
        raise LifecycleError("Item not found.")
    borrower_name = (borrower_name or "").strip()
    if not borrower_name:
        raise LifecycleError("Borrower name is required.")
    if item.get("lifecycle_status") in GONE_STATUSES:
        raise LifecycleError(f"This item is marked {LIFECYCLE_LABELS[item['lifecycle_status']]}, so it can't be lent.")
    if get_open_loan(conn, item_id):
        raise LifecycleError("This item is already lent out. Mark it returned first.")
    loaned_at = (loaned_at or "").strip() or _today()
    due_at = (due_at or "").strip() or None
    cur = conn.execute(
        """INSERT INTO loans(box_item_id, borrower_name, borrower_contact, loaned_at, due_at, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, borrower_name, (borrower_contact or "").strip(), loaned_at, due_at, (notes or "").strip()),
    )
    loan_id = int(cur.lastrowid)
    conn.execute(
        """UPDATE box_items SET lifecycle_status = 'loaned', status_note = '', status_changed_at = CURRENT_TIMESTAMP,
                  updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (item_id,),
    )
    record_history(
        conn,
        "box_item",
        item_id,
        "loaned",
        before={"lifecycle_status": item.get("lifecycle_status")},
        after={"loan_id": loan_id, "borrower_name": borrower_name, "loaned_at": loaned_at, "due_at": due_at},
    )
    return loan_id


def _close_loan(conn: sqlite3.Connection, loan: dict[str, Any], returned_at: str, extra_note: str = "") -> None:
    notes = loan.get("notes") or ""
    if extra_note:
        notes = f"{notes}\n{extra_note}".strip()
    conn.execute("UPDATE loans SET returned_at = ?, notes = ? WHERE id = ?", (returned_at, notes, loan["id"]))
    record_history(conn, "loan", loan["id"], "returned", before={"returned_at": None}, after={"returned_at": returned_at})


def return_loan(conn: sqlite3.Connection, loan_id: int, returned_at: str | None = None) -> int:
    """Close a loan and put the item back ``in_home``. Returns the item id."""
    loan = row(conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)))
    if not loan:
        raise LifecycleError("Loan not found.")
    if loan.get("returned_at"):
        raise LifecycleError("This loan is already closed.")
    returned_at = (returned_at or "").strip() or _today()
    _close_loan(conn, loan, returned_at)
    conn.execute(
        """UPDATE box_items SET lifecycle_status = 'in_home', status_note = '', status_changed_at = CURRENT_TIMESTAMP,
                  updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (loan["box_item_id"],),
    )
    record_history(
        conn,
        "box_item",
        loan["box_item_id"],
        "returned",
        before={"lifecycle_status": "loaned"},
        after={"lifecycle_status": "in_home", "loan_id": loan_id},
    )
    return int(loan["box_item_id"])


def list_open_loans(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Open loans with item and container names, and an ``overdue`` flag."""
    today = _today()
    loans = rows(
        conn.execute(
            """SELECT ln.*, bi.item_name, bi.box_id, b.name AS box_name, b.public_id
               FROM loans ln
               JOIN box_items bi ON bi.id = ln.box_item_id
               JOIN boxes b ON b.id = bi.box_id
               WHERE ln.returned_at IS NULL
               ORDER BY ln.due_at IS NULL, ln.due_at, ln.loaned_at"""
        )
    )
    for loan in loans:
        loan["overdue"] = bool(loan.get("due_at")) and loan["due_at"] < today
    return loans


def list_loans_for_item(conn: sqlite3.Connection, item_id: int) -> list[dict[str, Any]]:
    return rows(conn.execute("SELECT * FROM loans WHERE box_item_id = ? ORDER BY loaned_at DESC, id DESC", (item_id,)))


def count_items_out_of_house(conn: sqlite3.Connection) -> int:
    placeholders = ", ".join("?" for _ in OUT_OF_HOUSE_STATUSES)
    found = row(
        conn.execute(f"SELECT COUNT(*) AS n FROM box_items WHERE lifecycle_status IN ({placeholders})", OUT_OF_HOUSE_STATUSES)
    )
    return int(found["n"]) if found else 0


def verify_container(conn: sqlite3.Connection, box_id: int, present_item_ids: list[int], mark_missing: bool = False) -> dict[str, int]:
    """Verify mode: ticked items (and the container) get today's date.

    Unticked items that are ``in_home`` can be marked ``missing``. Items that
    are elsewhere (loaned, gone and so on) are left alone. A ticked item that
    was ``missing`` goes back to ``in_home``.
    """
    today = _today()
    items = rows(conn.execute("SELECT id, lifecycle_status FROM box_items WHERE box_id = ?", (box_id,)))
    present = {int(value) for value in present_item_ids}
    verified = 0
    missing = 0
    for item in items:
        if item["id"] in present:
            conn.execute("UPDATE box_items SET last_verified_at = ? WHERE id = ?", (today, item["id"]))
            if item["lifecycle_status"] == "missing":
                set_lifecycle_status(conn, item["id"], "in_home", "Found during verification.")
            verified += 1
        elif mark_missing and item["lifecycle_status"] == "in_home":
            set_lifecycle_status(conn, item["id"], "missing", f"Not found when verifying on {today}.")
            missing += 1
    conn.execute("UPDATE boxes SET last_verified_at = ? WHERE id = ?", (today, box_id))
    record_history(conn, "container", box_id, "verified", after={"verified": verified, "marked_missing": missing, "date": today})
    return {"verified": verified, "marked_missing": missing}


def attach_lifecycle_info(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add display fields (label, gone flag, open loan) to item dicts."""
    for item in items:
        status = item.get("lifecycle_status") or "in_home"
        item["lifecycle_label"] = LIFECYCLE_LABELS.get(status, status)
        item["is_gone"] = status in GONE_STATUSES
        item["open_loan"] = get_open_loan(conn, item["id"]) if status == "loaned" else None
    return items


# ---------------------------------------------------------------------------
# QW-2: estimated value totals (latest estimate x quantity, confirmed items)
# ---------------------------------------------------------------------------

def descendant_box_ids(conn: sqlite3.Connection, box_id: int) -> list[int]:
    """The container and every container nested inside it, at any depth."""
    ids = [box_id]
    seen = {box_id}
    queue = [box_id]
    while queue:
        current = queue.pop()
        for child in conn.execute("SELECT id FROM boxes WHERE parent_box_id = ?", (current,)).fetchall():
            child_id = int(child["id"])
            if child_id not in seen:
                seen.add(child_id)
                ids.append(child_id)
                queue.append(child_id)
    return ids


def _value_totals(conn: sqlite3.Connection, where: str, params: tuple) -> dict[str, Any]:
    """Sum of latest per-unit estimate x current quantity for confirmed items.

    Items that have left the household (donated, sold, given away, discarded)
    are not counted. ``unestimated`` counts confirmed items with no estimate.
    """
    gone = ", ".join("?" for _ in GONE_STATUSES)
    found = row(
        conn.execute(
            f"""SELECT
                  COALESCE(SUM(CASE WHEN ce.estimated_cost_usd IS NOT NULL THEN ce.estimated_cost_usd * bi.quantity END), 0) AS total,
                  COALESCE(SUM(CASE WHEN ce.estimated_cost_usd IS NOT NULL THEN 1 ELSE 0 END), 0) AS estimated,
                  COALESCE(SUM(CASE WHEN ce.estimated_cost_usd IS NULL THEN 1 ELSE 0 END), 0) AS unestimated
                FROM box_items bi
                LEFT JOIN cost_estimates ce ON ce.id = (
                    SELECT id FROM cost_estimates WHERE box_item_id = bi.id ORDER BY created_at DESC, id DESC LIMIT 1
                )
                WHERE bi.status = 'confirmed' AND bi.lifecycle_status NOT IN ({gone}) AND {where}""",
            (*GONE_STATUSES, *params),
        )
    )
    if not found:
        return {"total": 0.0, "estimated": 0, "unestimated": 0}
    return {"total": round(float(found["total"]), 2), "estimated": int(found["estimated"]), "unestimated": int(found["unestimated"])}


def container_value_totals(conn: sqlite3.Connection, box_id: int) -> dict[str, Any]:
    """Totals for a container, including everything nested inside it."""
    ids = descendant_box_ids(conn, box_id)
    placeholders = ", ".join("?" for _ in ids)
    return _value_totals(conn, f"bi.box_id IN ({placeholders})", tuple(ids))


def household_value_totals(conn: sqlite3.Connection) -> dict[str, Any]:
    return _value_totals(conn, "1 = 1", ())
