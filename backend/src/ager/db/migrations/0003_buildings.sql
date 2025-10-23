CREATE TABLE IF NOT EXISTS buildings (
  village_id INTEGER NOT NULL,
  building   TEXT NOT NULL,
  level      INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (village_id, building)
);
