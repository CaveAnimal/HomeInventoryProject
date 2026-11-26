# PROJECT GOALS — summary_suggestions

*Pillar 1 of the GOAL → CONTEXT → DECISIONS → TODO framework
([abstract_goal_context_decisions_todo.md](../llm_vision/abstract_goal_context_decisions_todo.md)).
See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for how this folder is organized.*

- **Status:** REVISION 4. Owner review answers from 2026-11-24 are applied (§8), plus two owner directions: data protection (WS-10, PD-11, PD-12, [DATA_PROTECTION.md](DATA_PROTECTION.md)) and user-owned originals (WS-11, PD-13…PD-15, [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md)). Awaiting final approval of the licensing direction (PD-9) and the placement of WS-10 and WS-11.
- **Created:** 2026-11-24 · **Revised:** 2026-11-24
- **Source of every goal below:** [docs/notes/summary/README.md](../../../notes/summary/README.md) (application review of 2026-11-23), §3.7 *Current limitations*, §4.1 *Sprint roadmap*, §4.2 *Business considerations*, §4.3 *Quick wins*. There are three additions, all from the owner and all recorded as scope changes: **WS-9 Licensing & Distribution** (§8, Q4), **WS-10 Data Protection** (§8, item 6) and **WS-11 User-Owned Originals** (§8, item 7).
- **Deferred ideas:** items once classified ⚠️ MAYBE were moved to the [project backlog](../../backlog/README.md) (BL-001…BL-006) by owner decision.

---

## 0. How to Use This Document

This file is plural (GOALS) because the source suggestions make up a **program of several workstreams**, not one feature. It is organized so the rest of the framework can be built from it directly:

| Framework document | How it derives from this file |
|---|---|
| `CONTEXT.md` (next) | Describe the current system once for the whole program, using summary §3. Add a *Target State* subsection per workstream. |
| `DECISIONS.md` | Start with the **Proposed Decisions** in §6 (status `PROPOSED`). Add the inherited constraints in §1 as references to the existing D-numbers. Record the §8 owner answers as a scope-change decision. |
| `TODO.md` | **One TODO phase per workstream** (WS-0 → Phase 1, WS-1 → Phase 2, …), with Phase 0 = discovery plus the spikes in §7. Apply rolling waves: only WS-0 and WS-1 get full task detail at first. Later workstreams stay coarse until refined at a phase boundary. |
| `SPRINT_STORY_summary_suggestions.md` | Epic = §1 Program Goal. One story per TODO task. Spikes from §7 become Spike stories. |

**Splitting rule:** if a workstream grows past about 15 TODO tasks, or needs its own release, move it into its own folder (for example `support/client_report/`) with its own G/C/D/T set. Copy that workstream's section from here as its `GOAL.md`, and record the split in DECISIONS.md as a scope change.

**Classification key** (framework Step 1B): ✅ IN SCOPE · ❌ OUT OF SCOPE · 📦 BACKLOG (moved to `docs/AI_Planning/backlog/`; not part of this program unless promoted)

---

## 1. PROGRAM GOAL

### Primary Objective
Turn Home Inventory from a single-household personal tool into **licensable software**: a household runs its own copy to cover insurance documentation, downsizing, finding belongings and tracking loaned items. The owner can optionally offer a setup-and-documentation service on top. Local-first privacy is kept throughout.

### Business Model (owner direction, 2026-11-24)
- **Primary:** clients **license the software** and run it on their own hardware. They own their data and edit their own inventory.
- **Optional add-on:** the owner documents a client's home (photography + AI cataloging) and hands the finished inventory over to the client's licensed install.
- **No immediate clients and no target date.** Work proceeds by priority, without deadline pressure.
- The model is recorded as **PD-9** (§6) for formal acceptance in DECISIONS.md.

### Why This Matters (Business Value)
- The application already does the hardest part (photos → AI suggestions → confirmed, searchable, located inventory). What's missing is mostly packaging: reports, status tracking, security and distribution (summary §1).
- Privacy ("your photos never leave your house") is a real differentiator for software people run at home, so every workstream must preserve it.
- The owner's own use cases are served along the way: finding anything, knowing whether it is still in the house, and knowing who borrowed it.

### Success Criteria (Definition of Done for the Program)
- [ ] All six quick wins in WS-0 are shipped.
- [ ] Any item can be marked with a lifecycle status, and loans record borrower and dates (WS-1).
- [ ] Items can hold insurance fields (brand, model, serial, purchase data, condition) and per-item evidence photos (WS-2).
- [ ] A client-ready PDF report (Insurance, Downsizing and Quick-find variants) can be generated from an install (WS-3).
- [ ] An install has logins, can hold more than one household inventory, and can transfer a household between installs (WS-4).
- [ ] Items carry a downsizing disposition and a recipient assignment (WS-5).
- [ ] A capture session can run at a client's house and be finished afterwards (WS-6).
- [ ] Platform hardening items are done (WS-7), and business-readiness items are recorded with owner decisions (WS-8).
- [ ] A non-technical client can install, license, run and update the software on supported hardware (WS-9).
- [ ] Every install keeps an automatic, encrypted, versioned backup on a second media type (USB drive). An encrypted off-site backup to free or low-cost storage is offered and encouraged, and a restore has been tested (WS-10).
- [ ] The app stores only reduced working copies of photos, never originals. Every capture path leaves the original with the user, or tells the user plainly when no original will exist (WS-11).
- [ ] **Throughout:** no new test failures beyond the known baseline (6 pre-existing Windows failures, 51 passing as of 2026-11-23). Every workstream adds tests for what it builds.

### In Scope
WS-0 through WS-11 as defined in §2 and §3.

### Explicitly Out of Scope (Program-wide)
- ❌ Moving AI vision or photo storage to a cloud service by default (contradicts llm_vision D-001).
- ❌ Saving AI suggestions to inventory without human confirmation (contradicts llm_vision D-002).
- ❌ A native iOS/Android app. The phone browser stays the capture surface (llm_vision GOAL).
- ❌ Certified appraisals. The app produces *estimated* replacement or resale values with cited sources only (summary §4.2).
- ❌ A hosted SaaS version where client data lives on the owner's servers.
- ❌ Payment processing, storefront, invoicing or CRM (licenses can be sold through an existing third-party store if needed; see WS-9).
- ❌ Rewriting the stack (FastAPI + SQLite + Jinja2 stays).

### Non-Negotiable Constraints (inherited — do not violate)
| Constraint | Source | Why |
|---|---|---|
| Photos and inventory data stay on hardware the household controls; vision runs locally (now Bonsai via llama.cpp, Ollama optional) | llm_vision D-001 | Privacy is the product's differentiator |
| AI output is a *suggestion* until a person confirms it | llm_vision D-002 | Accuracy and trust |
| All vision output passes the strict detection contract (`normalize_detection`) | llm_vision D-003 | Data integrity |
| Cost lookup: provider abstraction, local LLM reasoning, one item per request, kill switch, budget guard | cost_of_replacement D-001…D-007 | Privacy and spend control |
| Estimates are insert-only history | cost_of_replacement D-004 | Auditability for insurance |
| Database changes are **additive SQL migrations only** (new tables or columns, no destructive changes); existing data must stay valid | Migration pattern 001–007 | The live inventory is irreplaceable, and licensed installs must upgrade safely |
| **Back up `outputs/home-inventory-app/data/` before any branch switch, checkout or reset** | Incident 2026-11-23 (a branch switch destroyed the live DB) | Data loss prevention |
| Every user-visible change is recorded in `edit_history` | Existing pattern (`record_history`) | Insurance evidence trail |
| Licensing must not send inventory data or usage telemetry off the client's machine | Follows from D-001 (proposed as PD-10) | A license check that phones home would break the privacy promise |
| **Every backup copy is encrypted, local ones included.** The customer alone holds the key; the vendor never holds customer data or keys. | PD-11 / [DATA_PROTECTION.md](DATA_PROTECTION.md) | An inventory is a burglar's shopping list; vendor-held data would break the privacy promise |
| **The app keeps working copies, not original photos.** Users own their originals and the backup of those originals. | PD-13 / [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) | Owner direction; clear responsibility; 74% less storage; no GPS held |

### Risk Assessment (Program)
| Risk | Impact | Mitigation |
|---|---|---|
| **Typical client PCs can't run the local vision model** (Bonsai 27B needs a strong GPU) | High | Spike SP-7 early: minimum hardware, smaller-model quality, fallback options. This affects whether licensing is viable at all. |
| Multi-household/transfer (WS-4) leaks data between households | High | Spike SP-4; decide on the isolation model before any code; isolation tests |
| AI values used in real insurance claims are wrong | High | Always labeled "estimate", with source URL and age; disclaimer in reports; E&O insurance and EULA wording (WS-8) |
| Schema changes break upgrades on licensed installs | High | Additive migrations; automatic pre-upgrade backup; upgrade tested on copies of real databases |
| Support burden from non-technical clients | Medium | Installer, health checks and documentation in WS-9 |
| A user relies on the app for originals it no longer keeps (for example "Quick Photo" without saving to the phone) | Medium | WS-11: Library-first capture, a "save original to phone" prompt, plain warnings, a user-guide chapter, and EULA wording |
| Customer loses data through a drive failure, theft, fire or ransomware, or loses the backup password | High | WS-10: required second-media backup, encouraged off-site copy, printable Recovery Sheet, regular restore tests |
| Scope creep from a long suggestion list | Medium | Rolling-wave TODO; MAYBE items parked in the backlog; owner review at each phase boundary |

### Rollback Plan (Program)
- Each workstream ships behind its own migration(s) and UI entry points. Rolling back a workstream means reverting its commits; its new tables can be left in place or dropped without touching core tables.
- Restore data from `D:\HomeInventoryBackups` (weekly, integrity-checked) if a migration damages the owner's database. Licensed installs get the same safety from an automatic backup before each upgrade (WS-9).
- Time to roll back one workstream: under 30 minutes.

---

## 2. WORKSTREAM OVERVIEW & SEQUENCE

| WS | Name | Summary source | Priority | Depends on | Refinement now |
|---|---|---|---|---|---|
| WS-0 | Quick Wins | §4.3 | P1 | — | Full detail |
| WS-1 | Where Is It & Is It Still Here (status + loans) | §4.1 Sprint 1 | P1 | — | Full detail |
| WS-2 | Insurance-Grade Records | §4.1 Sprint 2 | P2 | — | Coarse |
| WS-3 | Client Report | §4.1 Sprint 3 | P1 | WS-0 (totals), benefits from WS-1/WS-2 | Coarse; first after WS-1 |
| WS-4 | Households, Accounts & Security | §4.1 Sprint 4 | P2 | Spike SP-4 | Coarse |
| WS-5 | Downsizing Workflow | §4.1 Sprint 5 | P3 | WS-1 (status), WS-3 (report variant) | Coarse |
| WS-6 | Field Efficiency | §4.1 Sprint 6 | P3 | WS-4 (transfer), spike SP-6 | Coarse |
| WS-7 | Platform Hardening | §3.7 | P2 (run alongside) | — | Coarse |
| WS-8 | Business Readiness (non-code) | §4.2 | Owner-driven | — | Checklist |
| WS-9 | Licensing & Distribution | Owner review §8 Q4 | P3 (no clients yet) | WS-4, spike SP-7 | Coarse |
| WS-10 | Data Protection (backup strategy) | Owner direction §8 item 6 | P1 | Spike SP-9; WS-11 (what gets stored) | Coarse; detail in [DATA_PROTECTION.md](DATA_PROTECTION.md) |
| WS-11 | User-Owned Originals (capture change) | Owner direction §8 item 7 | P1 | Spike SP-10 | Coarse; detail and workflow diagram in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) |

**Order (confirmed by owner, 2026-11-24; WS-11 and WS-10 placement proposed, awaiting confirmation):**
`Phase 0 discovery + spikes → WS-0 → WS-1 → WS-11 → WS-10 → WS-3 (first version) → WS-2 → WS-4 → WS-5 → WS-6 → WS-9`. WS-7 runs alongside as needed, and WS-8 runs in parallel, led by the owner.

- WS-11 comes before WS-10 because the backup design depends on what the app stores: working copies make backups about 74% smaller.
- WS-10 follows directly, because data safety comes before new features: the live database was lost once already, on 2026-11-23. The owner's own install becomes the first real user of the customer backup design. WS-9 later reuses WS-10's first-run setup steps.

- WS-3 comes before WS-2 and WS-4 because the report shows value early and later fields plug into it.
- WS-9 comes last because there are no immediate clients. But **SP-7 (client hardware) runs early**, in Phase 0 or before WS-4 is refined, because its answer could change WS-4 and WS-6.

---

## 3. WORKSTREAM GOALS

Each workstream uses the framework's GOAL template sections. A workstream marked *Coarse* gets its detailed acceptance criteria when its TODO phase is refined (rolling wave). Its criteria below are goal-level only.

---

### WS-0 — Quick Wins

**Objective:** Fix the six small, high-value gaps the review found, each in hours, not days.

**Why:** Immediate usefulness for insurance exports and day-to-day trust in the app. They also provide the value totals that WS-3 needs.

**Success Criteria**
- [ ] QW-1: The CSV export includes `category`, `container_path` and the latest estimated cost with its date (`export.csv`). Existing columns keep their order, and new columns are appended.
- [ ] QW-2: The container detail page and the dashboard show **total estimated value** (sum of latest estimate × quantity for confirmed items). Child containers roll up into their parent, and the number of unestimated items is shown next to the total.
- [ ] QW-3: The app README setup section reflects the current path, port 1800 and `start.ps1` usage.
- [ ] QW-4: The SQLite file-lock teardown failures in tests are fixed on Windows. The suite runs with only failures that have a written, accepted reason, or none at all.
- [ ] QW-5: Failed cost lookups (outbound attempts) count toward `COST_LOOKUP_MONTHLY_LIMIT`, closing the accepted gap from cost_of_replacement.
- [ ] QW-6: `backup-data.ps1` can copy each snapshot to an off-site destination (configurable path, for example a OneDrive-synced folder or the NAS), and logs whether that copy succeeded. *Interim measure for the owner's install. The off-site copy must be encrypted, using the PD-12 engine if SP-9 has concluded, otherwise an encrypted archive. WS-10 replaces this script.*

**In Scope:** the six items above.
**Out of Scope:** ❌ new report formats (WS-3); ❌ changing which cost provider is used.
**Constraints:** QW-5 must not change any privacy guardrail. QW-6 must never delete the local copy.
**Risks:** QW-4 may show real bugs rather than teardown noise → record it as a finding and escalate, don't mask it.
**Rollback:** each QW is an independent commit.

---

### WS-1 — Where Is It & Is It Still Here (Item Status + Loans)

**Objective:** Let a household find anything it owns, tell whether it is still in the house, and see who it is loaned to.

**Why:** This is the owner's added use case. It turns the inventory from a one-time snapshot into a living record. It is also what a "status" column in the client report needs (WS-3).

**Success Criteria**
- [ ] Every item has a `lifecycle_status` from a fixed set of **ten** values (confirmed by owner, 2026-11-24):

  | Value | Meaning |
  |---|---|
  | `in_home` | In the house at its recorded location (default for existing items) |
  | `loaned` | Lent to someone (an open loan record is required) |
  | `in_repair` | Out for repair or service |
  | `in_vehicle` | Kept in or temporarily in a vehicle |
  | `in_storage_offsite` | In a storage unit or another off-site location |
  | `donated` | Given to a charity or organization |
  | `sold` | Sold |
  | `given_away` | Given to a person |
  | `discarded` | Thrown away or recycled |
  | `missing` | Expected but not found (for example by verify mode) |

- [ ] The existing `status` field (`confirmed`/`likely`, which means AI certainty) stays separate and unchanged.
- [ ] A loan can be recorded with item, borrower name, optional contact, date out, expected return date and notes, and closed with a return date. Returning a loaned item sets status back to `in_home`. Loan history is kept, never overwritten.
- [ ] Items `in_repair` can optionally record where and since when (in notes or a light field, decided in TODO refinement).
- [ ] The dashboard has a **"Lent out"** panel listing open loans, with overdue loans highlighted. It also shows a count of items out of the house (`loaned` + `in_repair` + `in_vehicle` + `in_storage_offsite`).
- [ ] Search results and the QR mobile page show status and loan info (for example "Loaned to Dave since 2026-10-02") next to location.
- [ ] Search can filter by lifecycle status. By default it shows all statuses, with gone items (`donated`/`sold`/`given_away`/`discarded`) visibly marked.
- [ ] Items and containers have a **last verified** date.
- [ ] **Verify mode:** from a container page (or its QR scan), the user ticks items still present. Ticked items get `last_verified` set to today. Unticked items can be bulk-marked `missing`.
- [ ] All status, loan and verification changes are written to `edit_history`.
- [ ] Tests cover all ten statuses, status transitions, loan open/close, overdue calculation and verify mode.

**In Scope:** status field, loans table, Lent-out panel, status in search, QR page and exports, last-verified date, verify mode.
**Out of Scope:** ❌ email/SMS reminders to borrowers; ❌ borrower accounts or logins; 📦 barcode check-in/out → [BL-005](../../backlog/BL-005-barcode-check-in-out.md).
**Constraints:** additive migration only. Status changes never delete items.
**Risks:** confusing `status` (AI certainty) with `lifecycle_status` (physical state) → UI labels the two differently (PD-2).
**Rollback:** revert the commits; the new column has a default and the loans table is standalone.

---

### WS-2 — Insurance-Grade Records *(Coarse)*

**Objective:** Capture the details insurers and adjusters ask for, with photo evidence linked to each item.

**Why:** Summary §3.7 found items link only to a container, not to the photo that shows them, which weakens per-item evidence.

**Success Criteria (goal-level)**
- [ ] Items can store brand, model, serial number, purchase date, purchase price, condition and `owned_by_date` (defaults to the date of the first photo showing the item).
- [ ] Receipt photos and close-up evidence photos can be attached to a specific item. These are stored as working copies (PD-13), with the original's date taken, filename and optional fingerprint recorded.
- [ ] Each item confirmed from a detection keeps a link to the photo it was detected in.
- [ ] Vision can read brand, model and serial from close-up photos as **suggestions** marked "AI-read, verify". They never overwrite fields the user entered without confirmation.
- [ ] Items can be flagged **high-value** (jewelry, electronics, art, firearms, collectibles), with a reminder to take close-up photos.

**Out of Scope:** ❌ integration with insurer systems; 📦 crop regions → [BL-003](../../backlog/BL-003-photo-crop-regions.md); 📦 receipt OCR → [BL-004](../../backlog/BL-004-receipt-ocr.md).
**Constraints:** AI-read fields follow D-002 (confirmation required) and the D-003 validation style.
**Risks:** serial misreads presented as fact → always marked unverified until confirmed.
**Spike:** SP-2 (can the local model read serial/model stickers reliably **from 2,400 px working copies**?).

---

### WS-3 — Client Report *(Coarse; first in line after WS-1)*

**Objective:** Generate a professional report of a household's inventory that the household can hand to an insurer, an executor or family members.

**Why:** It is the most visible proof of value, both for a licensed household and for the optional documentation service (summary §1 and §4.1 Sprint 3).

**Success Criteria (goal-level)**
- [ ] A report is generated locally (HTML, then PDF) for one household, with no cloud rendering service.
- [ ] **Insurance variant:** cover page, household summary, total estimated replacement value by room and by category, per-item rows (thumbnail, quantity, condition, value, source, estimate date), a high-value appendix and a photo evidence appendix.
- [ ] **Downsizing variant:** items grouped by disposition (Keep/Sell/Donate/Gift/Discard) with recipients and a sale-value subtotal. Requires WS-5, so the first version covers lifecycle status only.
- [ ] **Quick-find variant:** a printable item → location index, including lifecycle status.
- [ ] An adjuster-friendly CSV/XLSX export with a stable, documented column layout.
- [ ] Every monetary value is labeled as an estimate, with its source and date. The report carries a "not an appraisal" disclaimer.
- [ ] A 500-item report generates in a reasonable time (target set during refinement).

**Out of Scope:** ❌ e-signature; ❌ emailing the report from the app; 📦 branding/white-labeling → [BL-006](../../backlog/BL-006-report-branding.md).
**Constraints:** report generation must not send inventory data off-device.
**Spike:** SP-3 (choice of PDF generation library on Windows).

---

### WS-4 — Households, Accounts & Security *(Coarse)*

**Objective:** Give each install logins and roles, and let an install hold more than one household inventory. A household can be **transferred** between installs, which is how the optional documentation service hands a finished inventory to a client's licensed copy.

**Why:** Today the app has no authentication, holds one household, and puts the host's LAN address into its QR labels (summary §3.7). The licensing model (PD-9) makes the client the administrator of their own install.

**Success Criteria (goal-level)**
- [ ] **Login** with roles on each install: *admin* (the licensee: manages accounts and settings), *member* (household members: view and edit inventory), *read-only*. Clients edit their own inventory (owner answer §8, Q4).
- [ ] **Households:** every container, item, photo, label, loan and estimate belongs to exactly one household. Isolation is proven by tests showing no query returns another household's data. A licensed install normally has one household; the owner's service install has many.
- [ ] **Household transfer:** export one household (database rows + photos + labels) as a single package and import it into another install with no data loss. This is also the client's own full-data export.
- [ ] **Portable QR labels** that don't depend on the host's current LAN IP (scheme set by PD-4). Labels survive a transfer to the client's install, or can be regenerated in bulk.
- [ ] Backups cover every household on an install, using the WS-10 engine. With per-household files (PD-3), each household can have its own backup repository.

**Out of Scope:** ❌ public SaaS hosting; ❌ self-service signup; ❌ SSO/OAuth providers; 📦 read-only share links → [BL-001](../../backlog/BL-001-read-only-share-links.md).
**Constraints:** stays local-first. Any remote access goes through the household's own network or VPN, never a public cloud.
**Risks:** a data leak between households (owner's service install) → SP-4 and PD-3 must be decided before any code. Labels breaking on transfer → PD-4 covers transfer explicitly.
**Rollback:** existing data goes into a default household, so the single-household behavior can be restored.

---

### WS-5 — Downsizing Workflow *(Coarse)*

**Objective:** Support moving, downsizing and estate work: deciding what happens to each item and who receives it.

**Why:** Downsizing is one of the two markets the side-hustle idea named.

**Success Criteria (goal-level)**
- [ ] Items have a **disposition** (Keep / Sell / Donate / Gift / Discard / Undecided), stored separately from lifecycle status (PD-6).
- [ ] Items can be assigned to a recipient (for example "Grandma's clock → Sarah").
- [ ] **Resale value estimates** (used-market) are stored separately from replacement cost, reusing the cost-lookup pipeline and its privacy rules.
- [ ] Donation summary per recipient organization, for the household's tax records.
- [ ] Packing list per destination (which boxes go where).
- [ ] Carrying out a disposition updates lifecycle status (for example Gift + handed over → `given_away`).

**Out of Scope:** ❌ listing items on marketplaces; ❌ tax advice; 📦 family claiming/voting view → [BL-002](../../backlog/BL-002-family-claiming-view.md).
**Constraints:** the resale lookup obeys all cost_of_replacement decisions, including excluded categories.

---

### WS-6 — Field Efficiency *(Coarse)*

**Objective:** Make documenting a home on site fast and reliable, both for the owner's documentation service and for households capturing their own homes.

**Why:** The full vision model needs a capable GPU machine (summary §3.7). Documenting someone else's home needs a laptop-plus-phone workflow.

**Success Criteria (goal-level)**
- [ ] **Field-capture mode:** photos can be captured and queued without a connection to the machine running the AI, and synced later. Detection runs then, or during the overnight deep scan.
- [ ] A smaller vision model option for laptops, **or** remote inference to a GPU machine over a VPN. Chosen by SP-6 (informed by SP-7).
- [ ] **Room-by-room progress** ("Kitchen: 12 containers, 80% confirmed") and a walkthrough checklist so no room is missed.
- [ ] A finished field session can be handed over as a household transfer package (WS-4).

**Out of Scope:** ❌ offline-first native app; ❌ third-party sync services.
**Spike:** SP-6 (laptop model quality and speed vs remote inference).

---

### WS-7 — Platform Hardening *(Coarse; run alongside)*

**Objective:** Pay down the technical debt in summary §3.7 that the workstreams above don't already cover.

**Success Criteria (goal-level)**
- [ ] Search moves from SQL `LIKE` to SQLite **FTS5**, keeping synonyms, filters and similar-item suggestions. Results for existing test queries are unchanged or better.
- [ ] The `COST_LOOKUP_MONTHLY_LIMIT` setting is read when needed rather than cached at import, and whitespace is stripped from the provider env value (accepted gaps from cost_of_replacement).
- [ ] The detection → item → photo link (WS-2) is backfilled for existing items where it can be done unambiguously.

**Out of Scope:** ❌ switching databases (Postgres etc.).

---

### WS-8 — Business Readiness (Owner-Led, Non-Code)

**Objective:** Record the business preparation the summary recommends, so the software is not finished long before the business can use it.

**Checklist (owner decisions; tracked, not coded)**
- [ ] Decide the offer: license tiers (for example personal / family), annual vs one-time license, optional documentation service, optional setup service (summary §4.2, updated for PD-9).
- [ ] Get professional liability (E&O) insurance, for the documentation service and for software whose output is used in claims.
- [ ] Write an end-user license agreement (EULA) with a limitation-of-liability clause and wording for "estimated replacement cost with cited sources, not an appraisal". Use the same wording in WS-3 reports.
- [ ] Identify an appraiser partner for jewelry, art and antiques.
- [ ] Write a data and privacy statement (data stays on the client's machine; what the optional cost lookup sends).
- [ ] Decide the support model (documentation only, email support, paid support).
- [ ] List referral partners: insurance agents, estate attorneys, senior move managers, realtors, estate-sale companies, assisted-living communities.
- [ ] Positioning statement leading with privacy.

**Out of Scope:** ❌ legal or tax advice from the AI. These items are reminders for the owner, not deliverables an agent can complete. A lawyer should review the EULA.

---

### WS-9 — Licensing & Distribution *(Coarse; added by owner review)*

**Objective:** Make the application something a non-technical household can install, license, run and keep up to date on its own hardware.

**Why:** Owner direction (§8, Q4): clients license the software. Today the app installs through PowerShell scripts, a hand-built Python virtualenv and a separately run llama.cpp server. That works for the owner, not for a client.

**Success Criteria (goal-level)**
- [ ] **Supported hardware is defined and published** (minimum and recommended), based on SP-7. This includes what happens on machines that can't run the default vision model.
- [ ] **Installer:** one download that installs the app, its Python runtime and the local AI runtime and model. It creates a desktop/start-menu shortcut and starts the app at login. No terminal needed.
- [ ] **First-run setup:** create the admin account, name the household, run the WS-10 backup setup (USB drive, password, Recovery Sheet, optional off-site), and run an AI health check with a plain-language result.
- [ ] **License mechanism** (PD-10): works **offline** with no phone-home and no telemetry, for example a signed license file checked locally. The app keeps working read-only (data always accessible and exportable) if a license lapses. Exact rules are set in PD-10.
- [ ] **Updates:** a safe update path that takes an automatic backup before applying migrations, and can be rolled back.
- [ ] **User guide** covering capture, search, loans, reports and backup, written for non-technical households.
- [ ] Owner-specific settings are removed from defaults: hard-coded IPs, the `D:` backup path, the network names in the runbooks.

**Out of Scope:** ❌ app-store distribution; ❌ online license server or account system; ❌ macOS/Linux installers in the first version (⚠️ decided in refinement after SP-7); ❌ building a payment system (use a third-party store if needed).
**Constraints:** licensing never blocks access to a household's own data and never transmits it (privacy constraint in §1).
**Risks:** client hardware can't run local AI → SP-7 determines viability; options include a smaller model, or (only with explicit decision) an opt-in alternative provider. That would need a new decision, since D-001 forbids cloud vision *by default*.
**Spikes:** SP-7 (client hardware viability), SP-8 (packaging approach for Python + llama.cpp on Windows).

---

### WS-10 — Data Protection *(Coarse; full analysis in [DATA_PROTECTION.md](DATA_PROTECTION.md))*

**Objective:** Keep every household's inventory safe and private at the least possible cost. Two media types on the customer's own premises are **required**. An encrypted off-site copy on free or low-cost storage is **encouraged**.

**Why:** Owner direction (§8, item 6). A home inventory is only useful if it survives the fire, flood or theft it was made for. It is also sensitive: a list of valuables and exactly where they are. Today the only protection is the owner's own weekly script (same media type, unencrypted, no off-site copy).

**Success Criteria (goal-level)**
- [ ] **Tier 1 (required):** automatic, encrypted, versioned backups to a USB drive (flash drive minimum, external HDD/SSD recommended). They run after capture sessions and daily, and catch up when the drive is reconnected. Database snapshots are consistent (SQLite online backup + integrity check). Retention follows a policy (for example 7 daily / 4 weekly / 12 monthly).
- [ ] **Tier 2 (encouraged):** an encrypted off-site backup set up from the app to the **customer's own** Google Drive or OneDrive ($0), Backblaze B2 (low cost), or a trusted relative's PC via Syncthing. Data is encrypted before it leaves the computer.
- [ ] **One engine, two repositories:** the same tool (PD-12) handles both tiers, with one password and one restore procedure.
- [ ] **Keys:** the backup password is created at first-run and stored locally (Windows Credential Manager). It is never transmitted. The app produces a printable **Recovery Sheet**, and states plainly that the vendor cannot recover a lost password.
- [ ] **Data Protection status** on the dashboard (🟢/🟡/🔴), with recurring, polite reminders when a backup is overdue or no off-site copy exists.
- [ ] **Restore:** a test restore at setup, a quarterly verify check, and a restore wizard (whole inventory or a chosen snapshot, same or new PC).
- [ ] Backups cover what the app stores: the database and **working copies** (WS-11), about 4.3 GB per 3,000 photos. Original photos are the user's responsibility and are not part of the app's backup.
- [ ] The customer's minimum extra cost is **$0–15** (a USB drive they may already own). The recommended setup is **about $50–70 one-time, $0 ongoing** (see DATA_PROTECTION.md §6).
- [ ] The owner's install is migrated onto WS-10 and replaces `backup-data.ps1`.

**In Scope:** backup engine integration, both tiers, key handling, Recovery Sheet, status and reminders, restore wizard, user-guide chapter.
**Out of Scope:** ❌ vendor-hosted backup storage; ❌ writing custom encryption; ❌ backing up the customer's other files (only inventory data); ❌ forcing an off-site copy.
**Constraints:** every backup copy encrypted (§1); the vendor never holds data or keys (R4); restore must work with the standalone engine even if the app is broken.
**Risks:** customers lose the password → Recovery Sheet plus repeated guidance. Cloud authorization too hard for non-technical users → SP-9 tests it, with Kopia as fallback. Free-tier limits change → a tier change only changes the destination, not the design.
**Spike:** SP-9 (engine licensing, speed, cloud authorization ease, credential storage).
**Rollback:** backups are additional copies and never modify live data. Disabling WS-10 leaves the inventory untouched. Re-enable `backup-data.ps1` for the owner.

---

### WS-11 — User-Owned Originals (Capture Change) *(Coarse; design and workflow diagram in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md))*

**Objective:** Change image capture so the app keeps only reduced **working copies** and never the user's original photos. Users are responsible for their originals and for backing them up.

**Why:** Owner direction (§8, item 7). Today the main capture path ("Take Photo", the in-page camera) leaves the original **only** in the app, because iPhone doesn't save those photos to the camera roll. The app stores full originals (about 5.35 MB each). Working copies are measured at about 1.42 MB, 74% smaller, which makes WS-10's free backup tiers realistic.

**Success Criteria (goal-level)**
- [ ] Every upload path (Library, Quick Photo, import inbox, desktop upload) goes through one **server normalizer**: upright orientation, 2,400 px long edge, JPEG quality 85, GPS removed, date taken and original filename recorded. Optionally a SHA-256 fingerprint of the original is stored.
- [ ] **Only the working copy is saved.** The app reads the uploaded photo, makes the working copy from it, and never saves the full-size upload to disk (not in `data/photos/` or anywhere else). The household's original on their phone or computer is never touched. A test proves the stored file is the working copy.
- [ ] **Customer-facing wording** (screens, user guide, EULA) follows [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) §6. It never says the app "discards" or "deletes" originals, and always says the original stays with the household.
- [ ] **"Choose From Library" is the primary path** on the capture page. The wording tells users to shoot with the Camera app so originals stay in Photos.
- [ ] **In-app camera becomes "Quick Photo"**, with a "Save original to my phone" share-sheet prompt and a plain warning if declined (or it is removed, per SP-10 and PD-14).
- [ ] **Import inbox files are never moved or deleted.** They are marked imported (name + fingerprint) so they aren't imported twice.
- [ ] Detection, deep scan and tiling work unchanged on working copies. Golden-set accuracy (`scripts/vision_eval`) does not drop compared with originals.
- [ ] **Existing photos** stay as they are by default. An optional "Compact existing photos" tool runs only after a verified backup and asks for confirmation (PD-15).
- [ ] The user guide (WS-9) and EULA (WS-8) state that the household is responsible for original photos and their backup.

**In Scope:** normalizer, capture page changes, Quick Photo prompt, inbox behavior, fingerprint, compaction tool, tests, documentation wording.
**Out of Scope:** ❌ backing up users' originals; ❌ managing the user's phone photo library or iCloud; ❌ a native app to write to the camera roll.
**Constraints:** additive changes only. Existing photo files are never altered without the PD-15 confirmation. AI detection quality must not drop.
**Risks:** users lose originals taken with Quick Photo → prompt, warning, Library-first design. Serial reading worse at 2,400 px → SP-2/SP-10 measure it, and the working-copy size can be raised if needed (it's a setting).
**Spike:** SP-10 (iPhone Safari behavior: library resolution and HEIC handling, share-sheet save, in-browser resize, working-copy size).
**Rollback:** set the normalizer to "store original" (a setting kept for rollback). Photos uploaded while the change was active exist in the app only as working copies; their full-size versions are still with the household. PD-15 compaction is opt-in because it replaces full-size files the app already holds.

---

## 4. TRACEABILITY & SCOPE CLASSIFICATION

Every suggestion in the summary, plus owner-review additions, mapped to where it lives.

| Item | Source | Classification | Goal |
|---|---|---|---|
| CSV export missing category, cost and path | Summary §3.7, §4.3 #1 | ✅ | WS-0 QW-1 |
| Total estimated value | Summary §3.7, §4.3 #2 | ✅ | WS-0 QW-2 |
| README setup section stale | Summary §3.7, §4.3 #3 | ✅ | WS-0 QW-3 |
| Windows SQLite test teardown | Summary §3.6, §4.3 #4 | ✅ | WS-0 QW-4 |
| Cost guard counts successes, not attempts | Summary §3.7, §4.3 #5 | ✅ | WS-0 QW-5 |
| Backups local only / off-site copy | Summary §3.7, §4.3 #6 | ✅ | WS-0 QW-6 |
| Lifecycle status (8 suggested + `in_repair`, `in_vehicle`) | Summary §4.1 S1; owner §8 Q3 | ✅ | WS-1 |
| Loans table + Lent-out panel | Summary §4.1 S1 | ✅ | WS-1 |
| Last seen / verify mode | Summary §4.1 S1 | ✅ | WS-1 |
| Status in search | Summary §4.1 S1 | ✅ | WS-1 |
| Barcode check-in/out | GOALS rev 1 WS-1 | 📦 | BL-005 |
| Brand/model/serial/purchase/condition/owned_by_date | Summary §4.1 S2 | ✅ | WS-2 |
| Receipt and close-up photos per item | Summary §4.1 S2 | ✅ | WS-2 |
| Item ↔ photo link | Summary §3.7, §4.1 S2 | ✅ | WS-2 |
| Crop region per item | Summary §4.1 S2 | 📦 | BL-003 |
| Receipt OCR | GOALS rev 1 WS-2 | 📦 | BL-004 |
| AI-read brand/model/serial | Summary §4.1 S2 | ✅ | WS-2 |
| High-value flag | Summary §4.1 S2 | ✅ | WS-2 |
| PDF/HTML report: Insurance / Downsizing / Quick-find | Summary §4.1 S3 | ✅ | WS-3 |
| Adjuster CSV/XLSX | Summary §4.1 S3 | ✅ | WS-3 |
| Report branding / white-label | GOALS rev 1 WS-3 | 📦 | BL-006 |
| Households/workspaces | Summary §3.7, §4.1 S4 | ✅ | WS-4 |
| Login + roles (clients edit their own data) | Summary §3.7, §4.1 S4; owner §8 Q4 | ✅ | WS-4 |
| Read-only share link | Summary §4.1 S4 | 📦 | BL-001 |
| Portable QR labels | Summary §3.7, §4.1 S4 | ✅ | WS-4 / PD-4 |
| Encrypted backup + hand-over export | Summary §4.1 S4 | ✅ | Hand-over → WS-4 (household transfer); encrypted backup → WS-10 |
| Disposition + recipient | Summary §4.1 S5 | ✅ | WS-5 |
| Family claiming/voting view | Summary §4.1 S5 | 📦 | BL-002 |
| Resale value estimates | Summary §4.1 S5 | ✅ | WS-5 |
| Donation summaries, packing lists | Summary §4.1 S5 | ✅ | WS-5 |
| Field-capture offline queue | Summary §4.1 S6 | ✅ | WS-6 |
| Small model / remote inference | Summary §3.7, §4.1 S6 | ✅ | WS-6 / SP-6 |
| Room progress + walkthrough checklist | Summary §4.1 S6 | ✅ | WS-6 |
| Search `LIKE` → FTS5 | Summary §3.7 | ✅ | WS-7 |
| Cost limit cached at import; env whitespace | Accepted gaps, cost_of_replacement | ✅ | WS-7 |
| Packages, E&O, disclaimer, appraiser, retention, partners, positioning | Summary §4.2 | ✅ (owner-led) | WS-8 |
| Client licenses the software | Owner §8 Q4 | ✅ (scope change) | WS-9 / PD-9 |
| Installer, first-run, offline license, updates, user guide | Follows from Q4 | ✅ | WS-9 |
| Local backup on two media types (required) | Owner §8 item 6; summary §3.7 "backups local only" | ✅ (scope change) | WS-10 Tier 1 / PD-11 |
| Encrypted off-site backup, free or low cost (encouraged) | Owner §8 item 6; summary §4.1 S4 | ✅ (scope change) | WS-10 Tier 2 / PD-11 |
| Backup engine choice | Follows from item 6 | ✅ | WS-10 / PD-12 / SP-9 |
| App keeps working copies, not originals | Owner §8 item 7 | ✅ (scope change) | WS-11 / PD-13 |
| Library-first capture, Quick Photo save prompt, inbox left untouched | Follows from item 7 | ✅ | WS-11 / PD-14 / SP-10 |
| Handling of already-stored originals | Follows from item 7 | ✅ | WS-11 / PD-15 |

---

## 5. SEQUENCING NOTES FOR TODO.md

- **Phase 0 (Discovery):** write CONTEXT.md, seed DECISIONS.md with §6 and the §8 scope change. Run spikes SP-1 and SP-3 (needed soonest) and **SP-7** (client hardware: it decides whether licensing is viable and affects WS-4/6/9). Leave SP-2, SP-4, SP-6 and SP-8 until their workstream's phase is refined.
- **Phases:** 1 = WS-0, 2 = WS-1, 3 = WS-11, 4 = WS-10, 5 = WS-3 (first version), then WS-2, WS-4, WS-5, WS-6, WS-9, each refined at the previous phase boundary. Run **SP-10** before Phase 3 is refined, and **SP-9** before Phase 4 is refined (or before QW-6, if its encrypted off-site copy should use the PD-12 engine).
- **No deadline:** with no clients and no target date, quality and data safety come before speed. Don't skip spikes or tests to move faster.
- **Check-ins** every 10 tasks and at each phase boundary should show working output: a screenshot of the Lent-out panel, a generated sample PDF, and so on.
- **Every task that runs a migration** includes "back up `data/` first" in its steps.

---

## 6. PROPOSED DECISIONS (seed for DECISIONS.md, all `PROPOSED`)

| ID | Question | Leaning (to validate) | Blocks |
|---|---|---|---|
| PD-1 | May new columns be added to `box_items`? (cost_of_replacement deliberately avoided it.) | Yes, additive columns with defaults, as migration 003 did. Side data with history (loans, evidence photos) gets its own tables. | WS-1, WS-2 |
| PD-2 | How do lifecycle status and AI-certainty `status` coexist? | Separate column `lifecycle_status` with the ten values in WS-1; the UI calls the old field "AI certainty" | WS-1 |
| PD-3 | Household isolation model: `household_id` on every table vs one database file per household | Undecided; decided by SP-4. One file per household makes transfer and hand-over trivial, which matters more now that transfer is a core flow. | WS-4 |
| PD-4 | QR label URL scheme that survives LAN IP changes **and household transfer** | A stable local host name + `/q/{public_id}`, with `public_id` unique across installs (for example a UUID) and a bulk regenerate tool | WS-4 |
| PD-5 | *Withdrawn 2026-11-24.* Share links moved to the backlog ([BL-001](../../backlog/BL-001-read-only-share-links.md)). | — | — |
| PD-6 | Disposition vs lifecycle status | Separate fields: disposition is a plan ("Gift to Sarah"), lifecycle is a fact ("given_away") | WS-5 |
| PD-7 | Report rendering library | Decided by SP-3 (candidates: HTML + browser print, WeasyPrint, ReportLab) | WS-3 |
| PD-8 | Auth mechanism | Simple local accounts with hashed passwords and session cookies; no external identity provider | WS-4 |
| PD-9 | **Business model** | Licensed software that households run themselves (primary), plus an optional documentation service with hand-over to the client's install. No hosted SaaS. | WS-4, WS-8, WS-9 |
| PD-10 | License mechanism | Offline, signed license file checked locally; no phone-home or telemetry; read-only fallback on lapse, never data lock-out | WS-9 |
| PD-11 | **Data protection strategy** (least expensive safe approach) | 3-2-1: (a) **required** encrypted, versioned backup to a USB drive as the second media type ($0–15 minimum); (b) **encouraged** encrypted off-site copy to the customer's own Google Drive/OneDrive ($0) or Backblaze B2 (low cost); customer-held keys + Recovery Sheet. See [DATA_PROTECTION.md](DATA_PROTECTION.md). | WS-10, QW-6 |
| PD-12 | Backup engine | **restic + rclone**, bundled (permissive licenses, single binaries, scriptable); Kopia as fallback; no custom crypto. Decided by SP-9. | WS-10 |
| PD-13 | **Store working copies, not originals** | 2,400 px, JPEG 85, upright, GPS removed; date taken + filename + optional fingerprint recorded; the app never saves the full-size upload, and the household's original is untouched. See [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md). | WS-11, WS-10 sizing |
| PD-14 | Capture paths | Library-first; in-app camera kept as "Quick Photo" with a save-to-phone prompt (or removed, after SP-10); inbox files never moved or deleted; optional in-browser resize | WS-11 |
| PD-15 | Already-stored originals | Leave as they are by default; optional one-time compaction only after a verified backup and with confirmation | WS-11 |

---

## 7. SPIKES (high-risk assumptions to test before building)

| ID | Question | Time-box | Before |
|---|---|---|---|
| SP-1 | Can the item-photo link be recovered for existing items from `detection_suggestions.photo_id`, and how often is it ambiguous? | 1 h | WS-2 / WS-7 backfill |
| SP-2 | Does the local vision model read brand, model and serial stickers accurately enough to be useful as suggestions? (Use the `scripts/vision_eval` harness.) | 2 h | WS-2 |
| SP-3 | Which PDF approach renders photos and tables reliably on this Windows host with no cloud dependency? | 2 h | WS-3 |
| SP-4 | Per-household database file vs `household_id` column: effort, isolation test strategy, effect on transfer and backup | 2 h | WS-4 |
| SP-6 | Detection quality and speed of a laptop-sized model vs remote inference to a GPU machine over VPN | 2 h | WS-6 |
| SP-7 | **Client hardware viability:** what is the smallest local vision model (and the minimum CPU/GPU/RAM) that still gives acceptable detection on the golden set? Can a typical household PC with no dedicated GPU run it at a tolerable speed? | 3 h | Phase 0; informs WS-4, WS-6, WS-9 |
| SP-8 | Packaging: how to ship Python app + llama.cpp + model as one Windows installer (for example embedded Python + Inno Setup, or PyInstaller), and what size the download is | 2 h | WS-9 |
| SP-9 | **Backup engine:** confirm restic/rclone licenses allow bundling; time a 10 GB first and incremental backup to USB and Google Drive from Python on Windows; judge how hard cloud authorization is for non-technical users (else Kopia); verify credential storage under the app's account (including SYSTEM); re-check free-tier prices. Checklist in [DATA_PROTECTION.md](DATA_PROTECTION.md) §8. | 3 h | WS-10 (and QW-6) |
| SP-10 | **iPhone capture behavior:** Library upload resolution and HEIC handling; share-sheet "Save Image" after in-page capture; in-browser resize orientation; working-copy size on 20+ photos; serial readability at 2,400 px (with SP-2). Checklist in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) §5. | 2 h | WS-11 |

---

## 8. OWNER REVIEW RECORD (2026-11-24)

| # | Question | Owner answer | Applied as |
|---|---|---|---|
| 1 | Is the recommended order right? | "The order is fine. No immediate clients." | §2 order confirmed; WS-9 appended last |
| 2 | Target date for a first paying client? | "No target date." | §1 Business Model; §5 "no deadline" note |
| 3 | Are the eight lifecycle statuses right? | Add `in_repair` and `in_vehicle`. | WS-1 now has ten statuses; PD-2 updated |
| 4 | Should clients edit their own inventory, or only view it? | "I thought that the client would license this software?" | New business model: licensed, self-run software, so clients edit their own data. Added WS-9, PD-9, PD-10, SP-7, SP-8; WS-4 reframed around accounts, households and transfer; WS-8 updated (EULA, license tiers, support). **Needs owner confirmation via PD-9.** |
| 5 | Keep ⚠️ MAYBE items or move them to the backlog? | Move them to the backlog, and create a space for it. | Created [docs/AI_Planning/backlog/](../../backlog/README.md); BL-001…BL-006; PD-5 withdrawn |
| 6 | *(Owner direction, after the review)* | "Decide on the least expensive way to keep the user data safe and secure, first on their own computer, on two media types, and then encrypted and backed up somewhere free or low cost as an encouraged option to the customer." | Added WS-10, PD-11, PD-12, SP-9, and [DATA_PROTECTION.md](DATA_PROTECTION.md). QW-6 and WS-4/WS-9 aligned. **WS-10 placement after WS-1 needs owner confirmation.** |
| 7 | *(Owner direction, after the review)* | "Change how image capture works, so that we do not keep their originals. Users should be responsible for their originals and their backups of their originals." | Added WS-11, PD-13…PD-15, SP-10, and [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md) with the workflow diagram. Measured: working copies average 1.42 MB vs 5.35 MB originals (−74%). WS-2, WS-10 and BL-003 aligned. **WS-11 placement (before WS-10) needs owner confirmation.** |
| 8 | *(Owner decision, 2026-11-26)* | Can backup encryption be optional for the user? → "Skip the optional encryption for a future release and only if there is demand." | Encryption stays mandatory for every backup copy (PD-11 unchanged). Optional local-backup encryption parked as [BL-007](../../backlog/BL-007-optional-local-backup-encryption.md); DATA_PROTECTION.md §1 notes it. |

---

## Next Steps (framework)
1. Owner confirms the licensing direction (PD-9) and the WS-11/WS-10 placement, and approves this revision → **Status: APPROVED**.
2. Create `CONTEXT.md` (current system from summary §3; target state per workstream).
3. Create `DECISIONS.md` seeded with PD-1…PD-15 (PD-11/12 from DATA_PROTECTION.md, PD-13…15 from USER_OWNED_ORIGINALS.md), the inherited D-numbers, and a scope-change decision for the §8 answers.
4. Create `TODO.md`: Phase 0 (including SP-7, SP-9 and SP-10), then full detail for WS-0 and WS-1 only.
5. Create `SPRINT_STORY_summary_suggestions.md` from TODO.md.
