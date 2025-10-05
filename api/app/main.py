import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import jobs, preview, downloads, approval, master_data, model_metadata
from .services.metrics import MetricsService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(title="CNE Processing API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics = MetricsService.get_instance()

@app.on_event("startup")
async def startup_event() -> None:
    metrics.set_gauge("api.startup", 1)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    metrics.set_gauge("api.startup", 0)

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(preview.router, prefix="/preview", tags=["preview"])
app.include_router(downloads.router, prefix="/download", tags=["download"])
app.include_router(approval.router, prefix="/approval", tags=["approval"])
app.include_router(master_data.router, prefix="/master-data", tags=["master-data"])
app.include_router(model_metadata.router, prefix="/models", tags=["models"])


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    metrics.increment("api.healthcheck")
    return {"status": "ok"}
