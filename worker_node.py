"""
AryaBot Worker Node — v2
========================
An independent, self-contained process that:
  1. Registers itself in MongoDB so the main bot can see it
  2. Publishes a heartbeat every 15s so the main bot knows it's alive
  3. Polls MongoDB job queues (merger, cleaner, multijob, taskjob)
  4. Atomically claims (status: queued → running) to prevent two workers
     from picking the same job
  5. Writes worker_node field on every job it runs
  6. Respects WORKER_TASKS env var so you can pin a worker to specific tasks

Environment Variables:
  WORKER_NAME   — Display name, e.g. "Worker-Node-1"   (default: Worker-Node)
  WORKER_TASKS  — Comma-separated task types to handle  (default: all)
                  e.g. "merger,cleaner"  or  "multijob,taskjob"
  POLL_INTERVAL — Seconds between polls                  (default: 8)

Task Types:
  merger   — Audio/Video Merge jobs  (heavy CPU + RAM + disk)
  cleaner  — Audio Cleaner & Renamer (FFmpeg re-encode)
  multijob — Multi-Job copy/forward  (medium CPU, high bandwidth)
  taskjob  — Single Task jobs        (medium CPU)
"""

import os
import asyncio
import logging
import time
import platform
import uuid
import socket

from bot import Bot
from database import db

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("arya_worker")

# ── Config ───────────────────────────────────────────────────────────────────
WORKER_NAME    = os.environ.get("WORKER_NAME", "Worker-Node")
POLL_INTERVAL  = int(os.environ.get("POLL_INTERVAL", "8"))
HEARTBEAT_INTERVAL = 15   # seconds between heartbeat writes to MongoDB

# Which task types this worker handles. Default = all heavy tasks.
# Set WORKER_TASKS=merger,cleaner to restrict to only those.
_RAW_TASKS = os.environ.get("WORKER_TASKS", "merger,cleaner,multijob,taskjob")
WORKER_TASKS = {t.strip().lower() for t in _RAW_TASKS.split(",") if t.strip()}

# MongoDB collection that tracks live workers
WORKER_COLL = "worker_registry"

# ── Worker Registry Helpers ───────────────────────────────────────────────────
async def _register_worker():
    """Write this worker's info into MongoDB so the main bot can show it."""
    doc = {
        "_id": WORKER_NAME,
        "name": WORKER_NAME,
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "tasks": list(WORKER_TASKS),
        "started_at": time.time(),
        "last_heartbeat": time.time(),
        "status": "online",
        "current_job": None,
        "current_job_type": None,
        "python": platform.python_version(),
        "platform": platform.system(),
    }
    await db.db[WORKER_COLL].replace_one({"_id": WORKER_NAME}, doc, upsert=True)
    logger.info(f"[{WORKER_NAME}] Registered in MongoDB (collection: {WORKER_COLL})")


async def _set_worker_job(job_id, job_type):
    """Update worker's current job in registry."""
    await db.db[WORKER_COLL].update_one(
        {"_id": WORKER_NAME},
        {"$set": {
            "current_job": job_id,
            "current_job_type": job_type,
            "last_heartbeat": time.time(),
        }}
    )


async def _clear_worker_job():
    """Mark worker as idle after job finishes."""
    await db.db[WORKER_COLL].update_one(
        {"_id": WORKER_NAME},
        {"$set": {
            "current_job": None,
            "current_job_type": None,
            "last_heartbeat": time.time(),
        }}
    )


async def _unregister_worker():
    """Called on shutdown — mark as offline."""
    await db.db[WORKER_COLL].update_one(
        {"_id": WORKER_NAME},
        {"$set": {"status": "offline", "current_job": None}}
    )
    logger.info(f"[{WORKER_NAME}] Marked offline in registry.")


async def _heartbeat_loop():
    """Update last_heartbeat every HEARTBEAT_INTERVAL seconds."""
    while True:
        try:
            await db.db[WORKER_COLL].update_one(
                {"_id": WORKER_NAME},
                {"$set": {"last_heartbeat": time.time(), "status": "online"}}
            )
        except Exception as e:
            logger.warning(f"[{WORKER_NAME}] Heartbeat failed: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)


# ── Atomic Job Claimer ────────────────────────────────────────────────────────
async def _claim_job(collection_name: str, job_id: str) -> bool:
    """
    Atomically transition a job from 'queued' → 'running' and tag it with
    this worker's name. Returns True if this worker successfully claimed it,
    False if another worker already claimed it (race condition).
    MongoDB findOneAndUpdate is atomic — only one worker wins.
    """
    result = await db.db[collection_name].find_one_and_update(
        {"job_id": job_id, "status": "queued"},
        {"$set": {
            "status": "running",
            "worker_node": WORKER_NAME,
            "claimed_at": time.time(),
        }},
        return_document=True  # returns the *updated* doc if matched
    )
    return result is not None


# ── Per-Task Runners ──────────────────────────────────────────────────────────

async def _handle_merger(job_id: str, bot):
    from plugins.merger import _mg_run_job, _mg_update_job
    logger.info(f"[{WORKER_NAME}] 🔀 Starting Merger job: {job_id}")
    await _set_worker_job(job_id, "merger")
    try:
        # _mg_run_job internally handles download → merge → upload
        await _mg_run_job(job_id, uid=None, bot=bot)
    except Exception as e:
        logger.error(f"[{WORKER_NAME}] Merger job {job_id} crashed: {e}")
        try:
            await _mg_update_job(job_id, status="error", error=str(e)[:400])
        except Exception:
            pass
    finally:
        await _clear_worker_job()


async def _handle_cleaner(job_id: str, bot):
    from plugins.cleaner import _cl_run_job, _cl_update_job
    logger.info(f"[{WORKER_NAME}] 🧹 Starting Cleaner job: {job_id}")
    await _set_worker_job(job_id, "cleaner")
    try:
        await _cl_run_job(job_id, bot=bot)
    except Exception as e:
        logger.error(f"[{WORKER_NAME}] Cleaner job {job_id} crashed: {e}")
        try:
            await _cl_update_job(job_id, {"status": "failed", "error": str(e)[:400]})
        except Exception:
            pass
    finally:
        await _clear_worker_job()


async def _handle_multijob(job_id: str, bot):
    from plugins.multijob import _mj_run_job, _mj_update_job
    logger.info(f"[{WORKER_NAME}] 📋 Starting MultiJob: {job_id}")
    await _set_worker_job(job_id, "multijob")
    try:
        await _mj_run_job(job_id, bot=bot)
    except AttributeError:
        # multijob may use a different function signature — try fallback
        try:
            from plugins.multijob import run_multijob
            await run_multijob(job_id, bot=bot)
        except Exception as e2:
            logger.error(f"[{WORKER_NAME}] MultiJob {job_id} crashed: {e2}")
    except Exception as e:
        logger.error(f"[{WORKER_NAME}] MultiJob {job_id} crashed: {e}")
        try:
            await _mj_update_job(job_id, {"status": "error", "error": str(e)[:400]})
        except Exception:
            pass
    finally:
        await _clear_worker_job()


async def _handle_taskjob(job_id: str, bot):
    from plugins.taskjob import run_task_job
    logger.info(f"[{WORKER_NAME}] ⚙️ Starting TaskJob: {job_id}")
    await _set_worker_job(job_id, "taskjob")
    try:
        await run_task_job(job_id, bot=bot)
    except Exception as e:
        logger.error(f"[{WORKER_NAME}] TaskJob {job_id} crashed: {e}")
    finally:
        await _clear_worker_job()


# ── Task type → (collection_name, handler, uid_field) ────────────────────────
TASK_MAP = {
    "merger":   ("mergejobs",   _handle_merger),
    "cleaner":  ("cleaner_jobs", _handle_cleaner),
    "multijob": ("multijobs",   _handle_multijob),
    "taskjob":  ("taskjobs",    _handle_taskjob),
}


# ── Main Polling Loop ─────────────────────────────────────────────────────────
async def poll_jobs(bot):
    logger.info(
        f"[{WORKER_NAME}] ▶ Polling started | "
        f"Tasks: {', '.join(sorted(WORKER_TASKS))} | "
        f"Interval: {POLL_INTERVAL}s"
    )

    while True:
        try:
            for task_type, (coll, handler) in TASK_MAP.items():
                if task_type not in WORKER_TASKS:
                    continue

                # Find ONE queued job for this task type
                cursor = db.db[coll].find({"status": "queued"}).sort("created_at", 1).limit(1)
                async for job in cursor:
                    job_id = job.get("job_id")
                    if not job_id:
                        continue

                    # Atomic claim — prevents double-pickup
                    claimed = await _claim_job(coll, job_id)
                    if not claimed:
                        logger.debug(f"[{WORKER_NAME}] Job {job_id} already claimed by another worker.")
                        continue

                    logger.info(f"[{WORKER_NAME}] ✅ Claimed {task_type} job: {job_id}")

                    # Run job in background so polling continues for other task types
                    asyncio.create_task(handler(job_id, bot))

                    # Small delay between picking tasks to avoid overloading
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"[{WORKER_NAME}] Poll loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


# ── Entrypoint ────────────────────────────────────────────────────────────────
async def main():
    logger.info("=" * 60)
    logger.info(f"  AryaBot Worker Node — {WORKER_NAME}")
    logger.info(f"  Host   : {socket.gethostname()}")
    logger.info(f"  PID    : {os.getpid()}")
    logger.info(f"  Tasks  : {', '.join(sorted(WORKER_TASKS))}")
    logger.info(f"  Python : {platform.python_version()}")
    logger.info("=" * 60)

    bot = Bot()
    await bot.start()
    logger.info(f"[{WORKER_NAME}] Bot client started.")

    # Register with MongoDB
    await _register_worker()

    # Start heartbeat loop as concurrent task
    asyncio.create_task(_heartbeat_loop())

    try:
        # Run polling forever
        await poll_jobs(bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info(f"[{WORKER_NAME}] Shutdown signal received.")
    finally:
        await _unregister_worker()
        try:
            await bot.stop()
        except Exception:
            pass
        logger.info(f"[{WORKER_NAME}] Stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
