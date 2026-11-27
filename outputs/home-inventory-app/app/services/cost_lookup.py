"""Cost-lookup providers for the opt-in "estimated replacement cost" feature.

PROVIDER ABSTRACTION (D-001)
============================
Structurally mirrors ``services/vision.py``: a result dataclass, a
``CostLookupProvider`` base class, a ``CostLookupError`` exception carrying a
user-safe message, and a ``get_cost_provider()`` factory keyed off an env var
with a safe, network-free fallback for any unset/unrecognized value.

PRIVACY CONTRACT (D-003)
=========================
The provider interface accepts exactly ONE item per call (``item_name`` +
``category`` only -- never notes, box/room location, or a list of items).
Callers that need to estimate several items must issue N separate calls;
batching identifying info into a single outbound request is not permitted.

KILL SWITCH (D-005)
====================
``COST_LOOKUP_PROVIDER`` (see ``settings.py``) defaults to ``"disabled"``.
``get_cost_provider()`` returns ``DisabledCostLookupProvider`` for
``"disabled"``, an unset value, or any value it does not recognize.
``DisabledCostLookupProvider.estimate()`` makes ZERO network calls and raises
``CostLookupError`` with a user-safe "feature disabled" message.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass

import requests

from .. import repository, settings
from .vision import bonsai_base_url, bonsai_vision_model

MAX_SOURCE_TITLE_LENGTH = 200
MAX_SNIPPET_LENGTH = 600


class CostLookupError(Exception):
    """Raised when a provider cannot produce a valid cost estimate.

    The message is safe to show directly to the user.
    """


@dataclass
class CostEstimate:
    estimated_cost_usd: float | None = None
    confidence: float = 0.5
    source_title: str = ""
    source_url: str = ""


def normalize_cost_estimate(raw: object) -> CostEstimate | None:
    """Normalize one raw extraction dict into the strict cost-estimate contract.

    Returns ``None`` when the entry is unusable: not a dict, missing a
    usable price, or missing a source citation (an estimate with no
    supporting source URL/title is a hallucination risk per GOAL.md and must
    not be persisted). Never raises for bad field values; it defaults/clamps
    them instead.
    """
    if not isinstance(raw, dict):
        return None
    cost = _coerce_cost(raw.get("estimated_cost_usd"))
    source_url = str(raw.get("source_url") or "").strip()
    source_title = str(raw.get("source_title") or "").strip()[:MAX_SOURCE_TITLE_LENGTH]
    if cost is None or not source_url:
        return None
    return CostEstimate(
        estimated_cost_usd=cost,
        confidence=_coerce_confidence(raw.get("confidence")),
        source_title=source_title,
        source_url=source_url,
    )


def _coerce_cost(value: object) -> float | None:
    try:
        cost = float(value)
    except (TypeError, ValueError):
        return None
    if cost != cost or cost < 0:  # NaN guard + reject negative prices
        return None
    return cost


def _coerce_confidence(value: object) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5
    if confidence != confidence:  # NaN guard
        return 0.5
    # Some models emit percentages (e.g. 85 instead of 0.85).
    if 1.0 < confidence <= 100.0:
        confidence = confidence / 100.0
    return min(1.0, max(0.0, confidence))


# PRIVACY GUARDRAILS (T8, T9)
# ============================
# Both checks below MUST run before any network call. They raise
# ``CostLookupError`` (never return a sentinel that a caller could ignore),
# so the safe path is also the only path.

# Verified against app/categories.py:HOUSEHOLD_CATEGORIES. Excluded by
# default because they are the most likely to leak privacy-sensitive
# household detail (personal documents, sentimental items) via the search
# query built from item_name + category.
EXCLUDED_CATEGORIES = {"Documents & Paper", "Sentimental / Keepsakes"}


def ensure_lookup_allowed(item_name: str, category: str, opt_out: bool = False) -> None:
    """Raise before any network call if this item must not be looked up.

    Enforces (a) the default category exclusion list and (b) a caller-
    supplied per-item opt-out flag. ``box_items`` has no cost-lookup
    opt-out column of its own (see migrations/001_initial.sql,
    migrations/003_item_category_standards.sql) and DECISIONS.md forbids
    adding one, so the opt-out flag is owned and persisted by the caller
    (the API/endpoint layer) and passed in here rather than read from the
    database.
    """
    if opt_out:
        raise CostLookupError(
            f'Estimated replacement cost is not available for "{item_name}": '
            "lookup has been turned off for this item."
        )
    if category in EXCLUDED_CATEGORIES:
        raise CostLookupError(
            f'Estimated replacement cost is not available for the "{category}" category. '
            "This category is excluded by default to protect privacy-sensitive items."
        )


def monthly_limit() -> int:
    """Read COST_LOOKUP_MONTHLY_LIMIT when needed, not once at import."""
    try:
        return int(os.environ.get("COST_LOOKUP_MONTHLY_LIMIT", str(settings.COST_LOOKUP_MONTHLY_LIMIT)).strip())
    except ValueError:
        return settings.COST_LOOKUP_MONTHLY_LIMIT


def ensure_budget_available(conn: sqlite3.Connection) -> None:
    """Raise before any network call once the monthly lookup cap is hit.

    Counts every outbound **attempt** this UTC month, successful or not
    (QW-5), from ``cost_lookup_attempts``. A failed lookup still uses a
    search credit, so it counts. The count resets at each month boundary.
    """
    limit = monthly_limit()
    count = repository.count_cost_lookup_attempts_this_month(conn)
    if count >= limit:
        raise CostLookupError(
            f"Monthly cost-lookup limit reached ({limit} lookups "
            "this month). Try again next month, or ask an administrator to raise "
            "COST_LOOKUP_MONTHLY_LIMIT."
        )


class CostLookupProvider:
    def makes_network_call(self) -> bool:
        """True when estimate() will contact an outside service (counted by QW-5)."""
        return False

    def estimate(self, item_name: str, category: str) -> CostEstimate:
        """Look up a current market replacement cost for a single item.

        ``item_name`` and ``category`` are the ONLY identifying information
        that may leave the device (no photos, box/room location, or notes).
        This method accepts exactly one item; callers needing several
        estimates must call it once per item.
        """
        raise NotImplementedError


class DisabledCostLookupProvider(CostLookupProvider):
    """No-op provider used when the feature is off or misconfigured.

    Makes zero network calls under any circumstance -- this is the
    kill-switch safety net (D-005), so it must never be changed to reach
    out to a network resource.
    """

    def estimate(self, item_name: str, category: str) -> CostEstimate:
        raise CostLookupError(
            "Estimated replacement cost is not available: this feature is disabled. "
            "An administrator can enable it by setting COST_LOOKUP_PROVIDER."
        )


def _extract_json_object(text: str) -> dict:
    """Extract the first JSON object from local-model output.

    Mirrors ``services/vision.py:extract_json_payload`` (markdown fences,
    leading prose, trailing commentary are all tolerated) but is
    duplicated locally rather than imported, so this module has no runtime
    dependency on the vision module. Raises ``ValueError`` when no JSON
    object is found.
    """
    if not text or not text.strip():
        raise ValueError("empty response")
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            payload, _ = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise ValueError("no JSON object found in response")


class TavilyCostLookupProvider(CostLookupProvider):
    """Search-provider client for Tavily (D-007), with local-LLM extraction (D-002, T6).

    Flow per ``estimate()`` call:
      1. Re-check the category exclusion list (defense in depth; the
         primary enforcement point is ``ensure_lookup_allowed()``, called
         by callers before a provider is even resolved).
      2. POST to Tavily's search API with a query built ONLY from
         ``item_name`` + ``category`` (never notes/box/room/photos).
      3. Hand the raw title/url/content results to the local LLM
         (Bonsai by default, Ollama with COST_LOOKUP_LLM=ollama), instructed to extract a structured
         estimate and to cite only a URL present in the search results.
      4. Normalize the extraction output and verify the cited URL is
         actually one of the URLs Tavily returned -- an estimate that
         fails either check is a hallucination risk and is rejected
         (raises ``CostLookupError``), never returned.
    """

    SEARCH_URL = "https://api.tavily.com/search"

    def __init__(self) -> None:
        self.api_key = os.environ.get("COST_LOOKUP_API_KEY") or os.environ.get("TAVILY_API_KEY")
        # Extraction runs on the same local Bonsai server as vision
        # (BONSAI_URL, see services/vision.py). COST_LOOKUP_LLM=ollama keeps
        # the older Ollama text-model path available.
        self.llm = os.environ.get("COST_LOOKUP_LLM", "bonsai").lower()
        self.bonsai_url = f"{bonsai_base_url()}/v1/chat/completions"
        self.bonsai_model = bonsai_vision_model()
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = os.environ.get("COST_LOOKUP_OLLAMA_MODEL", "llama3.2")

    def makes_network_call(self) -> bool:
        return bool(self.api_key)

    def estimate(self, item_name: str, category: str) -> CostEstimate:
        # Defense in depth: even if a caller skips ensure_lookup_allowed(),
        # an excluded category can never reach the network path here.
        ensure_lookup_allowed(item_name, category)
        if not self.api_key:
            raise CostLookupError(
                "Estimated replacement cost is not available: no COST_LOOKUP_API_KEY "
                "(or TAVILY_API_KEY) is configured."
            )
        results = self._search(item_name, category)
        return self._extract(item_name, category, results)

    def _search(self, item_name: str, category: str) -> list[dict]:
        query = f"{item_name} {category} replacement price"
        try:
            response = requests.post(
                self.SEARCH_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"query": query, "search_depth": "basic", "max_results": 5},
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise CostLookupError(
                "Could not reach the search service. Check your network connection and try again."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise CostLookupError(
                "The search service took too long to respond. Try again in a moment."
            ) from exc
        except requests.exceptions.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (401, 403):
                raise CostLookupError(
                    "The search service rejected the request (invalid or missing API key)."
                ) from exc
            detail = getattr(getattr(exc, "response", None), "text", "") or str(exc)
            raise CostLookupError(f"The search service returned an error: {detail[:300]}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise CostLookupError("The search service returned an unreadable response. Try again.") from exc
        results = body.get("results") if isinstance(body, dict) else None
        if not isinstance(results, list) or not results:
            raise CostLookupError(f'No search results were found for "{item_name}".')
        return results

    def _clean_results(self, results: list[dict]) -> list[dict]:
        cleaned = []
        for entry in results:
            if not isinstance(entry, dict):
                continue
            url = str(entry.get("url") or "").strip()
            if not url:
                continue
            cleaned.append(
                {
                    "title": str(entry.get("title") or "").strip()[:MAX_SOURCE_TITLE_LENGTH],
                    "url": url,
                    "content": str(entry.get("content") or "").strip()[:MAX_SNIPPET_LENGTH],
                }
            )
        return cleaned

    def _build_prompt(self, item_name: str, category: str, results: list[dict]) -> str:
        results_block = "\n".join(
            f'- title: "{r["title"]}"\n  url: {r["url"]}\n  snippet: "{r["content"]}"' for r in results
        )
        return (
            "You are extracting ONE current replacement-cost estimate for a home "
            f'inventory item named "{item_name}" (category: "{category}") using ONLY the '
            "web search results listed below. Do not use outside knowledge and do not "
            "invent a price that is not supported by a result. "
            "source_url MUST be copied exactly from one of the URLs listed below -- never "
            "a URL that does not appear in the results below. "
            "If none of the results give a usable price for this item, set "
            "estimated_cost_usd to null and source_url to an empty string. "
            "confidence is a number between 0 and 1 reflecting how directly the cited "
            "result supports the price. "
            "Respond with ONLY this JSON, no prose, no markdown: "
            '{"estimated_cost_usd": 0.0, "confidence": 0.0, "source_title": "...", "source_url": "..."}\n\n'
            f"Search results:\n{results_block}"
        )

    def _extract(self, item_name: str, category: str, raw_results: list[dict]) -> CostEstimate:
        cleaned = self._clean_results(raw_results)
        if not cleaned:
            raise CostLookupError(f'No search results with a usable source were found for "{item_name}".')
        known_urls = {entry["url"] for entry in cleaned}
        prompt = self._build_prompt(item_name, category, cleaned)
        if self.llm == "ollama":
            text = self._complete_ollama(prompt)
        else:
            text = self._complete_bonsai(prompt)
        try:
            payload = _extract_json_object(text)
        except ValueError as exc:
            raise CostLookupError(
                "The local extraction model returned output that could not be read as JSON. Try again."
            ) from exc
        estimate = normalize_cost_estimate(payload)
        if estimate is None:
            # No price and/or no source URL -- the hallucination guard from
            # GOAL.md's risk table. A source-less estimate is never returned.
            raise CostLookupError(
                f'No confident, source-backed cost estimate could be produced for "{item_name}".'
            )
        if estimate.source_url not in known_urls:
            # The model cited a URL we never showed it -- reject rather than
            # trust an unverifiable citation.
            raise CostLookupError(
                "The extraction model cited a source that was not part of the search "
                "results; rejecting the estimate to avoid an unverifiable price."
            )
        return estimate

    def _complete_bonsai(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.bonsai_url,
                json={
                    "model": self.bonsai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "temperature": 0,
                    "top_p": 0.1,
                    "max_tokens": 400,
                    "response_format": {"type": "json_object"},
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise CostLookupError(
                f"Could not reach the local Bonsai server at {bonsai_base_url()}. "
                "Make sure Bonsai's llama-server is running, then try again."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise CostLookupError(
                "The local extraction model took too long to respond. Try again."
            ) from exc
        except requests.exceptions.RequestException as exc:
            detail = getattr(getattr(exc, "response", None), "text", "") or str(exc)
            raise CostLookupError(f"The local extraction service returned an error: {detail[:300]}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise CostLookupError(
                "The local extraction service returned an unreadable response. Try again."
            ) from exc
        choices = body.get("choices") if isinstance(body, dict) else None
        if not choices:
            return ""
        return (choices[0].get("message") or {}).get("content") or ""

    def _complete_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "think": False,
                    "options": {"temperature": 0, "top_p": 0.1, "num_predict": 400},
                },
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise CostLookupError(
                "Could not reach the local Ollama service. Make sure Ollama is running "
                "on the desktop host, then try again."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise CostLookupError(
                "The local extraction model took too long to respond. Try again."
            ) from exc
        except requests.exceptions.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 404:
                raise CostLookupError(
                    f"The Ollama model '{self.ollama_model}' was not found. "
                    f"Run: ollama pull {self.ollama_model}"
                ) from exc
            detail = getattr(getattr(exc, "response", None), "text", "") or str(exc)
            raise CostLookupError(f"The local extraction service returned an error: {detail[:300]}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise CostLookupError(
                "The local extraction service returned an unreadable response. Try again."
            ) from exc
        return body.get("response", "") if isinstance(body, dict) else ""


def get_cost_provider() -> CostLookupProvider:
    provider = os.environ.get("COST_LOOKUP_PROVIDER", "disabled").lower()
    if provider == "disabled":
        return DisabledCostLookupProvider()
    if provider == "tavily":
        return TavilyCostLookupProvider()
    return DisabledCostLookupProvider()


def estimate_replacement_cost(
    conn: sqlite3.Connection, item_name: str, category: str, opt_out: bool = False
) -> CostEstimate:
    """Single wired-together entry point for the API layer (T10) to call.

    Runs the category/opt-out guard (T8) and the monthly budget guard (T9)
    BEFORE resolving a provider or making any network call, so it is
    impossible to reach the network path for an excluded/opted-out item or
    once the monthly cap is reached. Callers should use this function
    rather than calling ``get_cost_provider().estimate(...)`` directly.
    """
    ensure_lookup_allowed(item_name, category, opt_out)
    ensure_budget_available(conn)
    provider = get_cost_provider()
    if provider.makes_network_call():
        # Count the attempt before the call and commit it at once, so a
        # failed lookup (which the API turns into an error response and a
        # rolled-back request) still counts toward the monthly limit (QW-5).
        repository.record_cost_lookup_attempt(conn)
        conn.commit()
    return provider.estimate(item_name, category)
