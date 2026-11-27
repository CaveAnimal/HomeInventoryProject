# DECISIONS LOG — summary_suggestions

> ⚠️ **AI AGENT INSTRUCTIONS**
> - Before making any design choice, check whether it is already decided here, in an inherited decision (§2), or in a supporting analysis ([DATA_PROTECTION.md](DATA_PROTECTION.md), [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md)).
> - Follow **ACCEPTED** and **VALIDATED** decisions. Don't build on a **PROPOSED** decision until it is accepted or its spike has run.
> - If you make a new design choice, add it here with its rationale and get owner approval. Don't contradict a decision without explicit owner approval.
> - If reality shows an ACCEPTED decision is unworkable, mark it **INVALIDATED** with evidence, mark dependent TODO tasks ⛔, and **escalate to the owner**. Don't build a workaround.

Pillar 3 of GOAL → CONTEXT → DECISIONS → TODO. Goals: [GOALS.md](GOALS.md) (APPROVED 2026-11-26). Current system: [CONTEXT.md](CONTEXT.md).

- **Status:** **APPROVED** by owner on 2026-11-26. Statuses in §0 are in effect.
- **Created:** 2026-11-26.

---

## How to use this document

**IDs.** Decisions keep the IDs they had in GOALS.md §6 (**PD-1…PD-15**), so existing references stay valid. New decisions continue from **PD-16**. Scope changes from the owner review are **SC-1…SC-6**. Decisions from earlier epics are referenced as **LV-D-00x** (llm_vision) and **CR-D-00x** (cost_of_replacement).

**Status values**

| Status | Meaning |
|---|---|
| PROPOSED | Leaning recorded; not yet approved, or waiting on a spike |
| ACCEPTED | Approved; follow it |
| VALIDATED | Accepted and proven in practice (spike passed or shipped) |
| INVALIDATED | Proven unworkable. Escalate; dependent work stops |
| SUPERSEDED | Replaced by a newer decision (named) |
| REJECTED / WITHDRAWN | Considered and not chosen, or dropped |

**Decided by:** *Owner* = the product owner decided directly. *Owner (approved)* = proposed by the AI and approved by the owner. *Pending* = not yet decided.

---

## 0. Decision Status Summary

Approved by the owner on 2026-11-26. "ACCEPTED" rows are in effect; "PROPOSED" rows wait on the spike or phase named.

| ID | Decision | Status | Why this status |
|---|---|---|---|
| PD-1 | Additive columns on `box_items` are allowed | ACCEPTED | Low risk; migration 003 already did it |
| PD-2 | Separate `lifecycle_status` column, ten values | ACCEPTED | Values confirmed by owner 2026-11-24 |
| PD-3 | Household isolation model | PROPOSED | Waits on SP-4 |
| PD-4 | Portable QR label scheme | PROPOSED | Refined with WS-4 |
| PD-5 | Share links | WITHDRAWN | Moved to BL-001 by owner |
| PD-6 | Disposition separate from lifecycle | ACCEPTED | Low risk; keeps WS-1 and WS-5 independent |
| PD-7 | PDF rendering approach | PROPOSED | Waits on SP-3 |
| PD-8 | Simple local accounts | ACCEPTED | Follows from local-first and no SaaS |
| PD-9 | Business model: licensed, self-run software | **ACCEPTED** | Confirmed by owner 2026-11-26 |
| PD-10 | Offline license, no phone-home | ACCEPTED | Follows from LV-D-001; details refined in WS-9 |
| PD-11 | Data protection strategy (3-2-1, encryption mandatory) | ACCEPTED | Owner direction; engine details are PD-12 |
| PD-12 | Backup engine: restic + rclone | PROPOSED | Waits on SP-9 |
| PD-13 | Store working copies, never full-size uploads | ACCEPTED | Owner direction; the 2,400 px size is checked by SP-10 |
| PD-14 | Capture paths (Library-first, Quick Photo, inbox untouched) | PROPOSED | Waits on SP-10 |
| PD-15 | Leave stored originals; opt-in compaction | ACCEPTED | Safe default; nothing changes unless the owner runs it |
| PD-16 | QW-6 interim off-site backup: age (public-key) to OneDrive, owner's install only | ACCEPTED | Tool (age) and destination (OneDrive) chosen by owner; customers pick their own in WS-10 |
| PD-17 | QW-4: tests use a fake LLM provider for the 3 heuristic-provider failures | ACCEPTED | Option 1 approved 2026-11-26 |

---

## 1. Program Decisions

### PD-1 — Additive columns on `box_items` are allowed

- **Date:** 2026-11-24 (proposed) · **Status:** ACCEPTED (owner approved 2026-11-26) · **Decided by:** Owner (approved) · **Blocks:** WS-1, WS-2
- **Context:** cost_of_replacement deliberately added no columns to `box_items` (CR-D-004) so that feature could be dropped cleanly. WS-1 and WS-2 need per-item fields such as lifecycle status, last verified, brand, model and serial.
- **Decision:** New per-item **facts** may be added as columns on `box_items`, always with a default so existing rows stay valid (as migration 003 did). Data with **history or multiple rows per item** (loans, evidence photos, estimates) gets its own table.
- **Rationale:** these fields are core to every view and report; a side table for each would mean joins everywhere for no benefit. History tables keep the insert-only audit pattern.
- **Alternatives:** one side table per feature (cleaner removal, many joins everywhere); a generic key/value attributes table (flexible, untyped and hard to query in reports). Both rejected.
- **Consequences:** `box_items` grows wider over the program. Each column is documented in its migration. Removing a feature leaves its columns in place (harmless with defaults).
- **Verification:** every new migration touching `box_items` uses `ALTER TABLE … ADD COLUMN … DEFAULT …` only.
- **Rollback:** columns stay but are ignored; the feature's code is reverted.

### PD-2 — Lifecycle status is a separate column from AI certainty

- **Date:** 2026-11-24 · **Status:** ACCEPTED (owner approved 2026-11-26) · **Decided by:** Owner (values), Owner (approved) (design) · **Blocks:** WS-1
- **Context:** `box_items.status` already exists and means AI certainty (`confirmed` / `likely`). WS-1 needs to record where a thing physically is.
- **Decision:** add `box_items.lifecycle_status TEXT NOT NULL DEFAULT 'in_home'` with exactly ten values: `in_home`, `loaned`, `in_repair`, `in_vehicle`, `in_storage_offsite`, `donated`, `sold`, `given_away`, `discarded`, `missing`. The UI labels the old field **"AI certainty"** and the new one **"Status"**. Values are checked in the app (a SQLite `CHECK` cannot be added to an existing column).
- **Rationale:** overloading `status` would break existing queries and confuse "the AI wasn't sure" with "it's gone".
- **Alternatives:** reuse `status` with more values (breaks existing meaning and code); a separate status table (heavier, no history need beyond `edit_history`).
- **Assumptions:** the ten values cover the owner's cases (✅ confirmed by owner 2026-11-24).
- **Verification:** tests cover each value and the allowed transitions; `status` behavior is unchanged.
- **Rollback:** the column has a default; revert the code.

### PD-3 — Household isolation model

- **Date:** 2026-11-24 · **Status:** PROPOSED (decided by SP-4) · **Blocks:** WS-4
- **Context:** WS-4 lets one install hold more than one household (the owner's documentation service) and transfer a household to a client's install.
- **Options:** (a) `household_id` on every table; (b) one database file plus photo folder per household.
- **Leaning:** undecided. Option (b) makes transfer, per-household backup and hand-over close to copying a folder, which matters more now that transfer is a core flow. Option (a) is simpler to query across households.
- **Assumptions to test in SP-4:** effort of each; how to prove isolation in tests; effect on transfer and on WS-10 backup repositories.

### PD-4 — Portable QR label scheme

- **Date:** 2026-11-24 · **Status:** PROPOSED (refined with WS-4) · **Blocks:** WS-4
- **Context:** labels encode the creating request's host and port, for example `http://192.168.x.x:1800/box/<public_id>` (CONTEXT.md §4 Scenario 6). They break on an IP change or a transfer to another install.
- **Leaning:** a stable local host name plus a short path (`/q/{public_id}`), with `public_id` unique across installs (for example a UUID), the old `/box/{public_id}` route kept as an alias, and a bulk-regenerate tool.
- **Open:** how a client's phone resolves the stable name on their network (mDNS / `.local`, router DNS, or a printed fallback code).

### PD-5 — Read-only share links

- **Status:** WITHDRAWN 2026-11-24 by owner. Moved to [BL-001](../../backlog/BL-001-read-only-share-links.md).

### PD-6 — Disposition is separate from lifecycle status

- **Date:** 2026-11-24 · **Status:** ACCEPTED (owner approved 2026-11-26) · **Blocks:** WS-5
- **Decision:** disposition is a **plan** ("Gift to Sarah", Keep / Sell / Donate / Gift / Discard / Undecided). Lifecycle status is a **fact** ("given_away"). They are separate fields. Carrying out a disposition updates lifecycle status.
- **Rationale:** a plan can change many times before anything happens; mixing them loses either the plan or the fact.
- **Rollback:** WS-5 columns are ignored; WS-1 is unaffected.

### PD-7 — Report rendering approach

- **Date:** 2026-11-24 · **Status:** PROPOSED (decided by SP-3) · **Blocks:** WS-3
- **Candidates:** HTML + browser print-to-PDF, WeasyPrint, ReportLab.
- **Constraint:** renders locally on Windows with no cloud service (LV-D-001); handles photo thumbnails and long tables.
- **Implementation note:** whichever wins goes behind a small provider interface, following the existing provider pattern, so it can be swapped.

### PD-8 — Simple local accounts

- **Date:** 2026-11-24 · **Status:** ACCEPTED (owner approved 2026-11-26) · **Blocks:** WS-4
- **Decision:** local user accounts with salted, slow password hashes (for example `hashlib.scrypt` from the standard library) and server-side session cookies. Roles: admin, member, read-only. No external identity provider, no OAuth, no self-signup.
- **Rationale:** the app runs on the household's own PC and network; an external identity provider would break local-first and the no-SaaS model.
- **Open (WS-4 refinement):** password reset when the only admin forgets (likely a local recovery code on the Recovery Sheet, shared with WS-10).

### PD-9 — Business model: licensed, self-run software

- **Date:** 2026-11-24 (direction), **2026-11-26 (confirmed)** · **Status:** **ACCEPTED** · **Decided by:** Owner · **Blocks:** WS-4, WS-8, WS-9
- **Context:** owner review §8 Q4: "I thought that the client would license this software?"
- **Decision:** households **license the software and run it on their own hardware**, editing their own inventory. The owner may also offer an optional documentation service: photograph and catalog a home, then hand the finished inventory over to the client's install. **No hosted SaaS.** No immediate clients and no target date.
- **Rationale:** matches the privacy promise (data never on the vendor's servers), needs no hosting or operations work, and gives the documentation service a clean hand-over.
- **Assumptions:**

  | # | Assumption | Risk if wrong | How to validate | Status |
  |---|---|---|---|---|
  | 1 | A typical household PC can run a local vision model well enough | **High**: licensing isn't viable as designed | SP-7 (Phase 0) | ⬜ Untested |
  | 2 | The app can be packaged into one installer a non-technical user can run | Medium | SP-8 | ⬜ Untested |

- **Consequences:** adds WS-9 (installer, offline license, updates, user guide) and WS-8 business items (EULA, tiers, support). WS-4 is about accounts, households and transfer rather than a shared server.
- **Rollback:** a business decision; revisit if SP-7 fails, with a new owner decision.

### PD-10 — Offline license mechanism

- **Date:** 2026-11-24 · **Status:** ACCEPTED (owner approved 2026-11-26) (details refined in WS-9) · **Blocks:** WS-9
- **Decision:** a signed license file checked locally. **No phone-home, no telemetry.** If a license lapses, the app becomes read-only: data always stays viewable and exportable. Never a data lock-out.
- **Rationale:** follows from LV-D-001; a license server would send data off the client's machine and create an operations burden.
- **Open (WS-9):** tiers, how a license file is delivered, grace period.

### PD-11 — Data protection strategy

- **Date:** 2026-11-24 (direction), 2026-11-26 (encryption kept mandatory) · **Status:** ACCEPTED (owner approved 2026-11-26) · **Decided by:** Owner · **Blocks:** WS-10, QW-6
- **Context:** owner direction §8 item 6: the least expensive way to keep data safe, on the customer's own computer on two media types, and an encouraged encrypted backup somewhere free or low cost. Full analysis in [DATA_PROTECTION.md](DATA_PROTECTION.md).
- **Decision (3-2-1):**
  - **Tier 1, required:** automatic, versioned, encrypted backup to a USB drive (flash drive minimum, external HDD/SSD recommended).
  - **Tier 2, encouraged:** encrypted off-site copy to the customer's own Google Drive or OneDrive ($0), Backblaze B2 (low cost), or a relative's PC via Syncthing.
  - **Every backup copy is encrypted, with no opt-out in the first release** (owner decision 2026-11-26). Optional local-only encryption is parked as [BL-007](../../backlog/BL-007-optional-local-backup-encryption.md), revisited only if customers ask.
  - The customer alone holds the key, with a printable Recovery Sheet. The vendor never holds data or keys.
- **Rationale:** a home inventory is a burglar's shopping list; a lost unencrypted drive leaks it. The cost to the customer is $0–15 minimum.
- **Assumptions:** customers will keep the Recovery Sheet (mitigated by repeated guidance and the quarterly verify check). Engine-level assumptions belong to PD-12.
- **Rollback:** backups are extra copies and never touch live data.

### PD-12 — Backup engine

- **Date:** 2026-11-24 · **Status:** PROPOSED (decided by SP-9) · **Blocks:** WS-10 (and QW-6 if it waits for SP-9)
- **Leaning:** **restic + rclone**, bundled and driven by the app. Kopia as fallback. Never custom encryption. Comparison in [DATA_PROTECTION.md §4](DATA_PROTECTION.md).
- **Assumptions (SP-9 checklist, DATA_PROTECTION.md §8):**

  | # | Assumption | Risk if wrong | Status |
  |---|---|---|---|
  | 1 | restic (BSD-2) and rclone (MIT) can be bundled in a commercial installer | High | ⬜ |
  | 2 | First and incremental backups of 10 GB finish in acceptable time from Python on Windows | Medium | ⬜ |
  | 3 | rclone's Google Drive / OneDrive authorization is manageable for non-technical users | High (else Kopia) | ⬜ |
  | 4 | Windows Credential Manager works under the app's account, including SYSTEM | High | ⬜ |
  | 5 | Free-tier sizes and B2 prices still match DATA_PROTECTION.md §3 | Low | ⬜ |

### PD-13 — Store working copies, never full-size uploads

- **Date:** 2026-11-24 (direction) · **Status:** ACCEPTED (owner approved 2026-11-26) · **Decided by:** Owner · **Blocks:** WS-11; WS-10 sizing
- **Context:** owner direction §8 item 7. Today every upload is saved full-size (`main.py:551-553`, CONTEXT.md §1).
- **Decision:** every upload path produces one **working copy**: longest edge 2,400 px, JPEG quality 85, upright, **GPS removed**, with date taken and original filename recorded (optionally a SHA-256 fingerprint of the original). **The app never saves the full-size upload to disk.** The household's original is never touched. Analysis in [USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md).
- **Rationale:** 74% less storage (measured 1.42 MB vs 5.35 MB), which makes the free backup tiers realistic; less sensitive data held; a clear line of responsibility.
- **Assumptions:**

  | # | Assumption | Risk if wrong | How to validate | Status |
  |---|---|---|---|---|
  | 1 | Detection accuracy at 2,400 px matches originals | Medium | Golden set (`scripts/vision_eval`) in SP-10 | ⬜ |
  | 2 | Serial and model stickers stay readable at 2,400 px | Medium | SP-2 with SP-10 | ⬜ |

  If either fails, the working-copy size is raised (it's a setting). The principle stays.
- **Wording rule:** never say the app "discards" or "deletes" originals (USER_OWNED_ORIGINALS.md §6).
- **Rollback:** a "store original" setting kept for rollback.

### PD-14 — Capture paths

- **Date:** 2026-11-24 · **Status:** PROPOSED (decided after SP-10) · **Blocks:** WS-11
- **Leaning:** "Choose From Library" is the primary path. The in-app camera becomes "Quick Photo" with a "Save original to my phone" prompt (or is removed, after SP-10). **Inbox files are never moved or deleted**; they're recorded by name and fingerprint so they aren't imported twice. Today they are moved (`main.py:464`). Optional in-browser resize before upload.

### PD-15 — Photos already stored

- **Date:** 2026-11-24 · **Status:** ACCEPTED (owner approved 2026-11-26) · **Blocks:** WS-11
- **Decision:** existing stored photos are left as they are by default. Some exist nowhere else. An optional one-time "Compact existing photos" tool runs only after a verified backup and with confirmation, and warns that the full-size copies stored in the app will be replaced.

### PD-16 — QW-6 interim off-site backup uses age encryption *(new)*

- **Date:** 2026-11-26 · **Status:** ACCEPTED (owner approved 2026-11-26) (tool and destination chosen by owner) · **Decided by:** Owner · **Blocks:** QW-6
- **Context:** the owner moved QW-6 to the front of WS-0 (SC-6). SP-9 hasn't run, so the PD-12 engine isn't confirmed. QW-6 must still be encrypted (PD-11).
- **Decision:** use **[age](https://age-encryption.org)** (owner choice, 2026-11-26; 7-Zip rejected). After each successful snapshot, `backup-data.ps1` packs the snapshot folder with Windows' built-in `tar` and encrypts it with age into **one file**, `<snapshot>.tar.age`, in an off-site destination folder. It logs success or failure. The local snapshot is never deleted or changed by this step.
- **Keys: public-key mode, not passphrase.** age's passphrase mode (`-p`) only works interactively, so a scheduled task can't use it. Instead:
  - `age-keygen` creates a key pair once.
  - The **public key** (`age1…`, not secret) is kept in the repo or config, and the script encrypts with `age -r <public key>`. **No secret is needed on the PC for backups to run.**
  - The **private key** (the only thing that can decrypt) is kept **off the PC**: printed on the Recovery Sheet and stored on a USB stick, with a second copy somewhere safe. It is never stored in the off-site folder.
  - This is stronger than storing a password in Credential Manager: someone who takes over the PC or the cloud account still can't read the backups.
- **Restore:** `age -d -i key.txt <snapshot>.tar.age | tar -xf -` on any computer with age installed. This goes in the Recovery Sheet.
- **Installed:** age **1.3.2** via winget (`FiloSottile.age`), already on the owner's PC under the user account (`%LOCALAPPDATA%\Microsoft\WinGet\Links\age.exe`). License BSD-3-Clause.
- **Assumptions:**

  | # | Assumption | Risk if wrong | How to validate | Status |
  |---|---|---|---|---|
  | 1 | The account running the "HomeInventory Data Backup" task can find `age.exe` (the winget link is per-user; SYSTEM can't see it) | Medium: off-site step fails | QW-6: call age by absolute path, or install it machine-wide; check the task's account | ⬜ |
  | 2 | A full encrypted copy per run is small enough for the destination | Low: 47 MB today | QW-6: check size; keep the newest N off-site files | ⬜ |
  | 3 | A restore from the off-site file works on another computer | High if untested | QW-6 acceptance: decrypt and open the DB on a second machine or a clean folder | ⬜ |
  | 4 | The backup task's account can write to the OneDrive folder, and OneDrive is signed in and syncing when the task runs (on this PC `$env:OneDrive` points to a different Windows user profile from the one running these tools) | Medium: files written but never uploaded | QW-6: run the task under the account that owns OneDrive; check the file appears on onedrive.com | ⬜ |

- **Destination (owner's install): OneDrive** (owner choice, 2026-11-26). The script writes into a folder inside the OneDrive-synced folder (`$env:OneDrive\HomeInventoryBackups` by default), and the OneDrive client uploads it. The path is a script parameter, not hard-coded, so it can be changed to Google Drive, the NAS or anything else later.
- **Retention off-site:** keep the newest **3** encrypted files (a parameter). Each file is a full copy: 47 MB today, about 4.4 GB at 3,000 photos, so 3 copies would outgrow OneDrive's free 5 GB tier as the inventory grows (fine with Microsoft 365's 1 TB).
- **Customers choose their own destination.** QW-6 is for the owner's install only. Customers get WS-10, where first-run setup offers every PD-11 Tier 2 option and the customer picks: their own Google Drive or OneDrive, Backblaze B2, a relative's PC via Syncthing, or none. Nothing about the owner's OneDrive choice is a default for customers.
- **Relation to WS-10:** age is an interim tool for the owner's install. WS-10 uses the PD-12 engine (restic + rclone) for everyone, and QW-6 is retired then.
- **Rollback:** remove the off-site step; the local snapshot behavior is unchanged.

### PD-17 — How QW-4 handles the heuristic-provider test failures *(new)*

- **Date:** 2026-11-26 · **Status:** ACCEPTED (owner approved 2026-11-26, option 1) · **Decided by:** Owner (approved) · **Blocks:** QW-4
- **Context:** three tests fail because `save_photos_and_detect()` now refuses non-LLM providers (`main.py:539-541`), while the tests run with `VISION_PROVIDER=heuristic` and expect suggestions (CONTEXT.md §4 Scenario 7). That's a real mismatch, not teardown noise.
- **Options:**
  1. **Tests use a fake LLM provider** (a test double registered as an LLM provider that returns fixed detections). The production rule "only real LLM providers create suggestions from uploads" stays.
  2. Let the heuristic provider through the upload path again when an explicit test-only setting is on.
  3. Update the tests to expect no suggestions from heuristic, and cover detection through the fake provider elsewhere.
- **Decision:** **option 1.** It keeps the production rule, keeps end-to-end coverage, and adds no test-only switch to app code.
- **Also in QW-4:** fix the SQLite file-lock errors by closing every connection (or using a fresh temp DB per test). Re-run to confirm none were knock-on effects.

---

## 2. Inherited Decisions (still binding)

These come from earlier epics. This program must not contradict them without an owner decision.

| Ref | Decision | Source | Note for this program |
|---|---|---|---|
| LV-D-001 | Vision runs locally (no cloud vision by default) | [llm_vision/DECISIONS.md](../llm_vision/DECISIONS.md) D-001 | Written for Ollama; the backend is now Bonsai on llama.cpp (commit `c170736`). The **local-only principle** is what binds |
| LV-D-002 | AI output is confirmed by a person before entering inventory | llm_vision D-002 | Applies to WS-2 AI-read fields too |
| LV-D-003 | Strict detection contract (`normalize_detection`) | llm_vision D-003 | Unchanged by WS-11 |
| LV-D-004 | Container type defaults to `box` | llm_vision D-004 | — |
| LV-D-005 | iPhone capture page is the review surface | llm_vision D-005 | WS-11 reorders it (Library-first), doesn't replace it |
| CR-D-001 | Cost provider abstraction mirrors `VisionProvider` | [cost_of_replacement/DECISIONS.md](../cost_of_replacement/DECISIONS.md) D-001 | Pattern for any new pluggable piece (PD-7, PD-12) |
| CR-D-002 | Local LLM does all extraction | CR D-002 | Now Bonsai by default (`COST_LOOKUP_LLM`) |
| CR-D-003 | One item per outbound search request | CR D-003 | WS-5 resale lookup too |
| CR-D-004 | Estimates are insert-only history | CR D-004 | — |
| CR-D-005 | Kill switch `COST_LOOKUP_PROVIDER=disabled` | CR D-005 | — |
| CR-D-006 | App-side monthly budget guard | CR D-006 | QW-5 makes it count attempts, not just successes |
| CR-D-007 | Search provider: Tavily | CR D-007 | — |

---

## 3. Scope Changes from the Owner Review

GOALS.md §8 records the owner's words. These entries record what each one changed.

| ID | Date | Change | From | Effect |
|---|---|---|---|---|
| SC-1 | 2026-11-24 | Added **WS-9 Licensing & Distribution**; WS-4 reframed around accounts, households and transfer | §8 Q4, PD-9 | New spikes SP-7, SP-8; WS-8 gains EULA, tiers, support |
| SC-2 | 2026-11-24 | WS-1 lifecycle statuses grew from eight to **ten** (`in_repair`, `in_vehicle`) | §8 Q3 | PD-2 |
| SC-3 | 2026-11-24 | ⚠️ MAYBE items moved to the **backlog** (BL-001…BL-006); PD-5 withdrawn | §8 Q5 | Backlog created at `docs/AI_Planning/backlog/` |
| SC-4 | 2026-11-24 | Added **WS-10 Data Protection** | §8 item 6 | PD-11, PD-12, SP-9; QW-6 aligned |
| SC-5 | 2026-11-24 | Added **WS-11 User-Owned Originals** | §8 item 7 | PD-13…15, SP-10 |
| SC-6 | 2026-11-26 | Order confirmed with WS-11 → WS-10 after WS-1; **QW-6 first** within WS-0; optional backup encryption parked as BL-007 | §8 rows 8–10 | PD-16 added for QW-6 (age chosen over 7-Zip) |

---

## 4. Validation Log

Filled in as spikes run and decisions meet reality.

| Date | Decision | Spike / evidence | Outcome |
|---|---|---|---|
| 2026-11-26 | All §0 statuses | Owner review of DECISIONS.md | ACCEPTED rows in effect; PD-3, PD-4, PD-7, PD-12, PD-14 remain PROPOSED pending their spikes or phases |
