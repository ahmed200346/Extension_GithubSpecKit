import time

PIPELINE_PROGRESS = {
    "current_agent": None,
    "completed_agents": [],
    "total_agents": 6,
    "started_at": None,
    "elapsed_seconds": 0,
    "status": "idle",
    "agent_timings": {}
}

AGENT_ORDER = ["parsing", "summary", "glossary", "diagram", "doc_writer", "layout"]


def report_agent_start(agent_name: str):
    PIPELINE_PROGRESS["current_agent"] = agent_name
    PIPELINE_PROGRESS["status"] = "running"
    PIPELINE_PROGRESS["agent_timings"][agent_name] = {
        "started_at": time.time(),
        "elapsed": 0,
        "status": "running"
    }
    print(f"[📊 PROGRESS] {agent_name} started | {len(PIPELINE_PROGRESS['completed_agents'])}/{PIPELINE_PROGRESS['total_agents']} done", flush=True)


def report_agent_done(agent_name: str):
    if agent_name not in PIPELINE_PROGRESS["completed_agents"]:
        PIPELINE_PROGRESS["completed_agents"].append(agent_name)
    t = PIPELINE_PROGRESS["agent_timings"].get(agent_name, {})
    if t.get("started_at"):
        t["elapsed"] = round(time.time() - t["started_at"], 1)
    t["status"] = "done"
    PIPELINE_PROGRESS["agent_timings"][agent_name] = t
    PIPELINE_PROGRESS["current_agent"] = None
    done = len(PIPELINE_PROGRESS["completed_agents"])
    total = PIPELINE_PROGRESS["total_agents"]
    elapsed = round(time.time() - PIPELINE_PROGRESS["started_at"], 1) if PIPELINE_PROGRESS["started_at"] else 0
    print(f"[📊 PROGRESS] {agent_name} DONE in {t['elapsed']}s | {done}/{total} ({done/total*100:.0f}%) | {elapsed:.0f}s total", flush=True)
