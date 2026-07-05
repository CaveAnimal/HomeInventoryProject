# Insurance Evidence And Off-Site Backup

## Idea

Grow the inventory app toward insurance usefulness. Photos are the primary evidence. Other details may be estimates unless captured clearly in a photo or entered manually.

## Insurance Fields

Possible item fields:

```text
owned_by_date
brand
model
serial_number
condition
estimated_replacement_cost
estimated_purchase_cost
receipt_photo
evidence_photos
confidence
notes
```

## Evidence Rules

- `owned_by_date` can default to the date the photo was taken or uploaded.
- Brand/model can be detected from images or entered manually.
- Serial number should only be trusted when captured in a close-up photo.
- Cost and replacement cost are estimates unless supported by receipt data.
- Every important item should link to one or more evidence photos.

## Backup Need

For fire, flood, theft, or tornado scenarios, local backup is not enough. The app needs an off-site backup workflow.

## Backup Package

Create complete dated backups:

```text
home-inventory-backup-YYYY-MM-DD-HHMM.zip
  inventory.sqlite3
  photos/
  labels/
  receipts/
  evidence/
  export.json
  export.csv
```

## Off-Site Destinations

Good practical destinations:

```text
OneDrive
Google Drive
Dropbox
iCloud Drive
Backblaze
NAS at another location
S3-compatible cloud storage
external drive stored elsewhere
```

## Implementation Notes

- Keep SQLite for now unless scale demands otherwise.
- Add a "Backup Now" button.
- Add a backup destination setting.
- Show last backup timestamp.
- Warn if backup is stale.
- Include restore instructions.
- Consider optional encryption later.

