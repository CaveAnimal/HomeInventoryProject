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


@dataclass
class DetectedItem:
    name: str
    quantity: int = 1
    confidence: float = 0.5
    category: str = ""
    notes: str = ""


class VisionProvider:
    def detect(self, image_path: Path) -> list[DetectedItem]:
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

    def detect(self, image_path: Path) -> list[DetectedItem]:
        stem = re.sub(r"[_-]+", " ", image_path.stem.lower())
        tokens = [token for token in re.findall(r"[a-z0-9]+", stem) if token not in self.common_words and not token.isdigit()]
        if not tokens:
            return [DetectedItem("unidentified item", confidence=0.25, notes="No local vision provider configured.")]
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
        return "Unknown / Needs Review"


class OllamaVisionProvider(VisionProvider):
    def __init__(self) -> None:
        self.url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision")

    def detect(self, image_path: Path) -> list[DetectedItem]:
        cats = ", ".join(f'"{c}"' for c in HOUSEHOLD_CATEGORIES)
        prompt = (
            "Identify physical objects visible in this storage box photo. "
            f"Use one of these categories: {cats}. "
            "Return only JSON: {\"items\":[{\"name\":\"...\",\"quantity\":1,\"confidence\":0.0,\"category\":\"...\",\"notes\":\"...\"}]}"
        )
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        response = requests.post(
            self.url,
            json={"model": self.model, "prompt": prompt, "images": [encoded], "stream": False},
            timeout=90,
        )
        response.raise_for_status()
        text = response.json().get("response", "{}")
        return parse_detection_json(text)


class OpenAIVisionProvider(VisionProvider):
    def detect(self, image_path: Path) -> list[DetectedItem]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return HeuristicVisionProvider().detect(image_path)
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
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        text = json.dumps(response.json())
        return parse_detection_json(text)


def parse_detection_json(text: str) -> list[DetectedItem]:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    items = data.get("items", [])
    detected = []
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        detected.append(
            DetectedItem(
                name=name,
                quantity=max(1, int(item.get("quantity") or 1)),
                confidence=float(item.get("confidence") or 0.5),
                category=str(item.get("category") or ""),
                notes=str(item.get("notes") or ""),
            )
        )
    return detected


def get_provider() -> VisionProvider:
    if VISION_PROVIDER == "ollama":
        return OllamaVisionProvider()
    if VISION_PROVIDER == "openai":
        return OpenAIVisionProvider()
    return HeuristicVisionProvider()
