# Blunderboard — Chess Analytics Platform (DevOps/Data Showcase)

A practical, end‑to‑end project that ingests real chess games (PGN), analyzes them, stores results in Postgres, exposes metrics via a FastAPI service, and ships with a production‑grade CI/CD pipeline, monitoring, and dashboards.

---

## What this shows in \~1 minute

**Containerization, orchestration, CI/CD, secrets management, remote deployment, observability.**

* Dockerized multi‑service stack (Docker & Compose)
* GitLab CI/CD: build → test → deploy
* Secrets via CI variables
* Remote deployment via SSH
* Prometheus & Grafana monitoring out of the box

---

## TL;DR (for busy reviewers)

**Stack:** Python (FastAPI, `python-chess`), Postgres, Docker/Compose, GitLab CI/CD, Prometheus, Grafana

**Pipeline:** On push → build & push images → smoke tests → deploy to Ubuntu server via SSH → `docker compose pull && up -d`

**Metrics endpoint:** `GET /metrics` (Prometheus format), e.g. `games_total`, `blunders_total`, `cp_loss_avg`

**Why it matters:** Demonstrates production thinking — immutable images, reproducible deploys, secrets via CI variables, monitoring by default

---

## Architecture (overview)

```
                 +---------------------------+
PGN files  --->  | Analyzer (Python)        |----\
(./data/inbox)   | parses PGN, computes KPIs|     \
                 +---------------------------+      \
                                                     v
                 +---------------------------+   +--------+
                 | API (FastAPI)             |-->| /metrics
                 | exposes metrics & health  |   +--------+
                 +---------------------------+        ^
                         |  DB_DSN                      |
                         v                              |
                 +---------------------------+          |
                 | Postgres (persistent vol) |<---------
                 +---------------------------+

            Prometheus scrapes API:/metrics  |  Grafana dashboards (http://localhost:3000)
```

### Key features

* **Ingestion & analysis:** PGN → Analyzer → Postgres
* **Service boundary:** `api` exposes Prometheus metrics; `analyzer` runs as a separate worker
* **Observability:** Prometheus + Grafana baked in
* **Reproducibility:** Everything via Docker Compose (dev & prod variants)
* **CI/CD:** GitLab pipeline builds, tests, and deploys to a remote Ubuntu server

### Tech highlights (what I practiced)

* **Docker & Compose:** multi‑service stack, volumes, health/`depends_on`
* **GitLab CI/CD:**

  * build images for `api` & `analyzer` and push to GitLab Container Registry
  * SSH deploy: `rsync` compose/configs → registry login → `compose pull` → `compose up -d`
* **Secrets & config:** environment via GitLab CI variables; DB password not stored in repo
* **Monitoring:** Prometheus scrape of `/metrics`; Grafana dashboards

---

## Quickstart (local, dev)

**Prereqs:** Docker Desktop / Docker Engine + Compose plugin.

```bash
# in repo root
docker compose up -d

# API metrics
curl http://localhost:8000/metrics

# Prometheus UI
open http://localhost:9090

# Grafana UI (login on first run)
open http://localhost:3000
```

**PGN ingestion:** drop `.pgn` files into `./data/inbox/`. The analyzer picks them up and writes results to Postgres.

---

## Production deployment (how I ship)

* **Images:** Built in CI and pushed to GitLab Container Registry
* **Host:** Ubuntu server with Docker + Compose
* **Deploy job:**

  1. Copy `docker-compose.prod.yml` and config (`monitoring/`, `db/`) via `rsync/scp`
  2. Write `.env` on server (injects `API_IMAGE`, `ANALYZER_IMAGE`, `POSTGRES_PASSWORD`)
  3. `docker login` to registry (stdin password)
  4. `docker compose -f docker-compose.prod.yml pull && up -d`

### Compose (prod) excerpt

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: blunderboard
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db:/docker-entrypoint-initdb.d:ro

  api:
    image: ${API_IMAGE}:latest
    environment:
      DB_DSN: postgres://postgres:${POSTGRES_PASSWORD}@db:5432/blunderboard
      PGN_INBOX: /data/inbox
    volumes: [ "./data/inbox:/data/inbox" ]
    ports: [ "8000:8000" ]
    depends_on: [ db ]

  analyzer:
    image: ${ANALYZER_IMAGE}:latest
    environment:
      DB_DSN: postgres://postgres:${POSTGRES_PASSWORD}@db:5432/blunderboard
      PGN_DIR: /data/inbox
    volumes: [ "./data/inbox:/data/inbox" ]
    depends_on: [ db ]

  prometheus:
    image: prom/prometheus
    volumes: [ "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro" ]
    ports: [ "9090:9090" ]
    depends_on: [ api ]

  grafana:
    image: grafana/grafana
    ports: [ "3000:3000" ]
    depends_on: [ prometheus ]

volumes:
  pgdata:
```

---

## CI/CD pipeline (GitLab)

**Stages:** `build` → `test` → `deploy`

* **build**

  * `docker build -t $CI_REGISTRY_IMAGE/api:<sha> api/`
  * `docker build -t $CI_REGISTRY_IMAGE/analyzer:<sha> analyzer/`
  * push both; optionally tag `:main` for stable

* **deploy**

  * SSH to server (key via masked CI variable)
  * `rsync` compose/configs
  * write `.env`
  * `docker compose pull && up -d`

**Secrets (masked CI variables):** `SSH_PRIVATE_KEY`, `POSTGRES_PASSWORD`, and registry creds via `CI_REGISTRY_*`.

---

## Repository structure

```
blunderboard/
├─ api/                    # FastAPI service exposing /metrics
├─ analyzer/               # PGN ingestion & analysis worker
├─ monitoring/
│  └─ prometheus.yml       # Prom scrape config
├─ db/                     # optional init/migration scripts
├─ data/
│  └─ inbox/               # drop PGNs here (bind mount)
├─ docker-compose.yml      # dev stack
├─ docker-compose.prod.yml # prod stack (images from registry)
└─ .gitlab-ci.yml          # CI/CD pipeline (GitLab)
```

---

## Security & data

* No secrets in repo — DB password & SSH key via masked CI variables
* SSH with keys — no password logins in deploy
* Volumes — DB data persists via `pgdata` (prod data is not synced from dev)
* Registry login — `--password-stdin` to avoid secrets in logs

---

## Roadmap (short)

* Extend `pytest` coverage (PGN parsing, API, analyzer workflows)
* Implement user-facing analytics in Looker Studio (Google Data Studio) or Power BI
* Basic Grafana dashboard provisioning
* Optional: nightly analysis job & lightweight caching layer
* Optional: promote `:main` vs `:<sha>` rollout strategy

---

## How to read this as a reviewer

* Look at `.gitlab-ci.yml` for the CI/CD pipeline design
* Skim `docker-compose.prod.yml` for production orchestration
* Hit `api/` to see how metrics are exposed; `analyzer/` for ingestion logic
* Open `monitoring/prometheus.yml` to see the scrape config

---

*This project is built as a hands‑on demonstration of DevOps/Data engineering fundamentals with real services, real deploys, and real monitoring.*
