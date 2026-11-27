-- WS-1: where is it, and is it still here? (PD-1, PD-2)
-- Additive only. box_items.status keeps meaning AI certainty (confirmed/likely);
-- lifecycle_status is the physical state. Values are checked in the app:
-- in_home, loaned, in_repair, in_vehicle, in_storage_offsite,
-- donated, sold, given_away, discarded, missing.
ALTER TABLE box_items ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'in_home';
ALTER TABLE box_items ADD COLUMN status_changed_at TEXT;
ALTER TABLE box_items ADD COLUMN status_note TEXT NOT NULL DEFAULT '';
ALTER TABLE box_items ADD COLUMN last_verified_at TEXT;
ALTER TABLE boxes ADD COLUMN last_verified_at TEXT;

-- Loan history is kept: rows are closed with returned_at, never deleted.
-- An open loan has returned_at IS NULL; at most one per item (enforced below).
CREATE TABLE IF NOT EXISTS loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_item_id INTEGER NOT NULL REFERENCES box_items(id) ON DELETE CASCADE,
  borrower_name TEXT NOT NULL,
  borrower_contact TEXT NOT NULL DEFAULT '',
  loaned_at TEXT NOT NULL,
  due_at TEXT,
  returned_at TEXT,
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loans_box_item_id ON loans(box_item_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_loans_one_open_per_item ON loans(box_item_id) WHERE returned_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_box_items_lifecycle_status ON box_items(lifecycle_status);
