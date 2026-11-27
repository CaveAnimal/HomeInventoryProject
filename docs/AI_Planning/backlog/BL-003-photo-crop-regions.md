# BL-003 — Photo crop region (bounding box) per item

- **Status:** parked
- **Origin:** [summary_suggestions GOALS.md](../support/summary_suggestions/GOALS.md) WS-2 (was ⚠️ MAYBE). Moved to the backlog by owner review on 2026-11-24.

## Idea
Store where in a photo each detected item appears, so reports and item pages can show a cropped thumbnail of the item itself instead of the whole container photo.

## Why deferred
WS-2 already links each item to the photo it was detected in. That is enough evidence for insurance. Bounding boxes depend on the vision model returning reliable coordinates, which has not been tested, and they would change the strict detection contract (llm_vision D-003).

## What it would take
- A spike: does the local vision model (Bonsai/qwen-VL) return usable coordinates? Measure with `scripts/vision_eval`.
- Optional `bbox` fields in the detection contract (validated, clamped to 0–1), stored on `detection_suggestions` and carried to the item.
- A crop/thumbnail generator, and a UI to adjust boxes by hand.

## Depends on
The WS-2 item ↔ photo link.

## Note (2026-11-24)
Under PD-13 / WS-11 the app stores 2,400 px working copies, not originals. Crops would come from those working copies, which is still enough resolution for report thumbnails.

## Revisit when
WS-3 reports are in use and whole-photo thumbnails prove too unclear for crowded containers.
