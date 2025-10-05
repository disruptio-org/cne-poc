from __future__ import annotations

import json
import logging
import time

from api.app.services.jobs import QUEUE_FILE

from .pipeline import process_job

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _pop_queue() -> list[dict]:
    if not QUEUE_FILE.exists():
        return []
    lines = [line for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    QUEUE_FILE.write_text("", encoding="utf-8")
    return [json.loads(line) for line in lines]


def run_forever(poll_interval: float = 2.0) -> None:
    LOGGER.info("Worker started")
    while True:
        jobs = _pop_queue()
        if not jobs:
            time.sleep(poll_interval)
            continue
        for job in jobs:
            job_id = job["job_id"]
            LOGGER.info("Worker picked job %s", job_id)
            process_job(job_id)


if __name__ == "__main__":
    run_forever()
