ALTER TABLE detection_suggestions ADD COLUMN source_model TEXT DEFAULT '';
ALTER TABLE detection_suggestions ADD COLUMN pass_type TEXT DEFAULT 'live';

ALTER TABLE box_photos ADD COLUMN deep_scan_model TEXT DEFAULT '';
ALTER TABLE box_photos ADD COLUMN deep_scanned_at TEXT;
