# BL-007 — Optional encryption for the local backup

- **Status:** parked
- **Origin:** [summary_suggestions DATA_PROTECTION.md](../support/summary_suggestions/DATA_PROTECTION.md) / PD-11. Owner decision on 2026-11-26: "skip the optional encryption for a future release and only if there is demand."

## Idea
Let the customer turn off encryption for the **local USB backup only** (Tier 1). Encryption stays on by default, and turning it off shows a clear warning ("a lost or stolen drive shows what you own and where it is") that the customer has to confirm. The **off-site copy (Tier 2) stays encrypted always**, because an unencrypted cloud copy would break the privacy promise (R4). Off-site backup is already optional, so nobody is forced into encryption unless they want a cloud copy.

Why a customer might want it: no password to lose, and the backup files can be opened directly without the app or restic.

## Why deferred
- The first release ships with **every backup copy encrypted**, as PD-11 and GOALS.md §1 state. There's no demand yet.
- restic and Kopia (PD-12) **always encrypt** and have no off switch. An unencrypted option needs a second backup path, such as plain versioned folder copies like `backup-data.ps1` makes today. That means two code paths to build, test and support instead of one.
- The main reason people want encryption off is fear of losing the password. The Recovery Sheet (DATA_PROTECTION.md §5) is meant to address that first.

## What it would take
- A setting on the Data Protection page: "Encrypt local backup" (default on), with the warning and confirmation when turned off.
- A plain versioned-copy backup path for Tier 1 with the same retention (7 daily / 4 weekly / 12 monthly), SQLite online backup and integrity check as the restic path.
- Restore wizard support for plain snapshots.
- Recovery Sheet and password steps shown only when encryption is on.
- Dashboard status shows 🟡 for an unencrypted local backup, as a gentle reminder.
- Doc updates: GOALS.md §1 constraint ("every backup copy is encrypted" → "encrypted by default"), DATA_PROTECTION.md §1 R1, §2, §4 and §5, and the EULA wording (WS-8).

## Depends on
WS-10 shipped with the PD-12 engine. A decision on whether a second backup path is acceptable to maintain.

## Revisit when
Customers ask for it: repeated support requests about lost backup passwords, or customers who want to open backup files without the app.
