# How This Folder Works — summary_suggestions

This folder turns the suggested further development in [docs/notes/summary/README.md](../../../notes/summary/README.md) into a plan built with the GOAL → CONTEXT → DECISIONS → TODO playbook ([abstract_goal_context_decisions_todo.md](../llm_vision/abstract_goal_context_decisions_todo.md)).

Start with [GOALS.md](GOALS.md). It is the first pillar and is at **Revision 3**: the owner's review answers and data-protection direction are applied. It is now at **Revision 4**, which adds the user-owned-originals change (WS-11). It is waiting for final approval of the licensing direction (PD-9) and the placement of WS-11 and WS-10.

---

## How GOALS.md fits the playbook

- **One program-level goal** in the playbook's GOAL format: objective, business model, business value, success criteria, in and out of scope, non-negotiable constraints, risks, and rollback. The constraints carry over the decisions already accepted in earlier epics:
  - local vision (llm_vision D-001)
  - human confirmation before anything enters inventory (llm_vision D-002)
  - the strict detection contract (llm_vision D-003)
  - the cost-lookup privacy rules (cost_of_replacement D-001…D-007)

  They also add a "back up `data/` before any git operation" rule, after the 2026-11-23 incident in which a branch switch destroyed the live database, and a rule that licensing must never send data off the client's machine.

- **Business model (owner direction):** clients **license the software** and run it on their own hardware. They edit their own inventory. Optionally, the owner documents a home and hands the finished inventory to the client's install. There are no immediate clients and no target date.

- **Twelve workstreams**, each using the same template sections (objective, why, success criteria, scope, constraints, risks, rollback):

  | WS | Name |
  |---|---|
  | WS-0 | Quick wins |
  | WS-1 | Status and loans: find anything, tell whether it is still in the house, see who has it (ten lifecycle statuses, including `in_repair` and `in_vehicle`) |
  | WS-2 | Insurance-grade records |
  | WS-3 | Client report |
  | WS-4 | Households, accounts and security, including household transfer between installs |
  | WS-5 | Downsizing |
  | WS-6 | Field work at a client's house |
  | WS-7 | Platform hardening (technical cleanup) |
  | WS-8 | Business readiness: an owner-led checklist, not code (license tiers, EULA, E&O, support) |
  | WS-9 | Licensing and distribution: installer, offline license, updates, user guide (added by owner review) |
  | WS-10 | Data protection: required encrypted backup to a second media type (USB drive), encouraged encrypted off-site copy to free or low-cost storage (added by owner direction; analysis in [DATA_PROTECTION.md](DATA_PROTECTION.md)) |
  | WS-11 | User-owned originals: the app stores 2,400 px working copies only; users keep and back up their own originals; Library-first capture (added by owner direction; design and workflow diagram in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md)) |

- **Each workstream becomes one TODO phase.** The playbook says to detail only near-term work ("rolling waves"), so WS-0 and WS-1 have specific success criteria. The rest stay at goal level until their phase is refined at the previous phase boundary. If a workstream grows past about 15 tasks, it moves into its own folder with its own GOAL/CONTEXT/DECISIONS/TODO set.

- **A traceability table** (GOALS.md §4) maps every suggestion in the summary, plus the owner-review additions, to its workstream: ✅ in scope, ❌ out of scope, or 📦 moved to the backlog.

- **Proposed decisions** (PD-1…PD-15; PD-5 withdrawn) are ready to seed DECISIONS.md. PD-11 (data protection strategy) and PD-12 (backup engine) have their full reasoning in [DATA_PROTECTION.md](DATA_PROTECTION.md). PD-13…PD-15 (working copies, capture paths, already-stored photos) have theirs in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md). **Nine time-boxed spikes** (SP-1, SP-2, SP-3, SP-4, SP-6, SP-7, SP-8, SP-9, SP-10) test the riskiest assumptions before any code depends on them. **SP-7** (can a typical household PC run the local vision model?) runs early, because it decides whether licensing is viable. **SP-9** confirms the backup engine before WS-10 is built. **SP-10** confirms iPhone capture behavior before WS-11 is built.

- **Order (confirmed by owner; WS-11 and WS-10 placement proposed):** Phase 0 (discovery and spikes) → WS-0 → WS-1 → WS-11 → WS-10 → WS-3 (first version) → WS-2 → WS-4 → WS-5 → WS-6 → WS-9. WS-7 runs alongside as needed, and WS-8 runs in parallel, led by the owner.

---

## Supporting analysis documents

Some decisions need more reasoning than a row in a table. Their analysis lives in its own file in this folder, and GOALS.md links to it:

| File | Supports | Summary |
|---|---|---|
| [DATA_PROTECTION.md](DATA_PROTECTION.md) | PD-11, PD-12, WS-10, SP-9 | 3-2-1 backup at the least cost: required encrypted USB backup ($0–15), encouraged encrypted off-site copy to the customer's own Google Drive/OneDrive ($0) or Backblaze B2 (low cost), restic + rclone engine, customer-held keys with a printable Recovery Sheet |
| [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) | PD-13, PD-14, PD-15, WS-11, SP-10 | The app stores 2,400 px working copies (measured −74%), never originals; Library-first capture; Quick Photo save prompt; inbox files left alone. Includes the capture **workflow diagram** (Mermaid + plain text). |

When DECISIONS.md is created, each analysis becomes the body of its decisions.

---

## The backlog

Ideas that were ⚠️ MAYBE in the first revision were moved by the owner to the project backlog at [docs/AI_Planning/backlog/](../../backlog/README.md):

| ID | Item |
|---|---|
| BL-001 | Read-only share links |
| BL-002 | Family claiming / voting view |
| BL-003 | Photo crop regions per item |
| BL-004 | Receipt OCR |
| BL-005 | Barcode check-in/out for loans |
| BL-006 | Report branding / white-labeling |

An item comes back into a plan only by being **promoted**: its backlog file is marked `promoted`, and the plan's DECISIONS.md records a scope change.

---

## Owner review status

All five review questions are answered, and the data-protection direction is recorded (GOALS.md §8). Two items are still open:

- **Confirm PD-9:** licensed, self-run software as the primary model, with an optional documentation service and hand-over.
- **Confirm WS-11 and WS-10 placement:** right after WS-1 (WS-11, then WS-10), before the client report.

When both are confirmed, GOALS.md is marked **Status: APPROVED**.

---

## Documents in this folder

| File | Status | Purpose |
|---|---|---|
| [GOALS.md](GOALS.md) | Revision 4, awaiting PD-9 and WS-11/WS-10 placement confirmation | What is being built and why (pillar 1) |
| HOW_IT_WORKS.md | — | This guide |
| [DATA_PROTECTION.md](DATA_PROTECTION.md) | PROPOSED, pending SP-9 | Decision analysis for PD-11 / PD-12 |
| [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) | PROPOSED, pending SP-10 | Decision analysis for PD-13 / PD-14 / PD-15, with workflow diagram |
| `CONTEXT.md` | To create | Current system (from summary §3) and target state per workstream (pillar 2) |
| `DECISIONS.md` | To create | Seeded with PD-1…PD-15, references to inherited D-numbers, and the §8 scope changes (pillar 3) |
| `TODO.md` | To create | Phase 0 (including SP-7, SP-9 and SP-10), then full detail for WS-0 and WS-1 only (pillar 4) |
| `SPRINT_STORY_summary_suggestions.md` | To create | Jira-ready stories derived from TODO.md, one per task |

Create them in the order listed, each reviewed by the owner before the next one starts, as the playbook requires.
