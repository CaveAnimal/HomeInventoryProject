# BL-004 — Receipt OCR into line items

- **Status:** parked
- **Origin:** [summary_suggestions GOALS.md](../support/summary_suggestions/GOALS.md) WS-2 (was ⚠️ MAYBE). Moved to the backlog by owner review on 2026-11-24.

## Idea
Read a photographed receipt with the local vision model and suggest its line items (description, price, purchase date, store), to be matched with existing items or added as new ones.

## Why deferred
WS-2 already lets a receipt photo be attached to an item and purchase data be entered by hand. Automatic extraction is a separate accuracy problem: matching receipt lines to inventory items is hard.

## What it would take
- A receipt prompt and a strict schema, validated like the detection contract (llm_vision D-003).
- A review screen that suggests matches, which must be confirmed (llm_vision D-002 applies).
- Local processing only. Receipts are personal documents (compare the `Documents & Paper` exclusion in cost_of_replacement).

## Depends on
WS-2 receipt attachments and purchase fields.

## Revisit when
WS-2 is in use and entering receipts by hand is a real chore.
