import difflib
import re
import sqlite3

from ..repository import container_path, normalize, rows

SYNONYMS = {
    "cord": ["cable", "extension cord", "charger"],
    "cable": ["cord", "wire", "adapter"],
    "gloves": ["mittens", "winter gloves"],
    "xmas": ["christmas", "holiday"],
    "papers": ["documents", "files"],
}


def expand_query(query: str) -> list[str]:
    base = normalize(query)
    terms = {base, query.lower().strip()}
    for word in re.findall(r"[a-z0-9]+", base):
        terms.update(SYNONYMS.get(word, []))
    return [term for term in terms if term]


def search_items(conn: sqlite3.Connection, query: str = "", room: str = "", tag: str = "", category: str = "", min_confidence: float = 0) -> list[dict]:
    terms = expand_query(query) if query else [""]
    clauses = ["bi.confidence >= ?"]
    params: list = [min_confidence]
    if room:
        clauses.append("l.room_name LIKE ?")
        params.append(f"%{room}%")
    if tag:
        clauses.append("(bi.tags LIKE ? OR b.tags LIKE ?)")
        params.extend([f"%{tag}%", f"%{tag}%"])
    if category:
        clauses.append("bi.category LIKE ?")
        params.append(f"%{category}%")
    if query:
        clauses.append("(" + " OR ".join(["bi.normalized_name LIKE ? OR bi.item_name LIKE ?" for _ in terms]) + ")")
        for term in terms:
            params.extend([f"%{normalize(term)}%", f"%{term}%"])
    sql = f"""
        SELECT bi.*, b.name AS box_name, b.name AS container_name, b.public_id, b.tags AS box_tags,
               b.container_type, b.inaccessible,
               l.room_name, l.north_ft, l.east_ft, l.elevation_ft
        FROM box_items bi
        JOIN boxes b ON b.id = bi.box_id
        JOIN box_locations l ON l.box_id = b.id
        WHERE {' AND '.join(clauses)}
        ORDER BY bi.priority DESC, bi.status = 'confirmed' DESC, bi.confidence DESC, bi.item_name
    """
    results = rows(conn.execute(sql, params))
    for result in results:
        result["container_path"] = container_path(conn, result["box_id"])
    return results


def similar_items(conn: sqlite3.Connection, name: str, limit: int = 6) -> list[dict]:
    all_items = rows(
        conn.execute(
            """SELECT bi.item_name, bi.box_id, b.name AS box_name, b.name AS container_name, b.public_id, b.container_type, l.room_name
               FROM box_items bi JOIN boxes b ON b.id = bi.box_id JOIN box_locations l ON l.box_id = b.id"""
        )
    )
    names = [item["item_name"] for item in all_items]
    close = set(difflib.get_close_matches(name, names, n=limit, cutoff=0.55))
    matches = [item for item in all_items if item["item_name"] in close and item["item_name"] != name][:limit]
    for item in matches:
        item["container_path"] = container_path(conn, item["box_id"])
    return matches
