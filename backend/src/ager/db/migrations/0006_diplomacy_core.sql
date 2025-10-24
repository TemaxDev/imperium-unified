-- Migration 0006: Diplomacy Core Tables (A8)
-- Creates factions, relations, treaties, and events tables for AI diplomacy system

CREATE TABLE IF NOT EXISTS factions (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  is_player INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relations (
  a INTEGER NOT NULL,
  b INTEGER NOT NULL,
  stance TEXT NOT NULL DEFAULT 'NEUTRAL',
  opinion REAL NOT NULL DEFAULT 0,
  last_updated TEXT NOT NULL,
  PRIMARY KEY (a, b),
  FOREIGN KEY (a) REFERENCES factions(id),
  FOREIGN KEY (b) REFERENCES factions(id),
  CHECK (a < b)
);

CREATE TABLE IF NOT EXISTS treaties (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  a INTEGER NOT NULL,
  b INTEGER NOT NULL,
  type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  started_at TEXT NOT NULL,
  expires_at TEXT,
  FOREIGN KEY (a) REFERENCES factions(id),
  FOREIGN KEY (b) REFERENCES factions(id),
  CHECK (a < b)
);

CREATE TABLE IF NOT EXISTS diplomacy_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  ts TEXT NOT NULL
);
