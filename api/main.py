from fastapi import FastAPI, UploadFile, File
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import psycopg2, os, shutil, uuid

DB_DSN   = os.getenv("DB_DSN", "postgres://postgres:postgres@db:5432/blunderboard")
INBOX    = os.getenv("PGN_INBOX", "/data/inbox")

app = FastAPI()


g_games = Gauge("games_total", "Total games analyzed")
g_moves = Gauge("moves_total", "Total moves across all games")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/upload_pgn")
async def upload_pgn(f: UploadFile = File(...)):
    os.makedirs(INBOX, exist_ok=True)
    fn = f"{uuid.uuid4()}.pgn"
    with open(os.path.join(INBOX, fn), "wb") as out:
        shutil.copyfileobj(f.file, out)
    return {"ok": True, "file": fn}

@app.get("/metrics")
def metrics():
    conn = psycopg2.connect(DB_DSN); cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(SUM(moves_count),0) FROM games")
    games, moves = cur.fetchone()
    cur.close(); conn.close()
    g_games.set(games)
    g_moves.set(moves)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)