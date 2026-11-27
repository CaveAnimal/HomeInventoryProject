# Data Protection Strategy — Decision Analysis

*Supporting analysis for **PD-11** and **PD-12** in [GOALS.md](GOALS.md) §6, and for workstream **WS-10**. When DECISIONS.md is created, this becomes the body of those decisions. Until spike SP-9 confirms it, everything here is `PROPOSED`.*

- **Raised:** 2026-11-24, owner direction: "decide on the least expensive way to keep the user data safe and secure, first on their own computer, on two media types, and then encrypted and backed up somewhere free or low cost as an encouraged option to the customer."
- **Applies to:** every licensed install (PD-9), and the owner's own install.

---

## 1. The Requirement

| # | Requirement | Required or encouraged |
|---|---|---|
| R1 | Data is protected **on the customer's own premises**, on **two different media types** | **Required.** The app sets this up during first-run and nags if it is missing |
| R2 | An **encrypted off-site copy** at no cost or low cost | **Encouraged.** Offered and recommended, never forced |
| R3 | Least expensive overall for the customer | Design goal |
| R4 | The customer alone holds the keys. The vendor (owner) never holds customer data or keys. | **Required** (privacy promise, D-001 / PD-10) |
| R5 | Backups happen **automatically**. A backup that depends on remembering isn't a backup. | **Required** |
| R6 | A restore is possible and **has been tested** | **Required** |

This is the standard **3-2-1 rule**: 3 copies of the data, on 2 different media types, 1 of them off-site. R1 gives the first two copies on two media types. R2 adds the off-site copy.

### What is being protected
- `inventory.sqlite3`: the database (small: MB).
- `photos/`: the bulk of the data. Under PD-13 ([USER_OWNED_ORIGINALS.md](USER_OWNED_ORIGINALS.md)) these are **working copies** (2,400 px, measured average 1.42 MB), so 3,000 photos come to about **4.3 GB**. Stored originals were about 16 GB for the same count. The owner's install today is 47 MB with 11 photos, still originals (PD-15).
- `labels/`: regenerable, but small enough to include.
- **Not protected by the app:** the user's **original photos**. They live on the user's phone or in their own folders, and backing them up is the user's responsibility (iCloud Photos, Google Photos, their own PC backup). The app says so in onboarding and the user guide.

### Why encryption matters even for the local copy
A home inventory is **a burglar's shopping list**: what's valuable, which room, which shelf, which box. An unencrypted backup drive that is stolen, lost or thrown away leaks all of it. So **every backup copy is encrypted**, including the one on the customer's desk, not only the off-site one.

**Encryption is not optional in the first release** (owner decision, 2026-11-26). Letting customers turn it off for the local copy is parked as [BL-007](../../backlog/BL-007-optional-local-backup-encryption.md), to revisit only if customers ask for it. The off-site copy would stay encrypted either way.

---

## 2. Tier 1 — On the Customer's Premises, Two Media Types (Required)

**Copy 1:** the live data on the computer's internal drive (SSD or HDD), as today.
**Copy 2:** an automatic, versioned, encrypted backup on a **removable USB drive**, a different device and media type.

### Options considered for Copy 2

| Option | Approx. cost (US retail, late 2026, verify) | Protection | Verdict |
|---|---|---|---|
| **USB flash drive, 64–128 GB** | about $8–15 one-time | Survives internal drive failure, ransomware if unplugged, theft of the PC | ✅ **Minimum.** Cheapest acceptable; with working copies (about 4.3 GB per 3,000 photos) it holds many versions of a typical home. Replace every few years (flash wears out). |
| **External USB hard drive or SSD, 1 TB** | about $50–70 one-time | Same, more capacity, longer life | ✅ **Recommended.** Room for years of versions and other family files |
| Second folder on the same internal drive | $0 | None against drive failure, theft or ransomware | ❌ Not a second media type. Protects only against accidental deletion. Still useful as fast "undo" versions alongside a real Copy 2. |
| Second internal drive | about $40–80 + installation | Drive failure only; same theft/fire/ransomware exposure | ❌ Requires opening the PC; worse protection than removable |
| NAS (network storage box) | about $150–400 | Good, if maintained | ❌ Too expensive and complex as a requirement; supported as an alternative destination |
| Optical disc (M-DISC Blu-ray) | about $3–5 per disc + a drive most PCs lack | Very long archival life | ❌ Few customers have a drive; manual process breaks R5 |
| SD card | about $8–15 | Like a flash drive, easier to lose | ⚠️ Allowed as a flash-drive substitute, not recommended |

**Decision for Tier 1 (PD-11a):** Copy 2 is an encrypted, versioned backup on a **USB drive**. A flash drive is the minimum and an external HDD/SSD is recommended. Most households already own one, so the usual extra cost is **$0–15**.

### How it behaves
- **Automatic:** after each capture/confirm session (debounced, for example 10 minutes after the last change) and on a daily schedule. It runs whenever the drive is plugged in, and catches up as soon as a missing drive is reconnected.
- **Versioned with retention:** for example 7 daily, 4 weekly and 12 monthly snapshots. A mistake or corruption can be rolled back to an earlier version, not just to the latest copy.
- **Consistent:** the database is captured with SQLite's online backup API (as `backup-data.ps1` already does) and checked with an integrity check before it counts as a good snapshot.
- **Nagging:** the dashboard shows a **Data Protection** status. 🟢 local backup within 7 days; 🟡 overdue, or no off-site copy; 🔴 no local backup ever or for more than 30 days. Overdue warnings are polite and recurring.
- **Ransomware hint:** the guide advises keeping the drive unplugged between backups where practical. The catch-up behavior makes this easy.

---

## 3. Tier 2 — Encrypted Off-Site Copy (Encouraged)

The backup tool **encrypts on the customer's computer before upload**. Destinations receive only scrambled data and can't read it ("zero-knowledge"). This makes free consumer cloud accounts safe to use.

### Destinations, cheapest first

| Destination | Approx. cost (verify; free tiers change) | Notes | Verdict |
|---|---|---|---|
| **Customer's existing Google Drive** | $0 (15 GB, shared with Gmail) | Most households already have one; working copies of a typical home (about 4.3 GB) fit | ✅ **Default suggestion** |
| **Customer's existing OneDrive** | $0 (5 GB; 1 TB with Microsoft 365) | Built into Windows; many have 365 already | ✅ **Default suggestion** for 365 households |
| iCloud Drive | $0 (5 GB) | Awkward to reach from Windows tools | ⚠️ Possible through its synced folder |
| **Backblaze B2** | First 10 GB free, then about $6/TB/month (≈ $0.06/month per 10 GB) | Purpose-built, reliable, supported natively by backup tools | ✅ **Low-cost recommendation** once free space runs out |
| Trusted relative's PC (Syncthing "untrusted device") | $0 | No cloud at all; relative's PC must be on sometimes | ✅ Alternative for cloud-averse customers |
| Second USB drive rotated to a relative's house or safe deposit box | Cost of the drive | Manual; breaks R5 unless very disciplined | ⚠️ Supported, not recommended as the only off-site copy |
| MEGA / Proton Drive / Filen | $0 at about 5–20 GB | Already encrypt themselves; fine destinations | ✅ Supported where the backup tool can reach them |

**Decision for Tier 2 (PD-11b):** off-site backup is offered during first-run and on the Data Protection page. It suggests the **customer's own Google Drive or OneDrive** first ($0), with **Backblaze B2** as the low-cost option, and Syncthing to a relative for customers who avoid cloud services. The vendor never provides or touches the storage.

---

## 4. The Backup Engine (PD-12)

One engine handles both tiers: two repositories (USB + off-site), one password, the same restore procedure.

| Criterion | **restic** | **Kopia** | Duplicati | Custom (zip + encryption) |
|---|---|---|---|---|
| Cost | Free | Free | Free | Free |
| Client-side encryption (AES-256 class) | ✅ always on | ✅ always on | ✅ | ⚠️ we'd own the crypto, a bad idea |
| Incremental + deduplicated versions | ✅ | ✅ | ✅ | ❌ full copies every time |
| Single binary, easy to bundle and drive from Python | ✅ | ✅ (CLI + optional GUI) | ⚠️ heavier, .NET-based | ✅ |
| Google Drive / OneDrive | via **rclone** | via rclone; some native | ✅ native | ❌ |
| Backblaze B2 / local USB | ✅ native | ✅ native | ✅ | ⚠️ USB only |
| License allows bundling in a commercial product (verify in SP-9) | BSD-2-Clause (permissive) | Apache-2.0 (permissive) | verify | n/a |
| Restore usable without our app | ✅ (standalone tool) | ✅ | ✅ | ⚠️ |

**Leaning (PD-12): restic + rclone**, bundled with the app and driven by it. Both are single, permissively licensed binaries, widely used, and scriptable, which suits an app that runs backups by itself. **Kopia is the fallback** if SP-9 finds a blocker (for example rclone setup for Google Drive proving too hard for non-technical users, where Kopia's GUI may help). Custom crypto is rejected: never write your own encryption.

---

## 5. Keys and Recovery (the part that loses people's data)

- At first-run the app creates the backup password together with the customer, and produces a **printable Recovery Sheet** (PDF). It contains the password or recovery key, where the backups are, and plain-language restore steps. The customer is told to keep it with their insurance papers or in a fireproof box.
- The app stores the password locally (Windows Credential Manager / DPAPI) so backups run unattended. **It is never sent anywhere.**
- **The vendor cannot recover a lost password.** This is stated plainly in onboarding and in the EULA (WS-8). It is the price of R4, and it is also a selling point.
- **Restore test:** first-run ends with a test restore of one file. After that, the app offers a quarterly "verify your backup" check (restic `check` + a sample restore), with the result shown on the Data Protection page.
- **Restore wizard:** restore everything, or a chosen snapshot, onto this or a new computer. This also works as moving to a new PC.

---

## 6. Cost Summary for the Customer

| Setup | One-time | Ongoing | Protection |
|---|---|---|---|
| **Minimum (required)** | $0 if they own a USB drive, otherwise about $8–15 | $0 | 2 copies, 2 media, encrypted |
| **Recommended** | about $50–70 (external drive) | $0 with own Google Drive/OneDrive | Full 3-2-1, encrypted |
| **Larger inventories / more versions** | about $50–70 | about $0.06–1/month on Backblaze B2 | Full 3-2-1, encrypted, plenty of room |

---

## 7. What This Means for the Owner's Own Install Today

- Copy 1: `E:` (WD_BLACK HDD). Copy 2: `D:\HomeInventoryBackups` (WD Elements external HDD), weekly via `backup-data.ps1`. That is **two devices, but the same media type (HDD), unencrypted, and no off-site copy**.
- WS-0 **QW-6** (off-site copy) comes first (owner decision, 2026-11-26). It encrypts each snapshot with **age** (public key on the PC, private key kept off it) and writes it to the owner's **OneDrive**-synced folder (PD-16). WS-10 later moves the owner onto the PD-12 engine, so the owner's setup is still the first real test of the customer design.
- **Customers are not tied to OneDrive.** The owner's destination is a personal choice. Customers pick their own off-site destination from the Tier 2 options in §3 during first-run setup.

---

## 8. Open Items for SP-9 (spike, 3 h)

1. Confirm restic and rclone licenses allow bundling in a commercial installer, and note any attribution requirements.
2. Time a first backup and an incremental backup of a 10 GB sample to USB and to Google Drive (via rclone), from Python on Windows.
3. Assess how hard rclone's Google Drive / OneDrive authorization is for a non-technical user. If it's too hard, evaluate Kopia.
4. Confirm storing the password in Windows Credential Manager works under the account that runs the app (including the SYSTEM boot task the owner uses).
5. Re-check free-tier sizes and B2 pricing on the day of the spike and update §3.

Result: PD-11 and PD-12 marked ACCEPTED, or revised, in DECISIONS.md.
