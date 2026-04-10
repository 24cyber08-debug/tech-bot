"""
Tech Bot — FastAPI entrypoint.
POST /run  → run selected agents (planner, executor, verifier or any combo)
GET  /health, /history
"""
import time
import uuid
import json
import os
from collections import deque
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
from agents import plan as run_plan, execute, verify

app = FastAPI(title="Tech Bot", version="2.0.0")

_history: deque = deque(maxlen=20)

COST_PER_1K_INPUT  = 0.0002
COST_PER_1K_OUTPUT = 0.0006
MAX_TASK_LENGTH    = 500


class TaskRequest(BaseModel):
    task: str = ""
    parallel: bool = True
    agents: List[str] = ["planner", "executor", "verifier"]
    plan: Optional[dict] = None
    execution: Optional[list] = None

    @field_validator("task")
    @classmethod
    def validate_task(cls, v):
        v = v.strip()
        if len(v) > MAX_TASK_LENGTH:
            raise ValueError(f"Task too long ({len(v)} chars). Max {MAX_TASK_LENGTH}.")
        return v

    @field_validator("agents")
    @classmethod
    def validate_agents(cls, v):
        valid = {"planner", "executor", "verifier"}
        for a in v:
            if a.lower() not in valid:
                raise ValueError(f"Invalid agent '{a}'. Choose from: {valid}")
        return [a.lower() for a in v]


def _estimate_cost(text: str, is_output: bool = False) -> float:
    tokens = len(text.split()) * 1.33
    rate   = COST_PER_1K_OUTPUT if is_output else COST_PER_1K_INPUT
    return round((tokens / 1000) * rate, 6)


@app.on_event("startup")
def startup_check():
    key = os.getenv("MISTRAL_API_KEY", "")
    if not key:
        print("WARNING: MISTRAL_API_KEY is not set.")
    else:
        print(f"Tech Bot v2.0.0 started. Key loaded ({key[:6]}...)")


@app.post("/run")
async def run_task(req: TaskRequest):
    run_id     = str(uuid.uuid4())[:8]
    started_at = time.time()
    timeline   = []
    total_cost = 0.0

    def record(event, data=None):
        timeline.append({
            "event": event,
            "t": round(time.time() - started_at, 3),
            **(data or {})
        })

    agents_to_run = req.agents
    response = {"run_id": run_id, "task": req.task, "agents_run": agents_to_run}

    try:
        plan_result  = None
        exec_results = None
        final        = None

        # ── PLANNER ───────────────────────────────────────────────────────
        if "planner" in agents_to_run:
            if not req.task:
                raise ValueError("Task is required when running the Planner.")
            record("planner_start")
            plan_result = run_plan(req.task)
            record("planner_done", {"steps": len(plan_result.get("steps", []))})
            total_cost += _estimate_cost(req.task) + _estimate_cost(
                json.dumps(plan_result), is_output=True
            )
            response["plan"] = plan_result

        # ── EXECUTOR ──────────────────────────────────────────────────────
        if "executor" in agents_to_run:
            # Use Planner output if available, otherwise use req.plan directly
            if plan_result is not None:
                active_plan = plan_result
            elif req.plan is not None:
                active_plan = req.plan
                plan_result = req.plan
                response["plan"] = active_plan
            else:
                raise ValueError(
                    "Executor needs a plan. "
                    "Either include 'planner' in agents, or provide a JSON plan."
                )

            record("executor_start", {"parallel": req.parallel})
            exec_results = execute(active_plan, parallel=req.parallel)
            successes    = sum(1 for r in exec_results if r["status"] == "success")
            record("executor_done", {"successes": successes})
            total_cost  += _estimate_cost(json.dumps(exec_results))
            response["execution"] = exec_results

        # ── VERIFIER ──────────────────────────────────────────────────────
        if "verifier" in agents_to_run:
            if plan_result is None:
                plan_result = req.plan
            if exec_results is None:
                exec_results = req.execution

            if plan_result is None or exec_results is None:
                raise ValueError(
                    "Verifier needs both Planner and Executor results."
                )
            record("verifier_start")
            final = verify(req.task, plan_result, exec_results)
            record("verifier_done", {"verified": final.get("verified")})
            total_cost += _estimate_cost(json.dumps(final), is_output=True)
            response["answer"] = final

        elapsed = round(time.time() - started_at, 3)
        response["meta"] = {
            "elapsed_sec":        elapsed,
            "estimated_cost_usd": round(total_cost, 6),
            "parallel":           req.parallel,
            "agents_run":         agents_to_run,
            "timeline":           timeline,
        }

        _history.appendleft({
            "run_id":             run_id,
            "task":               req.task or "executor-only",
            "verified":           final.get("verified") if final else None,
            "elapsed_sec":        elapsed,
            "estimated_cost_usd": round(total_cost, 6),
            "agents_run":         agents_to_run,
            "timestamp":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "run_id": run_id})
    except Exception as e:
        elapsed = round(time.time() - started_at, 3)
        _history.appendleft({
            "run_id":    run_id,
            "task":      req.task or "executor-only",
            "verified":  False,
            "error":     str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        raise HTTPException(status_code=500, detail={
            "error":  str(e),
            "run_id": run_id,
            "meta":   {"elapsed_sec": elapsed, "timeline": timeline},
        })


@app.get("/health")
def health():
    return {
        "status":           "ok",
        "version":          "2.0.0",
        "name":             "Tech Bot",
        "mistral_key_set":  bool(os.getenv("MISTRAL_API_KEY", "")),
        "available_agents": ["planner", "executor", "verifier"],
    }


@app.get("/history")
def history():
    return {"runs": list(_history)}


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    index = os.path.join(static_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Tech Bot API — POST /run to execute a task"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
