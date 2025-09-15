CREATE TABLE IF NOT EXISTS games (
  id SERIAL PRIMARY KEY,
  white TEXT,
  black TEXT,
  result VARCHAR(8),
  moves_count INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Details pro Zug
CREATE TABLE IF NOT EXISTS moves (
  id SERIAL PRIMARY KEY,
  game_id INT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  ply INT NOT NULL,                      -- Halbzugnummer (1..)
  san TEXT,                              -- SAN-Notation
  color CHAR(1) CHECK (color IN ('w','b')),
  phase VARCHAR(12),                     -- opening | middle | end
  cp_before INT,                         -- Bewertung vor dem Zug (cp, aus Sicht des Spielers am Zug)
  cp_after INT,                          -- Bewertung nach dem Zug (cp, aus Sicht desselben Spielers)
  cp_loss INT,                           -- max(0, cp_before - cp_after)
  tag VARCHAR(16)                        -- ok | inaccuracy | mistake | blunder
);

-- Aggregierte Sicht je Partie 
CREATE MATERIALIZED VIEW IF NOT EXISTS analysis_summary AS
SELECT
  g.id AS game_id,
  AVG(m.cp_loss) AS avg_cploss,
  SUM(CASE WHEN m.tag='blunder' THEN 1 ELSE 0 END) AS blunders,
  SUM(CASE WHEN m.tag='mistake' THEN 1 ELSE 0 END) AS mistakes,
  SUM(CASE WHEN m.tag='inaccuracy' THEN 1 ELSE 0 END) AS inaccuracies
FROM games g JOIN moves m ON m.game_id = g.id
GROUP BY g.id;

-- Indexe (Performance)
CREATE INDEX IF NOT EXISTS idx_moves_game ON moves(game_id);
CREATE INDEX IF NOT EXISTS idx_moves_tag ON moves(tag);