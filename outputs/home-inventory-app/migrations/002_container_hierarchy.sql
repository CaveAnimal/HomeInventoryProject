ALTER TABLE boxes ADD COLUMN parent_box_id INTEGER REFERENCES boxes(id) ON DELETE SET NULL;
ALTER TABLE boxes ADD COLUMN container_type TEXT NOT NULL DEFAULT 'box';

CREATE INDEX IF NOT EXISTS idx_boxes_parent ON boxes(parent_box_id);
CREATE INDEX IF NOT EXISTS idx_boxes_type ON boxes(container_type);
