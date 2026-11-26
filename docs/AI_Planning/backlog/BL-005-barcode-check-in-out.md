# BL-005 — Barcode/QR check-in and check-out for loans

- **Status:** parked
- **Origin:** [summary_suggestions GOALS.md](../support/summary_suggestions/GOALS.md) WS-1 (was listed as ⚠️ MAYBE later). Moved to the backlog by owner review on 2026-11-24.

## Idea
Put small QR or barcode stickers on frequently loaned items (tools, camping gear). Scanning one opens a one-tap "lend to…" or "returned" screen, like a library checkout.

## Why deferred
WS-1 delivers loans from the item page, which is enough to start. Per-item labels add printing and sticker work that only pays off for items lent out often.

## What it would take
- A per-item `public_id` and label generation, reusing `services/labels.py` and the container QR pattern.
- A mobile check-in/check-out page wired to the WS-1 loans table.

## Depends on
The WS-1 loans table.

## Revisit when
WS-1 has been used for a while and the same items keep being lent out.
