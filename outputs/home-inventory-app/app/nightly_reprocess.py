"""Nightly deep-scan reprocessing pass (T-DEEPSCAN).

Live/mobile capture uses a fast vision pass (Bonsai with thinking off by
default) so a photo returns suggestions in seconds. This module re-runs
every stored photo through a slower, more thorough pass -- Bonsai with
thinking on (label BONSAI_REPROCESS_VISION_MODEL), or with
VISION_PROVIDER=ollama the larger OLLAMA_REPROCESS_VISION_MODEL -- that
would be too slow for live capture but can run unattended overnight.

New detections are added as *additional* suggestions (pass_type='reprocess')
alongside the original fast-pass ones -- never replacing or dismissing them
-- so a household member reviews the union of both passes on the container
page. Each photo is only reprocessed once per model (see
repository.list_photos_pending_deep_scan / mark_photo_deep_scanned); if
the reprocess model label is changed later, every photo becomes pending
again under the new model.

Run manually:
    python -m app.nightly_reprocess [--model NAME] [--limit N]

Schedule nightly via cron / Windows Task Scheduler by pointing it at this
command with the app's virtualenv Python.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from .database import connect, migrate
from .repository import add_detection, list_photos_pending_deep_scan, mark_photo_deep_scanned
from .services.vision import BonsaiVisionProvider, OllamaVisionProvider, VisionError
from .settings import PHOTO_DIR, ensure_dirs, reprocess_vision_model


def _deep_scan_provider(model: str):
    # The deep scan always needs a real LLM, so anything other than an
    # explicit "ollama" (including "heuristic") runs on Bonsai with thinking on.
    if os.environ.get("VISION_PROVIDER", "bonsai").lower() == "ollama":
        return OllamaVisionProvider(model=model)
    return BonsaiVisionProvider(model=model, thinking=True)


def run(model: str | None = None, limit: int | None = None) -> dict:
    ensure_dirs()
    migrate()
    model = model or reprocess_vision_model()
    provider = _deep_scan_provider(model)

    conn = connect()
    try:
        photos = list_photos_pending_deep_scan(conn, model)
        if limit is not None:
            photos = photos[:limit]

        processed = 0
        suggestions_added = 0
        errors: list[dict] = []

        for photo in photos:
            image_path = PHOTO_DIR / photo["filename"]
            if not image_path.exists():
                errors.append({"photo_id": photo["id"], "error": "file missing on disk"})
                continue
            t0 = time.perf_counter()
            try:
                detected = provider.detect(image_path, original_name=photo["original_filename"])
            except VisionError as exc:
                errors.append({"photo_id": photo["id"], "error": str(exc)})
                continue
            duration_ms = int((time.perf_counter() - t0) * 1000)
            for item in detected:
                add_detection(
                    conn,
                    photo["box_id"],
                    photo["id"],
                    item.name,
                    item.confidence,
                    item.quantity,
                    item.category,
                    item.notes,
                    source_model=model,
                    pass_type="reprocess",
                )
                suggestions_added += 1
            mark_photo_deep_scanned(conn, photo["id"], model)
            conn.commit()
            processed += 1
            print(
                f"[{processed}/{len(photos)}] photo {photo['id']} ({photo['original_filename']}): "
                f"{len(detected)} suggestion(s) in {duration_ms}ms"
            )

        summary = {
            "model": model,
            "photos_pending": len(photos),
            "photos_processed": processed,
            "suggestions_added": suggestions_added,
            "errors": errors,
        }
        print(
            f"Deep scan complete: model={model} photos={processed}/{len(photos)} "
            f"suggestions_added={suggestions_added} errors={len(errors)}"
        )
        return summary
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Nightly deep-scan vision reprocessing")
    parser.add_argument("--model", default=None, help="Override the deep-scan model label")
    parser.add_argument("--limit", type=int, default=None, help="Max photos to process this run")
    args = parser.parse_args()
    summary = run(model=args.model, limit=args.limit)
    # Non-zero exit only when nothing succeeded, so a scheduler can flag a
    # fully broken run (e.g. Ollama down, model missing) without treating
    # normal partial-failure (one bad photo among many) as a hard error.
    sys.exit(1 if summary["errors"] and summary["photos_processed"] == 0 else 0)


if __name__ == "__main__":
    main()
