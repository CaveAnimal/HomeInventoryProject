# Using AI Vision to Identify Objects in Container Photos

## Overview

When you upload a photo of an open container, the app sends the image to an AI vision model. The model looks at the photo and returns a list of every physical object it can identify — name, estimated quantity, confidence, and category. Those become "suggested items" that you review and confirm.

---

## How to Get Good Results

### Take the right photos

The model works best when objects are visible, distinct, and well-lit. Three photos cover most containers well:

| Shot | What to capture |
|---|---|
| **Top-down overview** | Everything in the container laid out or stacked — gives the model a complete census |
| **Close-up of small items** | Anything overlapping, bundled, or hard to distinguish from a distance |
| **Labels and markings** | Model numbers, serial stickers, document titles, book spines, tool brands |

You do not need a photo of every individual item. The overview shot does most of the work.

### Practical tips

- Open the lid or flaps fully before shooting — partially visible items are often missed
- Natural light or a bright overhead light reduces blur and shadow
- Hold the phone steady; a blurry photo cuts accuracy significantly
- If the container is deep, angle the shot slightly so the bottom layer is visible
- For dark containers (black totes, tool chests), use the phone's torch

---

## What the Model Returns

Each detected item comes back with:

```json
{
  "name": "10mm socket",
  "quantity": 1,
  "confidence": 0.82,
  "category": "Tools & Hardware",
  "notes": "Visible in top-right corner, appears to be part of a socket set"
}
```

- **name** — plain English description of the object
- **quantity** — count if multiple identical items are clearly visible; defaults to 1 when uncertain
- **confidence** — 0 to 1; above 0.7 is reliable, 0.4–0.7 is a reasonable guess, below 0.4 is speculative
- **category** — one of the 15 household categories (see below)
- **notes** — any contextual detail the model noticed (color, brand, condition, location in frame)

---

## Categories

The model is instructed to assign one of these categories to every item:

- Clothing & Accessories
- Tools & Hardware
- Cables & Electronics
- Kitchen & Dining
- Documents & Paper
- Seasonal & Holiday
- Sports & Camping
- Toys & Games
- Books & Media
- Home Decor
- Cleaning & Household Supplies
- Crafts & Hobbies
- Sentimental / Keepsakes
- Donate / Sell
- Unknown / Needs Review

If the model is unsure, it returns **Unknown / Needs Review** so you can categorize it yourself.

---

## Vision Providers

The app supports three interchangeable providers, configured via the `VISION_PROVIDER` environment variable.

### Heuristic (default — no AI required)

Derives guesses from the photo filename. Useful for testing or offline use. Accuracy is low; confidence is capped at 0.42. Set `VISION_PROVIDER=heuristic` or leave it unset.

### Ollama (local AI — private, no cloud)

Runs a vision-capable model on your own machine. Requires [Ollama](https://ollama.com) installed and a vision model pulled:

```bash
ollama pull llama3.2-vision
```

Set in your environment:

```
VISION_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api/generate   # default
OLLAMA_VISION_MODEL=llama3.2-vision              # default
```

Photos never leave your machine. Good choice for a home inventory with sensitive documents or valuables.

### OpenAI (cloud — highest accuracy)

Uses GPT-4.1 mini vision via the OpenAI API. Requires an API key.

```
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_VISION_MODEL=gpt-4.1-mini   # default
```

This sends photo data to OpenAI's servers. Check their [data usage policy](https://openai.com/policies/api-data-usage-policies) if that matters for your use case.

---

## Reviewing Detections

After uploading, go to the container's detail page. The **Suggested from photos** section lists every item the model detected. For each suggestion:

- **Confirm** — adds it to the container's item list with status `likely`
- **Dismiss** — removes the suggestion without adding it

Confirmed items can be upgraded to `confirmed` status by editing the item row directly.

---

## When Detection Misses Things

Vision models are not perfect. Common failure modes:

| Problem | Why it happens | Fix |
|---|---|---|
| Bundled cables look like one item | Overlapping identical objects are hard to count | Separate them before shooting, or add manually |
| Small text on documents not read | Low resolution at distance | Take a close-up label shot |
| Items in bags or cases not detected | Model only sees the bag | Open the bag, take a second photo |
| Confidence below 0.4 on everything | Photo is blurry or too dark | Retake in better light |
| Wrong category assigned | Model uncertainty | Edit the category on the item row |

When the model misses something, add the item manually on the container page — manual entries are always `confirmed` status.

---

## Standard Classification (Optional)

Each item in the database has three optional fields for mapping to public classification standards:

| Field | Purpose |
|---|---|
| `standard_system` | Which standard (e.g., `UNSPSC`, `GS1 GPC`) |
| `standard_code` | The numeric or alphanumeric code |
| `standard_label` | Human-readable label from that standard |

These are not populated by AI detection today. They exist for future use — for example, mapping to UNSPSC codes for insurance documentation or asset tracking that requires a standard taxonomy.
