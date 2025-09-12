import os, time, psycopg2, chess.pgn
from pathlib import Path

PGN_DIR = Path(os.getenv("PGN_DIR", "/data/inbox"))
DB_DSN  = os.getenv("DB_DSN", "postgres://postgres:postgres@db:5432/blunderboard")

def process_pgn(path: Path):
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    with open(path, encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            moves_count = len(list(game.mainline_moves()))
            cur.execute(
                "INSERT INTO games (white, black, result, moves_count) VALUES (%s,%s,%s,%s)",
                (
                    game.headers.get("White"),
                    game.headers.get("Black"),
                    game.headers.get("Result"),
                    moves_count,
                ),
            )
    conn.commit()
    cur.close(); conn.close()

def main():
    PGN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[analyzer] watching {PGN_DIR} ...")
    while True:
        for p in PGN_DIR.glob("*.pgn"):
            try:
                print(f"[analyzer] processing {p.name}")
                process_pgn(p)
                p.rename(p.with_suffix(".done"))
                print(f"[analyzer] done {p.name}")
            except Exception as e:
                print(f"[analyzer] ERROR {p.name}: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()
