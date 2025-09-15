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