CREATE TABLE boxes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL UNIQUE,
  notes TEXT DEFAULT '',
  tags TEXT DEFAULT '',
  inaccessible INTEGER DEFAULT 0,
  size TEXT DEFAULT '',
  stack_position TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE box_locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_id INTEGER NOT NULL UNIQUE REFERENCES boxes(id) ON DELETE CASCADE,
  room_name TEXT NOT NULL,
  north_ft REAL NOT NULL DEFAULT 0,
  east_ft REAL NOT NULL DEFAULT 0,
  elevation_ft REAL NOT NULL DEFAULT 0,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE box_photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_id INTEGER NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  content_type TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE box_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_id INTEGER NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
  item_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed', 'likely')),
  confidence REAL NOT NULL DEFAULT 1,
  category TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  tags TEXT DEFAULT '',
  priority INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_box_items_normalized ON box_items(normalized_name);
CREATE INDEX idx_box_items_box ON box_items(box_id);

CREATE TABLE detection_suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_id INTEGER NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
  photo_id INTEGER REFERENCES box_photos(id) ON DELETE SET NULL,
  item_name TEXT NOT NULL,
  quantity INTEGER DEFAULT 1,
  confidence REAL DEFAULT 0.5,
  category TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  status TEXT DEFAULT 'suggested' CHECK(status IN ('suggested', 'confirmed', 'dismissed')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE labels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  box_id INTEGER NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  target_url TEXT NOT NULL,
  format TEXT DEFAULT 'single',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edit_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  before_json TEXT DEFAULT '{}',
  after_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
