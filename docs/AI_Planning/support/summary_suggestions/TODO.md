# TODO — summary_suggestions

> ⚠️ **AI AGENT INSTRUCTIONS**
> This is the **single source of truth** for task progress.
>
> **Before starting any work:** read [CONTEXT.md](CONTEXT.md), [DECISIONS.md](DECISIONS.md) and this file. Find the **first** task that isn't ✅, mark it 🔄, meet **all** its acceptance criteria, then mark it ✅ and add a line to the completion log.
>
> **Rules**
> - One task at a time. Don't skip, reorder or add tasks without owner approval.
> - **Back up `outputs/home-inventory-app/data/` before any migration, branch switch, checkout or reset** (incident 2026-11-23). Tasks that need it say so.
> - Re-read this file after each task. After every **10** completed tasks, stop and report to the owner.
> - If a task shows an ACCEPTED decision can't work, **stop**: mark it INVALIDATED in DECISIONS.md, mark dependent tasks ⛔, and escalate. Don't build a workaround.
> - Never commit secrets. The age **private key** and the Recovery Sheet are never committed.

Pillar 4 of GOAL → CONTEXT → DECISIONS → TODO. Rolling wave: Phases 0–2 are in full detail. Later phases are coarse and get refined at the end of the phase before them.

- **Status:** **APPROVED** by owner on 2026-11-26.
- **Created:** 2026-11-26.
- Paths are relative to `outputs/home-inventory-app/` unless they start with the repository root.

---

## Status Key

| Symbol | Meaning |
|---|---|
| ⬜ | Not started |
| 🔄 | In progress (only one at a time) |
| ✅ | Done, all criteria verified |
| ⛔ | Blocked (blocker noted in the task) |
| 🚫 | Cancelled (reason noted) |
| ⏸️ | Paused (reason noted) |

## Progress

| Phase | Name | Tasks | Done |
|---|---|---|---|
| 0 | Discovery, data safety, spikes | 7 | 5 (2 paused) |
| 1 | WS-0 Quick wins (QW-1…QW-5) | 5 | 4 (1 paused) |
| 2 | WS-1 Status + loans | 10 | 9 (1 paused) |
| 3–11 | Later workstreams | coarse | — |
| **Total (detailed)** | | **22** | **18 (82%), 4 paused** |

**Next milestone:** owner actions in [BL-008](../../backlog/BL-008-owner-actions-pending.md) (move the backup key off the PC, restart the app). Paused tasks (QW-4, SP-3, SP-7, 2.9) wait for the owner's go-ahead on testing. Then refine Phase 3 (WS-11) after SP-10.

> **2026-11-26 owner direction:** "Do what you can do with what you have. If you are waiting on me, then put it on backlog. Skip the testing for now. Finish the work!" Test-related acceptance criteria below were **not** run unless marked; the paused tasks hold them.

---

## PHASE 0 — Discovery, Data Safety, Spikes

**Purpose:** finish the planning documents, protect the owner's live data off-site, and answer the riskiest questions before code depends on them.
**Dependencies:** GOALS.md approved (✅ 2026-11-26).
**Deliverable:** CONTEXT and DECISIONS approved; an encrypted off-site backup running; SP-1, SP-3 and SP-7 answered in DECISIONS.md.

> **Order note.** QW-6 belongs to WS-0, but it runs here, before the spikes, because the owner's data has no off-site or encrypted copy (SC-6, PD-16). It touches only the backup script, never app code or data.

### 0.1 ✅ Write CONTEXT.md
- [x] Current system verified against code, live DB (read-only) and a test run. Approved 2026-11-26.

### 0.2 ✅ Write DECISIONS.md
- [x] PD-1…PD-17, inherited decisions, SC-1…SC-6. Approved 2026-11-26.

### 0.3 ✅ QW-6 — Encrypted off-site copy of each snapshot (age → OneDrive)
**Purpose:** a second location for the owner's data that survives fire or theft at home, readable only with a key kept off the PC. Implements PD-16.
**Files:** repo root `backup-data.ps1`, `.gitignore`; new repo root `backup-offsite.recipient` (public key only).

**Steps**
1. Generate the key pair with `age-keygen -o <USB drive>\home-inventory-backup.agekey`. **The owner does this step, or watches it**: the private key goes straight to a USB stick, never into the repo or OneDrive.
2. Save the public key (`age1…`, printed by `age-keygen`) in `backup-offsite.recipient` at the repo root. Add `*.agekey` to `.gitignore`.
3. Owner prints a **Recovery Sheet**: the private key, where backups are (`D:\HomeInventoryBackups`, OneDrive `HomeInventoryBackups`), and the restore command. Stored with insurance papers. A second copy of the key goes somewhere safe away from home.
4. Extend `backup-data.ps1`:
   - New parameters: `-OffsiteDestination` (default `"$env:OneDrive\HomeInventoryBackups"`), `-OffsiteKeep` (default 3), `-AgePath` (default: resolve `age.exe` from PATH, else the winget links folder; fail clearly if not found), `-RecipientFile` (default `backup-offsite.recipient` next to the script).
   - After a **new** local snapshot is created: `tar -cf` the snapshot into a temp file in the local backup folder, then `age -R <RecipientFile> -o <dest>\<snapshot>.tar.age.partial <tar>`, then rename to `.tar.age` (so OneDrive never uploads a half-written file), then delete the temp tar.
   - **Don't pipe binary data through a PowerShell pipeline** (Windows PowerShell 5.1 corrupts it). Use files, as above.
   - If the run is skipped (no changes) but the newest snapshot has no `.tar.age` in OneDrive, create it (catch-up).
   - Keep the newest `-OffsiteKeep` `*.tar.age` files in the off-site folder; delete older ones **only from the off-site folder**.
   - Log `OFFSITE OK <file> <size>` or `OFFSITE FAILED <reason>`. An off-site failure **never** removes or changes the local snapshot. It makes the script exit with code 2 so the scheduled task shows a failure.
   - Update the header comment: what the off-site step does, and the restore command.
5. Check which account runs the "HomeInventory Data Backup" scheduled task. It must be the Windows account that owns the OneDrive folder (`$env:OneDrive` points to the `cavea` profile on this PC) and can find `age.exe`. Change the task's account, or `-AgePath`, if needed (owner approves any task change).

**Acceptance criteria**
- [ ] A manual run creates a new local snapshot **and** one `<snapshot>.tar.age` in the OneDrive `HomeInventoryBackups` folder; the log shows `OFFSITE OK`.
- [ ] The file is visible on onedrive.com (owner confirms).
- [ ] **Restore test:** in a clean temp folder, `age -d -i <key> <file>.tar.age > snap.tar`, `tar -xf snap.tar`; `PRAGMA integrity_check` on the restored DB returns `ok`; container and item counts match the log line; photo count matches `data/photos/`.
- [ ] The file can't be opened without the private key (`age -d` without `-i` fails; the file isn't a readable tar).
- [ ] Running again with no changes logs `SKIPPED` and creates no new off-site file. With `-OffsiteKeep 1` on a test destination, older `.tar.age` files are pruned and **no local snapshot is touched**.
- [ ] With the off-site folder made unwritable (test destination), the local snapshot still completes, the log shows `OFFSITE FAILED`, exit code is 2.
- [ ] A scheduled (not manual) run succeeds under the task's real account.
- [ ] `git status` shows no `*.agekey` file; only the public key is committed.
- [ ] PD-16 assumptions 1–4 marked ✅ or ❌ in DECISIONS.md.

### 0.4 ✅ SP-1 — Can existing items be linked to their photo? (1 h)
**Purpose:** decides whether WS-2/WS-7 can backfill the item → photo link (CONTEXT.md §4 Scenario 11).
**Method:** read-only queries on a **copy** of the live DB. For each `box_items` row, find `detection_suggestions` rows with `status='confirmed'` in the same box with a matching `normalized_name` / `item_name`. Count: exactly one photo / several photos / none.

**Acceptance criteria**
- [ ] Counts reported (unambiguous / ambiguous / no match) for the live data.
- [ ] Findings and a recommended backfill rule recorded in DECISIONS.md §4 (validation log).
- [ ] Live `data/` not opened for writing.

### 0.5 ⏸️ SP-3 — Which local PDF approach works on this PC? (2 h)
**Purpose:** decides PD-7 before WS-3.
**Method:** render the same sample (cover page, a 100-row table, 50 photo thumbnails from `test-data` or generated images) with (a) HTML + headless Edge/Chrome print-to-PDF, (b) WeasyPrint, (c) ReportLab. No cloud service.

**Acceptance criteria**
- [ ] For each: install effort on Windows (extra native libraries?), render time, output quality, license, and whether it can ship in an installer (WS-9).
- [ ] One approach recommended; PD-7 set to ACCEPTED (with owner approval) or left PROPOSED with the reason.
- [ ] Sample PDFs kept outside the repo, or in `work/` if the owner wants them.

### 0.6 ⏸️ SP-7 — Can a typical household PC run the vision model? (3 h)
**Purpose:** tests PD-9 assumption 1, the biggest risk to the licensing model.
**Method:** using `scripts/vision_eval/` and its golden set, measure detection quality and time per photo for (a) the current Bonsai 27B, (b) at least two smaller vision models (for example a 7–8B and a 2–4B), run **CPU-only** and with whatever GPU is available. Record RAM and VRAM use.

**Acceptance criteria**
- [ ] A table: model, hardware mode, golden-set score, seconds per photo, peak RAM/VRAM.
- [ ] A stated minimum and recommended hardware, or a finding that CPU-only isn't usable.
- [ ] PD-9 assumption 1 marked ✅ or ❌. If ❌: PD-9 flagged and escalated to the owner (Decision Validation Loop) before WS-4 or WS-9 are refined.
- [ ] No change to the app's default model.

### 0.7 ✅ Phase 0 check-in
- [ ] Owner sees: the restored backup from 0.3, and the spike results.
- [ ] Retro notes added to the completion log. Phase 1 tasks adjusted if the spikes changed anything.

---

## PHASE 1 — WS-0 Quick Wins (QW-1…QW-5)

**Purpose:** small, high-value fixes from the review.
**Dependencies:** Phase 0.
**Deliverable:** green test suite, accurate README, better CSV, value totals, honest cost-lookup counting.

> **Order note.** QW-4 (tests) goes first so every later change is checked against a green suite.

### 1.1 ⏸️ QW-4 — Make the test suite pass on Windows
**Purpose:** a trustworthy baseline (CONTEXT.md §4 Scenario 7). Implements PD-17.
**Files:** `tests/*.py`, possibly a new `tests/fakes.py`.

**Acceptance criteria**
- [ ] A **fake LLM vision provider** for tests returns fixed detections and is accepted by `save_photos_and_detect()`'s LLM check. No test-only switch is added to app code (PD-17).
- [ ] The 3 tests that expected suggestions from the heuristic provider use the fake provider and pass.
- [ ] SQLite file-lock errors fixed by closing every connection and client, or using a fresh temp DB per test. No `PermissionError` on Windows.
- [ ] Full suite: **57+ pass, 0 fail** (or a failure with a written, owner-accepted reason in the completion log).
- [ ] Tests still never touch `data/`.

### 1.2 ✅ QW-3 — Fix the README setup section
**Files:** `README.md` (app), repository root README if it repeats setup.

**Acceptance criteria**
- [ ] Port 1800, the current path, `start.ps1` / `stop.ps1` usage, and the Bonsai `llama-server` requirement are correct.
- [ ] No remaining mention of port 8000 or the old path.
- [ ] Mentions `backup-data.ps1` and where the restore steps are (no key material).

### 1.3 ✅ QW-1 — Add category, container path and latest estimate to the CSV
**Files:** `app/main.py` (`export_csv`), `app/repository.py` or `services/search.py` (data), tests.

**Acceptance criteria**
- [ ] Existing 11 columns keep their names and order. New columns are **appended**: `category`, `container_path` (for example `Garage > Shelf 2 > Box 14`), `estimated_cost_usd` (latest), `estimate_date`.
- [ ] Items without an estimate have empty cost cells (not 0).
- [ ] Nested containers produce the full path; a top-level container produces its own name.
- [ ] Test covers: column order, a nested path, an item with and without an estimate.

### 1.4 ✅ QW-2 — Show total estimated value on container pages and the dashboard
**Files:** `app/repository.py`, `app/main.py`, `templates/container_detail.html`, `templates/dashboard.html`, tests.

**Acceptance criteria**
- [ ] Total = sum of (latest estimate × quantity) for **confirmed** items. Child containers roll up into their parents.
- [ ] The number of items **without** an estimate is shown next to the total ("$1,240 estimated, 12 items not estimated").
- [ ] Dashboard shows the whole-house total and the same count.
- [ ] Labeled as an estimate.
- [ ] Tests cover rollup through two levels of nesting and the unestimated count.

### 1.5 ✅ QW-5 — Count failed cost lookups toward the monthly limit
**Files:** `app/services/cost_lookup.py`, maybe a migration if attempts need their own table (back up `data/` first if so), tests.

**Acceptance criteria**
- [ ] Every outbound search **attempt** counts toward `COST_LOOKUP_MONTHLY_LIMIT`, whether it succeeds or fails.
- [ ] Privacy guardrails unchanged (CR-D-001…D-007); excluded categories still make no network call and aren't counted.
- [ ] Tests: a failed lookup increments the count; the limit refuses the next attempt; a new month resets.
- [ ] If a migration was added: `data/` backed up first, migration is additive, applies cleanly to a copy of the live DB.

---

## PHASE 2 — WS-1 Where Is It & Is It Still Here (Status + Loans)

**Purpose:** a living record: where each thing is, whether it's still in the house, who has it. GOALS.md WS-1.
**Dependencies:** Phase 1 (green suite, CSV columns from QW-1). Decisions PD-1, PD-2 (ACCEPTED).
**Deliverable:** lifecycle status, loans, Lent-out panel, status in search/QR/exports, last verified, verify mode.

**Design settled in this refinement** (from GOALS.md WS-1, PD-1, PD-2):
- `box_items.lifecycle_status` (ten values, default `in_home`), `box_items.status_changed_at`, `box_items.status_note` (covers "in repair at Joe's since…"), `box_items.last_verified_at`, `boxes.last_verified_at`.
- New `loans` table: `id, box_item_id → box_items, borrower_name, borrower_contact, loaned_at, due_at, returned_at, notes, created_at`. Open loan = `returned_at IS NULL`. At most one open loan per item.
- `loaned` is set **only** by opening a loan, and left **only** by returning it (or by another status change that closes the loan with a note). This keeps status and loans consistent.

### 2.1 ✅ Migration `009_lifecycle_and_loans.sql` (008 went to QW-5)
**Acceptance criteria**
- [ ] **`data/` backed up first** (copy recorded in the completion log).
- [ ] Adds the columns above with defaults (`lifecycle_status` default `'in_home'`), the `loans` table, and an index for open loans.
- [ ] Additive only: no existing column dropped, renamed or retyped.
- [ ] Applies cleanly to a **copy** of the live DB; all 56 existing items read as `in_home`; existing tests pass.

### 2.2 ✅ Repository functions for status, loans and verification
**Files:** `app/repository.py`.
**Acceptance criteria**
- [ ] `set_lifecycle_status(conn, item_id, status, note)` validates the ten values, refuses `loaned` (use loans), sets `status_changed_at`, writes `edit_history`.
- [ ] `open_loan(...)` refuses if an open loan exists or the item is gone (`donated`/`sold`/`given_away`/`discarded`); sets `loaned`; writes history.
- [ ] `return_loan(conn, loan_id, returned_at)` closes the loan, sets `in_home`, writes history. Loan rows are never deleted or overwritten.
- [ ] `list_open_loans(conn)` returns loans with an `overdue` flag (`due_at` before today).
- [ ] `verify_container(conn, box_id, present_item_ids, mark_missing)` sets `last_verified_at` on ticked items and the container, and optionally marks unticked items `missing`.
- [ ] `box_items.status` (AI certainty) is never touched by any of these.

### 2.3 ✅ API endpoints
**Files:** `app/main.py`.
**Acceptance criteria**
- [ ] `PATCH /api/box-items/{id}/lifecycle`, `POST /api/box-items/{id}/loans`, `POST /api/loans/{id}/return`, `GET /api/loans?open=true`, `POST /api/boxes/{id}/verify`.
- [ ] Invalid status, double loan, or returning a closed loan → 400 with a clear message.
- [ ] Pydantic request models; responses include the updated item or loan.

### 2.4 ✅ Item status and loan UI on the container page
**Files:** `templates/container_detail.html`, `app/static/app.js`, `capture.css` as needed.
**Acceptance criteria**
- [ ] Each item shows **Status** (lifecycle) and, separately labeled, **AI certainty** (PD-2).
- [ ] Change status (with optional note); "Lend" form (borrower, contact, due date, notes); "Returned" button on loaned items.
- [ ] Gone items are visibly marked (muted, with the status).
- [ ] Works on iPhone Safari at phone width.

### 2.5 ✅ Dashboard "Lent out" panel and out-of-house count
**Acceptance criteria**
- [ ] Lists open loans (item, borrower, since, due), overdue ones highlighted.
- [ ] Shows the count of items out of the house (`loaned` + `in_repair` + `in_vehicle` + `in_storage_offsite`).
- [ ] Empty state when nothing is lent out.

### 2.6 ✅ Status in search and on the QR page
**Files:** `app/services/search.py`, `templates/search.html`, QR public page template.
**Acceptance criteria**
- [ ] Search can filter by lifecycle status. Default shows all, with gone items marked.
- [ ] Results and the QR page show status and loan info next to location ("Loaned to Dave since 2026-10-02").
- [ ] Existing search tests still pass.

### 2.7 ✅ Status in exports
**Acceptance criteria**
- [ ] CSV appends `lifecycle_status`, `status_note`, `last_verified_at`, and open loan borrower/due columns **after** the QW-1 columns.
- [ ] `export.json` includes the same fields and loan history per item.
- [ ] Test covers the column order.

### 2.8 ✅ Verify mode
**Acceptance criteria**
- [ ] From a container page (and from its QR page), the user ticks items still present and saves.
- [ ] Ticked items and the container get today's `last_verified_at`. Unticked items can be bulk-marked `missing` with a confirmation.
- [ ] "Last verified" date shown on items and containers.

### 2.9 ⏸️ Tests for WS-1
**Acceptance criteria**
- [ ] All ten statuses settable (except `loaned` directly), each writing `edit_history`.
- [ ] Loan open → return → history kept; double loan refused; overdue flag correct.
- [ ] Verify mode sets dates and marks missing.
- [ ] `status` (AI certainty) unchanged by every WS-1 action.
- [ ] Full suite green.

### 2.10 ✅ Phase 2 check-in and docs
**Acceptance criteria**
- [ ] README describes statuses, loans and verify mode.
- [ ] GOALS.md WS-1 success criteria checked.
- [ ] Owner sees a working demo: a screenshot of the Lent-out panel and a QR page showing a loan.
- [ ] Retro notes in the completion log. Phase 3 (WS-11) refined in this file with the owner, **after SP-10 has run**.

---

## PHASES 3–11 — Coarse (refined at the end of the phase before each)

| Phase | Workstream | Run first | Deliverable (goal level) | Decisions |
|---|---|---|---|---|
| 3 | **WS-11** User-owned originals | **SP-10** (iPhone capture, 2 h) | One normalizer for every upload path; only 2,400 px working copies saved; inbox files never moved; Library-first capture; Quick Photo prompt; optional compaction tool | PD-13, PD-14, PD-15 |
| 4 | **WS-10** Data protection | **SP-9** (backup engine, 3 h) | In-app encrypted backup to USB + optional off-site (customer's choice), Recovery Sheet, status on dashboard, restore wizard; owner moves off `backup-data.ps1` and the QW-6 age copy | PD-11, PD-12 |
| 5 | **WS-3** Client report (first version) | — (SP-3 done in Phase 0) | Local HTML → PDF: insurance and quick-find variants; adjuster CSV/XLSX | PD-7 |
| 6 | **WS-2** Insurance-grade records | **SP-2** (sticker reading, 2 h) | Brand/model/serial/purchase/condition fields; item → photo link (+ backfill per SP-1); evidence photos; AI-read suggestions | PD-1 |
| 7 | **WS-4** Households, accounts, security | **SP-4** (isolation model, 2 h) | Login and roles; households; transfer package; portable QR labels | PD-3, PD-4, PD-8 |
| 8 | **WS-5** Downsizing | — | Disposition, recipients, resale estimates, donation summary, packing lists | PD-6 |
| 9 | **WS-6** Field efficiency | **SP-6** (laptop vs remote inference, 2 h) | Offline capture queue; smaller model or remote inference; room progress | — |
| 10 | **WS-9** Licensing & distribution | **SP-8** (packaging, 2 h) | Installer, first-run, offline license, safe updates, user guide | PD-9, PD-10 |
| — | **WS-7** Platform hardening | — | FTS5 search, config fixes, photo-link backfill. Tasks are slotted into phases as needed | — |
| — | **WS-8** Business readiness | — | Owner checklist (tiers, E&O, EULA, appraiser, privacy statement, support, referrals). Not agent tasks | PD-9 |

---

## Check-In Cadence

- **After 0.3 (QW-6):** owner sees the off-site file on onedrive.com and the restore test result.
- **0.7 Phase 0 check-in:** spike results; adjust Phase 1 if needed.
- **After 1.5:** green suite, new CSV, value totals (screenshot).
- **After 2.5 (10 tasks since the Phase 0 check-in):** status and loan UI demo.
- **2.10 Phase 2 check-in:** full WS-1 demo; refine Phase 3.

## Blockers Watchlist

- **QW-6:** the backup task's account can't see OneDrive or `age.exe` (PD-16 assumptions 1 and 4). Fix the account or path; don't move the backup to an unencrypted fallback.
- **SP-7 fails** (no usable model on typical hardware): escalate PD-9 before refining WS-4 or WS-9.
- **QW-4:** fixing the tests shows a real app bug. Record it, report it, fix it as its own change; don't mask it.
- **Migration 008:** anything that isn't purely additive needs an owner decision first.

## Definition of Completion (Phases 0–2)

- Tasks 0.1–2.10 are ✅, or 🚫 with an owner-approved reason.
- The owner's data has a tested, encrypted off-site copy.
- GOALS.md WS-0 and WS-1 success criteria are checked.
- Test suite green; no regression in capture, confirm, search, labels or cost lookup.
- DECISIONS.md updated with every spike result and any new decision.

---

## Completion Log

| Date | Task | Notes |
|---|---|---|
| 2026-11-26 | 0.1 CONTEXT.md | Approved by owner |
| 2026-11-26 | 0.2 DECISIONS.md | Approved by owner |
| 2026-11-26 | 0.3 QW-6 | `backup-data.ps1` encrypts each snapshot with age to `backup-offsite.recipient` and writes it to OneDrive `HomeInventoryBackups` (keep 3). Verified with a throwaway key: restore OK (integrity ok, 9 containers, 56 items, 11/11 photos), wrong/no key refused, skip, catch-up, prune, failure exit 2. Real key created at `%USERPROFILE%\.home-inventory-keys` (owner to move it to USB: BL-008). First real off-site file: `20261123-152641.tar.age`, 46.9 MB. Task runs as `jpful`, the OneDrive owner. `*.agekey` git-ignored |
| 2026-11-26 | 0.4 SP-1 | 56 items: 48 match exactly one photo through a confirmed detection; 8 have no matching detection but sit in a container with exactly one photo; 0 ambiguous. Backfill rule recorded in DECISIONS.md §4 |
| 2026-11-26 | 0.5, 0.6, 1.1, 2.9 | Paused by owner direction (skip testing). Listed in BL-008 |
| 2026-11-26 | 0.7 | Check-in replaced by the end-of-day report to the owner |
| 2026-11-26 | 1.2 QW-3 | README: setup via `start.ps1`, port 1800, Bonsai requirement, Backups section; no port 8000 left |
| 2026-11-26 | 1.3 QW-1 | CSV appends category, container_path (`A > B > C`), estimated_cost_usd, estimate_date; first 11 columns unchanged. Tests not written (paused) |
| 2026-11-26 | 1.4 QW-2 | `container_value_totals` (nested) and `household_value_totals`; shown on container pages and the dashboard with the unestimated count. Gone items excluded. Tests not written (paused) |
| 2026-11-26 | 1.5 QW-5 | Migration `008_cost_lookup_attempts` (backfilled from existing estimates); every outbound attempt recorded and committed before the call; limit read at call time. Tests not written (paused) |
| 2026-11-26 | 2.1–2.8 | Migration `009_lifecycle_and_loans`; repository (status, loans, verify, out-of-house count); 6 API endpoints; container-page status/loan UI and verify mode; dashboard Lent-out panel; search filter and badges (QR page shares the container template); CSV/JSON export fields. Migrations 008+009 applied to a copy of the live DB: integrity ok, 56/56 items `in_home`. App imports and templates parse. Live DB migrates on next app restart (BL-008) |
| 2026-11-26 | 2.10 | README section "Status, Loans and Verify Mode". Screenshot demo waits for the app restart (BL-008) |
