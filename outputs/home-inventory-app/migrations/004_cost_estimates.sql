CREATE TABLE cost_estimates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_item_id INTEGER NOT NULL REFERENCES box_items(id) ON DELETE CASCADE,
  estimated_cost_usd REAL,
  confidence REAL DEFAULT 0.5,
  source_title TEXT DEFAULT '',
  source_url TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cost_estimates_box_item ON cost_estimates(box_item_id);
