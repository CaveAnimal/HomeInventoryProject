"""Regression tests for the cost_of_replacement feature (T14).

Covers the T14 acceptance criteria:
1. Disabled provider makes ZERO network calls.
2. Unrecognized COST_LOOKUP_PROVIDER value also resolves to the disabled provider.
3. normalize_cost_estimate(): malformed input, missing price/source -> None;
   percentage confidence scaling/clamping.
4. Extraction rejection: no source URL, or a URL not present in the search
   results -> CostLookupError, nothing persisted.
5. Category exclusion blocks BEFORE any network call.
6. Per-item opt-out (``no-cost-lookup`` tag) refused via endpoint + service.
7. Monthly budget cap refusal, and monthly reset (prior-month rows don't count).
8. Batch fan-out: exactly N single-item provider calls for a mixed box.
9. Insert-only history: two estimates -> two rows, latest() returns the newer.

No real network calls are made anywhere in this file; ``requests.post`` is
always mocked or guarded to fail the test if invoked unexpectedly.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["HOME_INVENTORY_DATA"] = str(ROOT / "test-data")
os.environ["HOME_INVENTORY_DB"] = str(ROOT / "test-data" / "test.sqlite3")
os.environ["VISION_PROVIDER"] = "heuristic"
os.environ.setdefault("COST_LOOKUP_PROVIDER", "disabled")

import pytest
from fastapi.testclient import TestClient

from app import settings
from app.database import connect, migrate
from app.main import app
from app.repository import (
    add_cost_estimate,
    add_item_to_box,
    create_box,
    latest_cost_estimate,
    list_cost_estimates_for_item,
)
from app.services import cost_lookup
from app.services.cost_lookup import (
    CostLookupError,
    DisabledCostLookupProvider,
    EXCLUDED_CATEGORIES,
    TavilyCostLookupProvider,
    ensure_budget_available,
    estimate_replacement_cost,
    get_cost_provider,
    normalize_cost_estimate,
)


def reset_db():
    db_path = Path(os.environ["HOME_INVENTORY_DB"])
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            # Windows: another test module (or the app under test) still holds
            # the sqlite file open, so it cannot be deleted. Fall back to
            # wiping the data instead: every table cascades from ``boxes``
            # (ON DELETE CASCADE), and edit_history is standalone.
            pass
    migrate(db_path)
    conn = connect(db_path)
    conn.execute("DELETE FROM boxes")
    conn.execute("DELETE FROM edit_history")
    conn.commit()
    conn.close()


def db_conn():
    return connect(Path(os.environ["HOME_INVENTORY_DB"]))


def make_item(conn, item_name="Toaster", category="Cables & Electronics", tags="", box_name="Test-Box"):
    box_id = create_box(conn, box_name, "office", 1, 1, 1)
    item_id = add_item_to_box(conn, box_id, item_name, category=category, tags=tags, status="confirmed")
    return box_id, item_id


def fail_if_called(*args, **kwargs):
    raise AssertionError(f"requests.post must NOT be called; got args={args} kwargs={kwargs}")


# ---------------------------------------------------------------------------
# 1. Disabled provider -> zero network calls
# ---------------------------------------------------------------------------

def test_disabled_provider_raises_and_makes_zero_network_calls(monkeypatch):
    reset_db()
    monkeypatch.delenv("COST_LOOKUP_PROVIDER", raising=False)
    monkeypatch.setattr(cost_lookup.requests, "post", fail_if_called)

    conn = db_conn()
    box_id, item_id = make_item(conn)
    conn.commit()

    with pytest.raises(CostLookupError, match="disabled"):
        estimate_replacement_cost(conn, "Toaster", "Cables & Electronics")
    conn.close()

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 422
    assert "disabled" in response.json()["detail"].lower()

    # Explicit "disabled" behaves the same as unset.
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "disabled")
    response2 = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response2.status_code == 422
    assert "disabled" in response2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 2. Unrecognized provider value -> disabled
# ---------------------------------------------------------------------------

def test_unrecognized_provider_value_resolves_to_disabled(monkeypatch):
    for value in ["openai", "brave", "serpapi", "TAVILY_TYPO", "  ", ""]:
        monkeypatch.setenv("COST_LOOKUP_PROVIDER", value)
        assert isinstance(get_cost_provider(), DisabledCostLookupProvider), value


def test_recognized_provider_value_resolves_to_tavily(monkeypatch):
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    assert isinstance(get_cost_provider(), TavilyCostLookupProvider)
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "TAVILY")  # case-insensitive
    assert isinstance(get_cost_provider(), TavilyCostLookupProvider)


# ---------------------------------------------------------------------------
# 3. normalize_cost_estimate()
# ---------------------------------------------------------------------------

def test_normalize_cost_estimate_rejects_malformed_or_missing_fields():
    assert normalize_cost_estimate("not a dict") is None
    assert normalize_cost_estimate(None) is None
    assert normalize_cost_estimate([1, 2, 3]) is None
    # missing price
    assert normalize_cost_estimate({"confidence": 0.9, "source_url": "https://x.example"}) is None
    # missing source_url
    assert normalize_cost_estimate({"estimated_cost_usd": 19.99, "confidence": 0.9}) is None
    assert normalize_cost_estimate({"estimated_cost_usd": 19.99, "source_url": ""}) is None
    # unusable price
    assert normalize_cost_estimate({"estimated_cost_usd": "not-a-number", "source_url": "https://x.example"}) is None
    assert normalize_cost_estimate({"estimated_cost_usd": None, "source_url": "https://x.example"}) is None
    # negative price rejected
    assert normalize_cost_estimate({"estimated_cost_usd": -5, "source_url": "https://x.example"}) is None
    # NaN price rejected
    assert normalize_cost_estimate({"estimated_cost_usd": float("nan"), "source_url": "https://x.example"}) is None


def test_normalize_cost_estimate_accepts_valid_and_truncates_title():
    est = normalize_cost_estimate(
        {
            "estimated_cost_usd": "49.99",
            "confidence": 0.72,
            "source_title": "x" * 500,
            "source_url": "https://example.com/widget",
        }
    )
    assert est is not None
    assert est.estimated_cost_usd == 49.99
    assert est.confidence == 0.72
    assert len(est.source_title) == cost_lookup.MAX_SOURCE_TITLE_LENGTH
    assert est.source_url == "https://example.com/widget"


def test_normalize_cost_estimate_percentage_confidence_scaled_and_clamped():
    # Percentage-style confidence (e.g. 85) is scaled to 0.85.
    est = normalize_cost_estimate({"estimated_cost_usd": 20, "confidence": 85, "source_url": "https://x.example"})
    assert est.confidence == 0.85

    # Out-of-range values are clamped rather than rejected.
    est_high = normalize_cost_estimate({"estimated_cost_usd": 20, "confidence": 500, "source_url": "https://x.example"})
    assert est_high.confidence == 1.0

    est_low = normalize_cost_estimate({"estimated_cost_usd": 20, "confidence": -3, "source_url": "https://x.example"})
    assert est_low.confidence == 0.0

    # Unparseable confidence defaults to 0.5 rather than raising.
    est_default = normalize_cost_estimate({"estimated_cost_usd": 20, "confidence": "very high", "source_url": "https://x.example"})
    assert est_default.confidence == 0.5


# ---------------------------------------------------------------------------
# 4. Extraction rejection: missing / unverifiable source URL
# ---------------------------------------------------------------------------

TAVILY_RESULTS_BODY = {
    "results": [
        {"title": "Example Store", "url": "https://example.com/widget", "content": "Widget costs $49.99 new."}
    ]
}


def _make_fake_post(ollama_response_text: str):
    def fake_post(url, *args, **kwargs):
        response = MagicMock()
        response.raise_for_status = lambda: None
        if url == TavilyCostLookupProvider.SEARCH_URL:
            response.json = lambda: TAVILY_RESULTS_BODY
        else:
            response.json = lambda: {
                "response": ollama_response_text,
                "choices": [{"message": {"content": ollama_response_text}}],
            }
        return response

    return fake_post


def test_extraction_rejected_when_no_source_url(monkeypatch):
    reset_db()
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")

    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Widget")
    conn.commit()
    conn.close()

    ollama_text = json.dumps(
        {"estimated_cost_usd": 49.99, "confidence": 0.8, "source_title": "Example Store", "source_url": ""}
    )
    monkeypatch.setattr(cost_lookup.requests, "post", _make_fake_post(ollama_text))

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 422

    conn = db_conn()
    assert list_cost_estimates_for_item(conn, item_id) == []
    conn.close()


def test_extraction_rejected_when_cited_url_not_in_results(monkeypatch):
    reset_db()
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")

    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Widget")
    conn.commit()
    conn.close()

    # Model cites a URL that was never part of the search results.
    ollama_text = json.dumps(
        {
            "estimated_cost_usd": 49.99,
            "confidence": 0.8,
            "source_title": "Made Up",
            "source_url": "https://not-in-results.example.com",
        }
    )
    monkeypatch.setattr(cost_lookup.requests, "post", _make_fake_post(ollama_text))

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 422
    assert "cited a source" in response.json()["detail"]

    conn = db_conn()
    assert list_cost_estimates_for_item(conn, item_id) == []
    conn.close()


def test_extraction_succeeds_when_cited_url_is_in_results(monkeypatch):
    reset_db()
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")

    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Widget")
    conn.commit()
    conn.close()

    ollama_text = json.dumps(
        {
            "estimated_cost_usd": 49.99,
            "confidence": 85,
            "source_title": "Example Store",
            "source_url": "https://example.com/widget",
        }
    )
    monkeypatch.setattr(cost_lookup.requests, "post", _make_fake_post(ollama_text))

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_cost_usd"] == 49.99
    assert body["confidence"] == 0.85
    assert body["source_url"] == "https://example.com/widget"

    conn = db_conn()
    assert len(list_cost_estimates_for_item(conn, item_id)) == 1
    conn.close()


# ---------------------------------------------------------------------------
# 5. Category exclusion blocks BEFORE any network call
# ---------------------------------------------------------------------------

def test_excluded_categories_constant_matches_goal():
    assert EXCLUDED_CATEGORIES == {"Documents & Paper", "Sentimental / Keepsakes"}


def test_category_exclusion_blocks_before_network_call(monkeypatch):
    reset_db()
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")
    monkeypatch.setattr(cost_lookup.requests, "post", fail_if_called)

    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Birth Certificate", category="Documents & Paper")
    conn.commit()

    with pytest.raises(CostLookupError, match="Documents & Paper"):
        estimate_replacement_cost(conn, "Birth Certificate", "Documents & Paper")
    conn.close()

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 422
    assert "Documents & Paper" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 6. Per-item opt-out (``no-cost-lookup`` tag)
# ---------------------------------------------------------------------------

def test_per_item_opt_out_tag_refused_via_endpoint_and_service(monkeypatch):
    reset_db()
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")
    monkeypatch.setattr(cost_lookup.requests, "post", fail_if_called)

    conn = db_conn()
    box_id, item_id = make_item(
        conn, item_name="Family Photo Album", category="Cables & Electronics", tags="fragile, no-cost-lookup"
    )
    conn.commit()

    with pytest.raises(CostLookupError, match="turned off"):
        estimate_replacement_cost(conn, "Family Photo Album", "Cables & Electronics", opt_out=True)
    conn.close()

    client = TestClient(app)
    response = client.post(f"/api/items/{item_id}/cost-estimate")
    assert response.status_code == 422
    assert "turned off" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 7. Monthly budget cap + reset
# ---------------------------------------------------------------------------

def test_budget_cap_reached_refuses_lookup_without_network_call(monkeypatch):
    reset_db()
    monkeypatch.setattr(settings, "COST_LOOKUP_MONTHLY_LIMIT", 2)
    monkeypatch.setenv("COST_LOOKUP_PROVIDER", "tavily")
    monkeypatch.setenv("COST_LOOKUP_API_KEY", "test-key")

    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Widget")
    add_cost_estimate(conn, item_id, 10.0, 0.9, "t1", "https://example.com/1")
    add_cost_estimate(conn, item_id, 12.0, 0.9, "t2", "https://example.com/2")
    conn.commit()

    monkeypatch.setattr(cost_lookup.requests, "post", fail_if_called)

    with pytest.raises(CostLookupError, match="Monthly cost-lookup limit reached"):
        estimate_replacement_cost(conn, "Widget", "Cables & Electronics")
    conn.close()


def test_budget_cap_monthly_reset_prior_month_rows_not_counted():
    reset_db()
    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Gadget")
    conn.commit()

    now = datetime.now(timezone.utc)
    prior_month_dt = (now.replace(day=1) - timedelta(days=1)).replace(day=15)
    prior_month_str = prior_month_dt.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT INTO cost_estimates(box_item_id, estimated_cost_usd, confidence, source_title, source_url, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, 10.0, 0.9, "Old", "https://example.com/old", prior_month_str),
    )
    conn.commit()

    from app.repository import count_cost_estimates_this_month

    assert count_cost_estimates_this_month(conn) == 0
    # Should not raise: current-month count is 0, well under the default limit.
    ensure_budget_available(conn)
    conn.close()


# ---------------------------------------------------------------------------
# 8. Batch fan-out: exactly N single-item calls, correct buckets
# ---------------------------------------------------------------------------

def test_batch_fanout_exactly_one_call_per_eligible_item_and_correct_buckets(monkeypatch):
    reset_db()
    conn = db_conn()
    box_id = create_box(conn, "Batch-Box", "office", 1, 1, 1)
    eligible_names = ["Lamp", "Chair", "Toaster"]
    for name in eligible_names:
        add_item_to_box(conn, box_id, name, category="Cables & Electronics", status="confirmed")
    add_item_to_box(conn, box_id, "Old Deed", category="Documents & Paper", status="confirmed")
    add_item_to_box(conn, box_id, "Grandma's Ring", category="Home Decor", tags="no-cost-lookup", status="confirmed")
    conn.commit()
    conn.close()

    calls = []

    def fake_estimate(conn, item_name, category, opt_out=False):
        calls.append((item_name, category))
        return cost_lookup.CostEstimate(
            estimated_cost_usd=25.0, confidence=0.9, source_title="Src", source_url="https://example.com/x"
        )

    import app.main as main_module

    monkeypatch.setattr(main_module, "estimate_replacement_cost", fake_estimate)

    client = TestClient(app)
    response = client.post(f"/api/boxes/{box_id}/cost-estimates")
    assert response.status_code == 200
    body = response.json()

    # Exactly N calls, one per eligible item, each carrying exactly one item's info.
    assert len(calls) == len(eligible_names)
    assert {name for name, _category in calls} == set(eligible_names)
    for name, category in calls:
        assert category == "Cables & Electronics"

    assert {entry["item_name"] for entry in body["estimated"]} == set(eligible_names)
    assert len(body["skipped"]) == 2
    skipped_reasons = {entry["item_name"]: entry["reason"] for entry in body["skipped"]}
    assert "excluded by default" in skipped_reasons["Old Deed"]
    assert "no-cost-lookup" in skipped_reasons["Grandma's Ring"]
    assert body["failed"] == []


def test_batch_fanout_stops_calling_provider_once_budget_exhausted_mid_batch(monkeypatch):
    reset_db()
    monkeypatch.setattr(settings, "COST_LOOKUP_MONTHLY_LIMIT", 2)

    conn = db_conn()
    box_id = create_box(conn, "Budget-Batch-Box", "office", 1, 1, 1)
    for name in ["Item A", "Item B", "Item C", "Item D"]:
        add_item_to_box(conn, box_id, name, category="Cables & Electronics", status="confirmed")
    conn.commit()
    conn.close()

    calls = []

    def fake_estimate(conn, item_name, category, opt_out=False):
        calls.append(item_name)
        return cost_lookup.CostEstimate(
            estimated_cost_usd=25.0, confidence=0.9, source_title="Src", source_url="https://example.com/x"
        )

    import app.main as main_module

    monkeypatch.setattr(main_module, "estimate_replacement_cost", fake_estimate)

    client = TestClient(app)
    response = client.post(f"/api/boxes/{box_id}/cost-estimates")
    assert response.status_code == 200
    body = response.json()

    # Budget allows exactly 2 lookups; the rest must be skipped, not attempted.
    assert len(calls) == 2
    assert len(body["estimated"]) == 2
    assert len(body["skipped"]) == 2
    assert all("budget" in entry["reason"] for entry in body["skipped"])


# ---------------------------------------------------------------------------
# 9. Insert-only history
# ---------------------------------------------------------------------------

def test_insert_only_history_two_estimates_yield_two_rows_latest_is_newer():
    reset_db()
    conn = db_conn()
    box_id, item_id = make_item(conn, item_name="Blender")
    conn.commit()

    add_cost_estimate(conn, item_id, 30.0, 0.7, "First Source", "https://example.com/first")
    conn.commit()
    add_cost_estimate(conn, item_id, 35.0, 0.8, "Second Source", "https://example.com/second")
    conn.commit()

    history = list_cost_estimates_for_item(conn, item_id)
    assert len(history) == 2

    latest = latest_cost_estimate(conn, item_id)
    assert latest["source_url"] == "https://example.com/second"
    assert latest["estimated_cost_usd"] == 35.0
    conn.close()
