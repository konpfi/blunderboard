import os, time, psycopg2, chess.pgn, chess.engine
from pathlib import Path

PGN_DIR = Path(os.getenv("PGN_DIR", "/data/inbox"))
DB_DSN  = os.getenv("DB_DSN", "postgres://postgres:postgres@db:5432/blunderboard")
ENGINE_PATH = os.getenv("ENGINE_PATH", "/usr/games/stockfish")  # apt install path
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "12"))

# Schwellen in Centipawns
INACCURACY, MISTAKE, BLUNDER = 50, 100, 300

def phase_by_ply(ply: int, total_moves: int) -> str:
    # simple Heuristik: erste 10 Halbzüge Eröffnung, letzte 12 Endspiel
    if ply <= 10: return "opening"
    if ply >= max(1, total_moves*2 - 12): return "end"
    return "middle"

def tag_of(cp_loss: int) -> str:
    if cp_loss >= BLUNDER: return "blunder"
    if cp_loss >= MISTAKE: return "mistake"
    if cp_loss >= INACCURACY: return "inaccuracy"
    return "ok"

def analyze_game(cur, engine, game):
    board = game.board()
    main_moves = list(game.mainline_moves())
    total_ply = len(main_moves)

    # Spielstammdaten
    cur.execute("""INSERT INTO games (white, black, result, moves_count)
                   VALUES (%s,%s,%s,%s) RETURNING id""",
                (game.headers.get("White"),
                 game.headers.get("Black"),
                 game.headers.get("Result"),
                 total_ply))
    game_id = cur.fetchone()[0]

    # Eval vor Start: aus Sicht des Spielers am Zug (board.turn)
    info = engine.analyse(board, chess.engine.Limit(depth=ENGINE_DEPTH))
    eval_prev = info["score"].pov(board.turn).score(mate_score=100000) or 0

    ply = 0
    for mv in main_moves:
        mover_color = 'w' if board.turn == chess.WHITE else 'b'

        san_str = board.san(mv)

        board.push(mv)
        ply += 1

        # Nach dem Zug ist die Seite am Zug gewechselt.
        # Wir wollen die Bewertung AUS SICHT DES SPIELERS, der den Zug gemacht hat.
        info = engine.analyse(board, chess.engine.Limit(depth=ENGINE_DEPTH))
        eval_now = info["score"].pov(not board.turn).score(mate_score=100000) or 0

        cp_loss = max(0, int(eval_prev) - int(eval_now))
        cur.execute(
            """INSERT INTO moves (game_id, ply, san, color, phase, cp_before, cp_after, cp_loss, tag)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (game_id, ply, san_str, mover_color,
             phase_by_ply(ply, total_ply),
             int(eval_prev), int(eval_now), int(cp_loss), tag_of(cp_loss))
        )

        eval_prev = eval_now

def process_pgn(path: Path):
    with open(path, encoding="utf-8") as f:
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                analyze_game(cur, engine, game)
        conn.commit()
        cur.close(); conn.close()

def main():
    PGN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[analyzer] watching {PGN_DIR} (depth={ENGINE_DEPTH})")
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
