from fastapi import FastAPI, UploadFile, File
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import psycopg2, os, shutil, uuid, time 

DB_DSN   = os.getenv("DB_DSN", "postgres://postgres:postgres@db:5432/blunderboard")
INBOX    = os.getenv("PGN_INBOX", "/data/inbox")

app = FastAPI()


g_games       = Gauge("games_total", "Total games analyzed")
g_moves       = Gauge("moves_total", "Total moves across all games")
g_blunders    = Gauge("blunders_total", "Total blunders across all games")
g_cpavg       = Gauge("cp_loss_avg", "Average centipawn loss across all moves")
g_last_scrape = Gauge("metrics_last_scrape_timestamp", "Unix ts of last metrics scrape")

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

    #Basis
    cur.execute("SELECT COUNT(*), COALESCE(SUM(moves_count),0) FROM games")
    games, moves = cur.fetchone()
    g_games.set(games); g_moves.set(moves)

    # Blunders total
    cur.execute("SELECT COALESCE(COUNT(*),0) FROM moves WHERE tag='blunder'")
    blunders = cur.fetchone()[0]
    g_blunders.set(blunders)

    # cp loss avg (über alle Züge)
    cur.execute("SELECT COALESCE(AVG(cp_loss),0) FROM moves")
    cpavg = float(cur.fetchone()[0] or 0.0)
    g_cpavg.set(cpavg)

    cur.close(); conn.close()
    g_last_scrape.set(time.time())
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)