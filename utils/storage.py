import json
import os
from datetime import datetime, timezone

FILE = "saved_jobs.json"
ACTIVITY_FILE = "activity.json"

def load_jobs():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []

def load_activity():
    if not os.path.exists(ACTIVITY_FILE):
        return []
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            activity = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read activity log '{ACTIVITY_FILE}'.") from error
    if not isinstance(activity, list):
        raise RuntimeError(f"Activity log '{ACTIVITY_FILE}' must contain a JSON array.")
    return activity

def record_activity(kind, label, detail="", score=None):
    activity = load_activity()
    event = {
        "kind": kind,
        "label": label,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if score is not None:
        event["score"] = score
    activity.insert(0, event)
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(activity[:100], f, indent=2)

def save_job(job):
    jobs = load_jobs()

    # duplicate (based on job link)
    if any(j.get("link") == job.get("link") for j in jobs):
        return

    jobs.append(job)

    with open(FILE, "w") as f:
        json.dump(jobs, f, indent=2)
    record_activity(
        "job_saved",
        f"Saved {job.get('title', 'a job')}",
        job.get("company", ""),
    )

def remove_job(index):
    jobs = load_jobs()

    if 0 <= index < len(jobs):
        jobs.pop(index)

    with open(FILE, "w") as f:
        json.dump(jobs, f, indent=2)