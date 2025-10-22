-- Initial schema for AGER database
CREATE TABLE IF NOT EXISTS village (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
    village_id INTEGER PRIMARY KEY,
    wood INTEGER DEFAULT 0,
    clay INTEGER DEFAULT 0,
    iron INTEGER DEFAULT 0,
    crop INTEGER DEFAULT 0,
    FOREIGN KEY(village_id) REFERENCES village(id)
);

CREATE TABLE IF NOT EXISTS build_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL,
    building TEXT NOT NULL,
    level INTEGER NOT NULL,
    queued_at TEXT NOT NULL,
    FOREIGN KEY(village_id) REFERENCES village(id)
);
