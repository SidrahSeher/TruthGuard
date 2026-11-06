import logging
import threading
import time
import uuid

log = logging.getLogger("truthguard")

JOBS = {}
_LOCK = threading.Lock()
MAX_JOBS = 50
GENERIC_ERROR = "The verification failed. Check the backend window for details."


class JobBusy(Exception):
    """Another verification is already running."""


def start_job(function, *args) -> str:
    """Run function(*args, progress=...) in the background. Only one job at a time."""
    with _LOCK:
        if any(j["status"] == "running" for j in JOBS.values()):
            raise JobBusy()
        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id, "status": "running", "stage": "Starting", "steps": [],
            "result": None, "error": None, "started": time.time(), "finished": None,
        }
        JOBS[job_id] = job
        while len(JOBS) > MAX_JOBS:
            del JOBS[next(iter(JOBS))]      # drop the oldest job

    def progress(stage, steps=None):
        with _LOCK:
            job["stage"] = stage
            if steps is not None:
                job["steps"] = steps

    def worker():
        try:
            result = function(*args, progress=progress)
            with _LOCK:
                job.update(status="done", stage="Done", result=result, finished=time.time())
        except ValueError as error:          # a clear input problem, safe to show
            with _LOCK:
                job.update(status="error", error=str(error), finished=time.time())
        except Exception:
            log.exception("Verification job failed")
            with _LOCK:
                job.update(status="error", error=GENERIC_ERROR, finished=time.time())

    threading.Thread(target=worker, daemon=True).start()
    return job_id


def get_job(job_id: str):
    with _LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return None
        snapshot = dict(job)
    snapshot["elapsed"] = round((snapshot["finished"] or time.time()) - snapshot["started"], 1)
    return snapshot