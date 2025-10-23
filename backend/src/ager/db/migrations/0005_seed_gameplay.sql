-- Seed minimal pour gameplay A7
INSERT OR IGNORE INTO buildings (village_id, building, level) VALUES
  (1, 'lumber_mill', 1),
  (1, 'clay_pit', 1),
  (1, 'iron_mine', 1),
  (1, 'farm', 1);

INSERT OR IGNORE INTO engine_state (village_id, last_tick)
VALUES (1, CURRENT_TIMESTAMP);
