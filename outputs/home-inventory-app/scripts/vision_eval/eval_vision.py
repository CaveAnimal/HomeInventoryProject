"""Small local eval harness for the Ollama vision provider.

Runs each photo in golden_set.json through the configured provider and
scores detections against hand-labeled expected keywords. Not a rigorous
benchmark -- just enough signal to compare prompt/preprocessing/model
changes against each other instead of eyeballing results.

Usage:
    python scripts/vision_eval/eval_vision.py
    OLLAMA_VISION_MODEL=llama3.2-vision python scripts/vision_eval/eval_vision.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.services.vision import OllamaVisionProvider, VisionError  # noqa: E402

# keyword -> synonyms/aliases that count as a match against a detected item name
ALIASES: dict[str, list[str]] = {
    "tape measure": ["tape measure", "measuring tape", "tape rule"],
    "ruler": ["ruler", "rule", "straightedge"],
    "file": ["file", "rasp", "needle file"],
    "pick": ["pick", "scribe", "probe", "awl", "dental"],
    "tweezers": ["tweezers", "forceps"],
    "pencil": ["pencil", "pencils"],
    "screwdriver": ["screwdriver", "bit set", "driver bit", "precision bit"],
    "electronics": ["electronic", "circuit", "chip", "component", "connector", "relay", "wire", "cable", "pcb"],
}


def matches(expected_keyword: str, detected_name: str) -> bool:
    name = detected_name.lower()
    for alias in ALIASES.get(expected_keyword, [expected_keyword]):
        if alias in name:
            return True
    return False


def score_photo(expected: list[str], detected_names: list[str]) -> dict:
    """Greedy one-to-one matching so duplicate expected keywords (e.g. two
    "ruler" entries) each need their own distinct detected item, instead of
    both matching the same detection."""
    available = list(enumerate(detected_names))
    matched_detected_idx: set[int] = set()
    missed = []
    for keyword in expected:
        found_idx = next((idx for idx, name in available if matches(keyword, name)), None)
        if found_idx is None:
            missed.append(keyword)
            continue
        matched_detected_idx.add(found_idx)
        available = [(idx, name) for idx, name in available if idx != found_idx]

    matched_count = len(expected) - len(missed)
    recall = matched_count / len(expected) if expected else 1.0
    precision = len(matched_detected_idx) / len(detected_names) if detected_names else 0.0
    unmatched_detections = [n for i, n in enumerate(detected_names) if i not in matched_detected_idx]
    return {
        "recall": recall,
        "precision": precision,
        "missed": missed,
        "unmatched_detections": unmatched_detections,
    }


def main() -> None:
    golden = json.loads((Path(__file__).parent / "golden_set.json").read_text())
    provider = OllamaVisionProvider()
    model_label = provider.model

    print(f"=== Vision eval run: model={model_label} url={provider.url} ===\n")

    total_recall = 0.0
    total_precision = 0.0
    n = 0

    for case in golden:
        image_path = ROOT / case["photo"]
        if not image_path.exists():
            print(f"SKIP {case['photo']} (file not found)")
            continue

        t0 = time.perf_counter()
        try:
            detections = provider.detect(image_path, original_name=image_path.name)
        except VisionError as exc:
            print(f"FAIL {case['photo']}: {exc}")
            continue
        elapsed = time.perf_counter() - t0

        detected_names = [d.name for d in detections]
        result = score_photo(case["expected"], detected_names)
        total_recall += result["recall"]
        total_precision += result["precision"]
        n += 1

        print(f"--- {case['photo']} ({elapsed:.1f}s) ---")
        print(f"  detected ({len(detections)}): {[(d.name, round(d.confidence, 2)) for d in detections]}")
        print(f"  recall={result['recall']:.2f} precision={result['precision']:.2f}")
        if result["missed"]:
            print(f"  MISSED expected: {result['missed']}")
        if result["unmatched_detections"]:
            print(f"  UNMATCHED (possible hallucinations): {result['unmatched_detections']}")
        print()

    if n:
        print(f"=== avg recall={total_recall / n:.2f} avg precision={total_precision / n:.2f} over {n} photo(s) ===")
    else:
        print("No photos scored.")


if __name__ == "__main__":
    main()
