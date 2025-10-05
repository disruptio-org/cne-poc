# CNE POC Platform

This repository contains a full-stack proof of concept for processing Conselho Nacional de Educação (CNE) documents.

## Services

- **API**: FastAPI backend providing job intake, preview, download, approval, master-data, and model metadata endpoints.
- **Worker**: Background processor that executes the OCR → layout → segmentation → extraction → normalization → validation → CSV pipeline.
- **Web**: React dashboard for uploading documents, reviewing previews, downloading CSV outputs, approving jobs, and inspecting history.
- **Registry**: Lightweight HTTP server exposing model registry artifacts.
- **ML Stack**: Utilities for training, promoting, and generating synthetic datasets from approved jobs.

## Quick start

```bash
make develop  # seeds master data
make api      # start FastAPI on :8000
make worker   # start queue worker
make web      # start React dev server on :5173
```

Alternatively, run everything via Docker:

```bash
docker-compose up --build
```

## Data directories

- `data/incoming/<job_id>/`: raw uploads
- `data/processed/<job_id>/`: preview JSON and UTF-8 CSV outputs
- `data/master/`: master data managed through the API
- `data/state/`: job state, queue, and model registry artifacts

## Scripts

- `scripts/seed_master_data.py`: populate baseline master-data records

## Testing

Run the automated worker pipeline tests locally with:

```bash
make test
```

The suite runs entirely offline using pytest and synthetic fixtures so it can be executed without external services.
