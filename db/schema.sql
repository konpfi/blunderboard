CREATE TABLE IF NOT EXISTS games (
  id SERIAL PRIMARY KEY,
  white TEXT,
  black TEXT,
  result VARCHAR(8),
  moves_count INT,
  created_at TIMESTAMPTZ DEFAULT now()
);