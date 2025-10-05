FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY worker ./worker
COPY data ./data

ENV PYTHONPATH=/app

CMD ["python", "-m", "worker.src.worker"]
