-- QW-5: count every outbound cost-lookup attempt (success or failure) toward
-- COST_LOOKUP_MONTHLY_LIMIT. Additive only. Existing estimates are copied in
-- as past attempts so this month's count stays correct after the upgrade.
CREATE TABLE IF NOT EXISTS cost_lookup_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cost_lookup_attempts_created_at ON cost_lookup_attempts(created_at);

INSERT INTO cost_lookup_attempts(created_at)
SELECT created_at FROM cost_estimates;
