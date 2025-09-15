FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends stockfish && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY analyze_pgn.py .
ENV ENGINE_DEPTH=12
ENV PYTHONUNBUFFERED=1
CMD ["python","analyze_pgn.py"]