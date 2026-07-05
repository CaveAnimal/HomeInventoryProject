import argparse
import sqlite3
from pathlib import Path

from .settings import APP_ROOT, DB_PATH, ensure_dirs


def connect(path: Path | None = None) -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(path: Path | None = None) -> None:
    conn = connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    for migration in sorted((APP_ROOT / "migrations").glob("*.sql")):
        version = migration.stem
        exists = conn.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (version,)).fetchone()
        if exists:
            continue
        conn.executescript(migration.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
    conn.commit()
    conn.close()


def seed(path: Path | None = None) -> None:
    from .repository import create_box, add_item_to_box

    conn = connect(path)
    if conn.execute("SELECT COUNT(*) AS n FROM boxes").fetchone()["n"]:
        conn.close()
        return
    box_id = create_box(
        conn,
        name="Basement-Box-014",
        room_name="basement storage room",
        north_ft=3.5,
        east_ft=8,
        elevation_ft=2,
        notes="Clear tote near the shelving unit.",
        tags="winter,seasonal,clothing",
        size="medium tote",
        stack_position="middle shelf",
    )
    add_item_to_box(conn, box_id, "winter gloves", quantity=2, status="confirmed", tags="winter,clothing")
    add_item_to_box(conn, box_id, "wool scarf", quantity=1, status="confirmed", tags="winter,clothing")
    add_item_to_box(conn, box_id, "snow brush", quantity=1, status="likely", tags="winter,car")
    second_id = create_box(
        conn,
        name="Garage-Box-003",
        room_name="garage",
        north_ft=12,
        east_ft=4,
        elevation_ft=0.5,
        notes="Heavy cardboard box below workbench.",
        tags="tools,cables",
        inaccessible=1,
        size="large cardboard",
        stack_position="floor, behind tool chest",
    )
    add_item_to_box(conn, second_id, "extension cord", quantity=3, status="confirmed", tags="tools,cables")
    add_item_to_box(conn, second_id, "camping stove", quantity=1, status="confirmed", tags="camping")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true")
    args = parser.parse_args()
    migrate()
    if args.seed:
        seed()
    print(f"Database ready at {DB_PATH}")
