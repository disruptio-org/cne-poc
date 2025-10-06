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

### End-to-end local test flow

1. **Prepare Python & Node tooling**
   - Create and activate a virtualenv (`python -m venv .venv && source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\Activate.ps1` in PowerShell after `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`).
   - Install dependencies with `pip install -r requirements.txt` and `npm install` under `web/`.
   - On Windows, install `make` via Chocolatey (`choco install make`) or use Git Bash/WSL where it is preinstalled.

2. **Seed master data**
   - Run `make develop` to invoke `scripts/seed_master_data.py`, which populates `data/master/` and prints a reminder of the next steps.

3. **Start services (separate terminals)**
   - `make api` launches the FastAPI backend on port 8000 (`api/app/main.py`).
   - `make worker` runs the offline processing pipeline that watches queued jobs and writes previews/CSVs under `data/processed/`.
   - `make web` boots the React dev server with Vite on port 5173 (hot-reloads the UI for upload/preview/approval).
   - Optional: `make registry` exposes the model registry JSON via `http.server` on port 9000.

4. **Exercise the workflow through the UI**
   - Open `http://localhost:5173`, upload a sample document (PDF/DOCX/XLSX/ZIP), and wait for the worker to process it.
   - Review validation badges (`OK/AVISO/ERRO`) and OCR confidence mean pulled from `preview.json` (`worker/src/pipeline.py`).
   - Download the generated CSV and click **Aprovar** to trigger approval; the API copies artifacts to `data/approved/<YYYY-MM-DD>/<job_id>/` and records the job in the registry (`api/app/services/jobs.py`).

5. **Trigger retraining manually (optional)**
   - Execute `python -c "from ml.training import train; train()"` to build a corpus from approved CSVs (semicolon delimited, 10-column contract) and register metrics for the new dataset.
   - Promotion helpers live in `ml/promotion.py`; invoke functions such as `evaluate_and_promote(version)` from a Python shell once you have candidate versions recorded in the registry.

6. **Automated checks**
   - Run `make test` to execute the pytest suite that validates the worker pipeline, approval artifact materialization, and registry bookkeeping.

### Python environment notes

- Install dependencies into a virtual environment with `pip install -r requirements.txt` before running the Make targets.
- Ensure the upstream [`pydantic`](https://pydantic.dev/) package is available; avoid creating a local module named `pydantic/` inside the repo because it will shadow the dependency that FastAPI imports at runtime.

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
