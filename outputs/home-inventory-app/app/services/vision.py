"""Vision providers and the strict detection contract.

STRICT DETECTION SCHEMA CONTRACT (T2 / D-003)
=============================================
Every provider must return ``list[DetectedItem]`` where each item satisfies:

    name        non-empty str, whitespace-trimmed, max 120 chars (required;
                items without a usable name are dropped)
    quantity    int >= 1 (defaults to 1; floats truncated; invalid -> 1)
    confidence  float clamped to [0.0, 1.0] (defaults to 0.5; invalid -> 0.5)
    category    one of ``HOUSEHOLD_CATEGORIES`` (case-insensitive match is
                normalized to canonical casing; anything else becomes
                "Unknown / Needs Review")
    notes       str, max 500 chars (defaults to "")

``normalize_detection`` is the single source of truth for these
validation/defaulting rules and is unit-tested for valid, partial, and
malformed inputs.

ERROR HANDLING CONTRACT (T3)
============================
Providers raise ``VisionError`` with a user-safe message when detection cannot
proceed (runtime unreachable, model missing, malformed/non-JSON output in
strict mode).  Callers surface the message without corrupting stored data:
photos are still saved, only suggestions are skipped.
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import requests

from ..categories import HOUSEHOLD_CATEGORIES
from ..settings import VISION_PROVIDER

FALLBACK_CATEGORY = "Unknown / Needs Review"
MAX_NAME_LENGTH = 120
MAX_NOTES_LENGTH = 500
_CANONICAL_CATEGORIES = {category.lower(): category for category in HOUSEHOLD_CATEGORIES}


class VisionError(Exception):
    """Raised when a provider cannot produce a valid detection list.

    The message is safe to show directly to the user.
    """


@dataclass
class DetectedItem:
    name: str
    quantity: int = 1
    confidence: float = 0.5
    category: str = ""
    notes: str = ""


def normalize_detection(raw: object) -> DetectedItem | None:
    """Normalize one raw detection dict into the strict contract.

    Returns ``None`` when the entry is unusable (not a dict, or no name).
    Never raises for bad field values; it defaults/clamps them instead.
    """
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or "").strip()[:MAX_NAME_LENGTH]
    if not name:
        return None
    return DetectedItem(
        name=name,
        quantity=_coerce_quantity(raw.get("quantity")),
        confidence=_coerce_confidence(raw.get("confidence")),
        category=_coerce_category(raw.get("category")),
        notes=str(raw.get("notes") or "").strip()[:MAX_NOTES_LENGTH],
    )


def _coerce_quantity(value: object) -> int:
    try:
        quantity = int(float(value))  # accepts "3", 3.0, 3
    except (TypeError, ValueError):
        return 1
    return max(1, quantity)


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


def _coerce_category(value: object) -> str:
    category = str(value or "").strip()
    if not category:
        return FALLBACK_CATEGORY
    return _CANONICAL_CATEGORIES.get(category.lower(), FALLBACK_CATEGORY)


def extract_json_payload(text: str) -> dict | list:
    """Extract the first JSON object/array from model output.

    Handles common model quirks: markdown code fences, leading prose, and
    trailing commentary.  Raises ``ValueError`` when no valid JSON is found.
    """
    if not text or not text.strip():
        raise ValueError("empty response")
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\{\[]", cleaned):
        try:
            payload, _ = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, (dict, list)):
            return payload
    raise ValueError("no JSON object found in response")


def parse_detection_json(text: str, strict: bool = False) -> list[DetectedItem]:
    """Parse model output text into strict ``DetectedItem`` rows.

    In non-strict mode (legacy behavior) malformed input returns ``[]``.
    In strict mode (T3) malformed or shapeless input raises ``VisionError``
    with a user-safe message so the API can respond gracefully.
    """
    try:
        payload = extract_json_payload(text)
    except ValueError:
        if strict:
            raise VisionError(
                "The vision model returned output that could not be read as JSON. "
                "Try taking the photo again."
            )
        return []
    if isinstance(payload, dict):
        items = payload.get("items", [])
    else:
        items = payload
    if not isinstance(items, list):
        if strict:
            raise VisionError(
                "The vision model returned an unexpected format. Try taking the photo again."
            )
        return []
    detected = [item for item in (normalize_detection(raw) for raw in items) if item]
    return detected


class VisionProvider:
    def detect(self, image_path: Path, original_name: str | None = None) -> list[DetectedItem]:
        """Detect items in the photo at ``image_path``.

        ``original_name`` is the filename as uploaded by the user; stored
        files are renamed to opaque UUIDs, so filename-based providers must
        use this hint instead of ``image_path``.
        """
        raise NotImplementedError


class HeuristicVisionProvider(VisionProvider):
    common_words = {
        "box", "photo", "image", "img", "contents", "storage", "items", "iphone", "jpeg", "jpg", "png", "heic"
    }

    category_keywords: dict[str, set[str]] = {
        "Clothing & Accessories": {"glove", "gloves", "scarf", "hat", "shirt", "coat", "jacket", "boot", "shoe", "belt", "sock"},
        "Tools & Hardware": {"drill", "hammer", "screwdriver", "wrench", "tape", "nail", "screw", "bolt", "saw", "level", "chisel"},
        "Cables & Electronics": {"cable", "cord", "charger", "adapter", "hdmi", "usb", "extension", "power", "remote", "battery"},
        "Kitchen & Dining": {"plate", "cup", "mug", "pan", "pot", "utensil", "bowl", "fork", "spoon", "knife", "cutting"},
        "Documents & Paper": {"paper", "file", "folder", "document", "receipt", "manual", "book", "binder", "envelope"},
        "Seasonal & Holiday": {"christmas", "xmas", "halloween", "decoration", "ornament", "wreath", "lights", "holiday", "seasonal"},
        "Sports & Camping": {"tent", "stove", "lantern", "camping", "sleeping", "ball", "racket", "helmet", "bike", "ski", "fishing"},
        "Toys & Games": {"toy", "game", "puzzle", "lego", "doll", "block", "board", "card"},
        "Books & Media": {"book", "dvd", "cd", "vinyl", "magazine", "album"},
        "Home Decor": {"frame", "vase", "candle", "picture", "mirror", "rug", "pillow", "curtain"},
        "Cleaning & Household Supplies": {"cleaner", "soap", "spray", "mop", "broom", "sponge", "trash", "bag", "towel"},
        "Crafts & Hobbies": {"paint", "brush", "fabric", "yarn", "craft", "sewing", "knitting", "stamp"},
        "Sentimental / Keepsakes": {"photo", "album", "trophy", "medal", "keepsake", "memento"},
        "Donate / Sell": {"donate", "sell", "thrift", "giveaway"},
    }

    def detect(self, image_path: Path, original_name: str | None = None) -> list[DetectedItem]:
        source = Path(original_name).stem if original_name else image_path.stem
        stem = re.sub(r"[_-]+", " ", source.lower())
        tokens = [token for token in re.findall(r"[a-z0-9]+", stem) if token not in self.common_words and not token.isdigit()]
        if not tokens:
            return [DetectedItem("unidentified item", confidence=0.25, category=FALLBACK_CATEGORY, notes="No local vision provider configured.")]
        phrases = []
        if len(tokens) >= 2:
            phrases.append(" ".join(tokens[:3]))
        phrases.extend(tokens[:5])
        seen = set()
        detected = []
        for phrase in phrases:
            phrase = phrase.strip()
            if phrase in seen:
                continue
            seen.add(phrase)
            detected.append(DetectedItem(phrase, confidence=0.42, category=self._category(phrase), notes="Filename-based suggestion."))
        return detected[:6]

    def _category(self, name: str) -> str:
        words = set(re.findall(r"[a-z]+", name.lower()))
        for category, keywords in self.category_keywords.items():
            if words & keywords:
                return category
        return FALLBACK_CATEGORY


class OllamaVisionProvider(VisionProvider):
    def __init__(self) -> None:
        self.url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision")

    def detect(self, image_path: Path, original_name: str | None = None) -> list[DetectedItem]:
        cats = ", ".join(f'"{c}"' for c in HOUSEHOLD_CATEGORIES)
        prompt = (
            "You are creating a strict home inventory from one photo of an open storage container. "
            "List each distinct physical object you can see, with a count. "
            f"category MUST be exactly one of: {cats}. "
            "confidence is a number between 0 and 1. "
            'Respond with ONLY this JSON, no prose, no markdown: '
            '{"items":[{"name":"...","quantity":1,"confidence":0.0,"category":"...","notes":"..."}]}'
        )
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [encoded],
                    "stream": False,
                    "format": "json",
                },
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise VisionError(
                "Could not reach the local Ollama service. Make sure Ollama is running "
                "on the desktop host, then try again."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise VisionError(
                "The vision model took too long to respond. Try again with a smaller or clearer photo."
            ) from exc
        except requests.exceptions.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 404:
                raise VisionError(
                    f"The Ollama model '{self.model}' was not found. "
                    f"Run: ollama pull {self.model}"
                ) from exc
            raise VisionError("The vision service returned an error. Check the Ollama logs and try again.") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise VisionError("The vision service returned an unreadable response. Try again.") from exc
        text = body.get("response", "")
        return parse_detection_json(text, strict=True)


class OpenAIVisionProvider(VisionProvider):
    def detect(self, image_path: Path, original_name: str | None = None) -> list[DetectedItem]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return HeuristicVisionProvider().detect(image_path, original_name)
        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        data_url = f"data:{mime};base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"
        payload = {
            "model": os.environ.get("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"List visible storage-box objects as JSON with items: name, quantity, confidence, category (one of: {', '.join(HOUSEHOLD_CATEGORIES)}), notes."},
                    {"type": "input_image", "image_url": data_url},
                ],
            }],
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise VisionError("The cloud vision service could not be reached. Try again later.") from exc
        text = json.dumps(response.json())
        return parse_detection_json(text)


def get_provider() -> VisionProvider:
    if VISION_PROVIDER == "ollama":
        return OllamaVisionProvider()
    if VISION_PROVIDER == "openai":
        return OpenAIVisionProvider()
    return HeuristicVisionProvider()
