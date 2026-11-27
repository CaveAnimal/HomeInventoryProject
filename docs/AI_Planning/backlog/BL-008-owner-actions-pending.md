# BL-008 — Owner actions pending

- **Status:** parked (waiting on the owner)
- **Origin:** [summary_suggestions TODO.md](../support/summary_suggestions/TODO.md), 2026-11-26. Owner direction: "If you are waiting on me, then put it on backlog."

Work the agent finished but that needs the owner to complete. Each item says why it matters. Tick them off here; when all are done, set Status to `dropped` with "done".

## 1. Move the backup private key off the PC (QW-6, PD-16) — important
The age private key that decrypts the off-site backups is at `%USERPROFILE%\.home-inventory-keys\home-inventory-backup.agekey` (readable by your Windows account only). PD-16 says it should **not** stay on the PC.
- [ ] Copy it to a USB stick.
- [ ] Print a **Recovery Sheet**: the key's contents (the `AGE-SECRET-KEY-…` line), where backups are (`D:\HomeInventoryBackups`; OneDrive `HomeInventoryBackups`), and the restore steps from the header of `backup-data.ps1`. Keep it with insurance papers.
- [ ] Put a second copy of the key somewhere safe away from home.
- [ ] Delete the copy on the PC.
- **Why:** until then, someone with access to this PC could decrypt the off-site backups. Without any copy, the backups can't be restored.

## 2. Confirm the off-site file reached OneDrive (QW-6)
- [ ] On onedrive.com, check `HomeInventoryBackups` contains `20261123-152641.tar.age` (46.9 MB).

## 3. Restart the app to apply the new code (Phase 1 and 2)
- [ ] Run `stop.ps1` then `start.ps1` (or restart the PC). The app runs under an account the agent can't restart.
- On start, migrations `008_cost_lookup_attempts` and `009_lifecycle_and_loans` apply to the live database. Both are additive and were checked on a copy (all 56 items become "In home"; integrity `ok`). A backup of the current data exists on `D:` and in OneDrive.

## 4. Decisions deferred by "skip the testing for now" (2026-11-26)
Not waiting on the owner's action, but on the owner's go-ahead to run them:
- [ ] **QW-4** (TODO 1.1): fix the 6 failing tests (PD-17: fake LLM provider; close SQLite connections).
- [ ] **WS-1 tests** (TODO 2.9).
- [ ] **QW-6 acceptance checks** still open: a scheduled (not manual) run, and a restore with the real key on a second computer.
- [ ] **SP-3** (PDF approach, before WS-3) and **SP-7** (household hardware, before WS-4/WS-9).

## Revisit when
The owner has a few minutes for items 1–3 (item 1 first), or gives the go-ahead for item 4.
