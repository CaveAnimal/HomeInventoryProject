# PROJECT CONTEXT

> AI AGENT INSTRUCTIONS: This document defines implementation context for the llm_vision workflow. If a change is outside this context, request clarification before implementation.

## Current System Overview

### Purpose
The current Home Inventory app is a local-first FastAPI application that stores containers, photos, detections, and confirmed items in SQLite. It already supports mobile capture via Safari and can run Ollama vision locally.

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Language | Python | 3.x | Runtime for app and services |
| Framework | FastAPI + Jinja2 | Current repo state | Server-rendered pages with JSON APIs |
| Frontend | HTML/CSS/Vanilla JS | Current repo state | Mobile capture UI already exists |
| Database | SQLite | file-based | Local-first, migrations in SQL |
| Vision Runtime | Ollama | local install | `llama3.2-vision` available |
| Test framework | pytest | current repo state | Core flow tests exist |

### Architecture Overview
- Route and page orchestration: `outputs/home-inventory-app/app/main.py`
- Data access and persistence: `outputs/home-inventory-app/app/repository.py`
- Vision provider abstraction and parsing: `outputs/home-inventory-app/app/services/vision.py`
- Mobile capture UX: `outputs/home-inventory-app/app/templates/capture.html`
- Generic client behaviors: `outputs/home-inventory-app/app/static/app.js`

Data flow today:
1. User uploads photo to `/api/boxes/{box_id}/photos`.
2. Server stores image under `data/photos` and calls vision provider.
3. Provider returns detections; app stores them in `detection_suggestions`.
4. User confirms suggestions later on container detail page.

### Key Files and Their Roles

| File Path | Purpose | Change Expected? |
|-----------|---------|------------------|
| outputs/home-inventory-app/app/main.py | API endpoints and page routes | Yes - add/adjust capture-first container flow and confirmation flow |
| outputs/home-inventory-app/app/services/vision.py | Provider logic, prompt, JSON parsing | Yes - tighten strict output contract and resilience |
| outputs/home-inventory-app/app/templates/capture.html | iPhone capture + immediate feedback | Yes - support explicit confirm list with quantity |
| outputs/home-inventory-app/app/repository.py | Persistence helper functions | Likely - batch confirm semantics and audit states |
| outputs/home-inventory-app/migrations/*.sql | DB schema migration files | Maybe - only if additional state is required |
| outputs/home-inventory-app/tests/test_core.py | Core regression tests | Yes - add end-to-end test cases for new flow |

### Current Behavior (Baseline)
Scenario 1: Mobile capture to existing container
- Current behavior: User selects an existing container, takes photo, sees detected names + confidence, then reviews on container page.
- Limitation: Capture page does not provide a final confirm-and-save action for item counts.

Scenario 2: Creating new container
- Current behavior: Container can be created from `/boxes/new`; default `container_type` is already `box` in API.
- Limitation: Not integrated as one smooth iPhone capture-first flow.

Scenario 3: Vision extraction
- Current behavior: Ollama prompt requests JSON items with quantity/confidence/category/notes.
- Limitation: Parser is permissive and may accept malformed model output without explicit user-facing recovery path.

## Hard Constraints (DO NOT VIOLATE)

| Constraint | Rationale | Impact |
|------------|-----------|--------|
| Local-first operation remains primary | User privacy and convenience | Ollama path must work without cloud APIs |
| Existing SQLite data must remain valid | Preserve user inventory history | Backward-compatible schema changes only |
| iPhone Safari workflow is mandatory | Primary user capture device | Avoid desktop-only interactions in core flow |
| Default container type is `box` in this phase | User requirement | Do not introduce branching type UX yet |
| Confirmation before persistence | Data quality | Never auto-promote raw detections as confirmed items |

## Required Knowledge

### Domain Concepts
| Concept | Description | Why It Matters | Where to Learn |
|---------|-------------|----------------|----------------|
| Container | Physical storage unit in the home inventory model | Every photo and item ties to one container | outputs/home-inventory-app/README.md |
| Detection suggestion | AI-generated candidate item from photos | Must be reviewed before becoming inventory | outputs/home-inventory-app/app/main.py |
| Confirmed inventory item | Persisted item in `box_items` | Source of truth for search/export/labels | outputs/home-inventory-app/app/repository.py |

### Technical Patterns in This Codebase
| Pattern | Where Used | How It Works | Why We Use It |
|---------|------------|--------------|---------------|
| Provider abstraction | `services/vision.py` | `get_provider()` resolves heuristic/ollama/openai | Easy switching of vision backends |
| Server-rendered capture + JS fetch | `templates/capture.html` | Upload via `fetch` to JSON API | Fast mobile UX with minimal SPA complexity |
| Repository helper layer | `repository.py` | Encapsulates insert/update/history operations | Keeps route handlers compact and consistent |

### Integration Points
| System/Service | Purpose | How We Interact | Constraints |
|----------------|---------|-----------------|-------------|
| Ollama API (`/api/generate`) | Local vision inference | HTTP POST with base64 image | Model must exist and be reachable from app host |
| iPhone Safari camera/file input | Photo capture and upload | `<input type="file" accept="image/*" capture="environment">` | Browser permissions and network path required |
| SQLite | Persistence of containers/detections/items | SQL via repository helpers | Must preserve migration discipline |

## Target State (After Project Completion)

### What Will Change
- Capture page supports creating a new container inline, then immediately uploading iPhone photos.
- Detection response shown on the same iPhone page includes strict item name + count + confidence + category.
- User can confirm selected detections from that page; confirmed items are written to permanent inventory.
- The flow clearly separates suggested vs confirmed states with audit history.

### What Will NOT Change
- Existing dashboard/search/labels workflows remain available.
- Local SQLite + local filesystem storage remain the default persistence model.
- Vision provider abstraction remains in place.

### Migration Path
Current state -> Phase 1 API hardening -> Phase 2 mobile confirm UX -> Phase 3 persistence + tests -> Target state
- Phase 1: Strict schema validation and robust parse/error responses.
- Phase 2: Capture page UI for inline container creation and item confirmation.
- Phase 3: Confirmation persistence path, regression tests, and acceptance checklist.

## Reference Materials

### Internal Documentation
- `docs/AI_Planning/support/llm_vision/GOAL.md`: target outcomes and constraints.
- `docs/notes/mobile-photo-capture/README.md`: existing mobile capture expectations.
- `docs/notes/mobile-photo-capture/ai-vision-guide.md`: vision result shape and quality guidance.
- `outputs/home-inventory-app/README.md`: current app behavior and setup.

### External Resources
- Ollama model docs for `llama3.2-vision`: local vision model behavior and prompt guidance.
- FastAPI docs for file upload handling and form+file endpoints.

### Key People/Contacts
- Product owner/user: defines acceptance for inventory strictness and mobile usability.
