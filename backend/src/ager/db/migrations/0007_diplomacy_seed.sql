-- Migration 0007: Diplomacy Seed Data (A8)
-- Seeds initial factions and relations for testing

INSERT OR IGNORE INTO factions (id, name, is_player) VALUES
  (1, 'Player', 1),
  (2, 'Empire North', 0),
  (3, 'Guild East', 0);

-- Initialize relations between all faction pairs (a < b)
-- All start as NEUTRAL with opinion=0
INSERT OR IGNORE INTO relations (a, b, stance, opinion, last_updated) VALUES
  (1, 2, 'NEUTRAL', 0, CURRENT_TIMESTAMP),
  (1, 3, 'NEUTRAL', 0, CURRENT_TIMESTAMP),
  (2, 3, 'NEUTRAL', 0, CURRENT_TIMESTAMP);
