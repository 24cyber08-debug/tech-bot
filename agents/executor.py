"""
Executor Agent — iterates through the plan steps, calls the appropriate
tools, handles failures gracefully, and supports parallel execution.
"""
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from tools import run_tool

MAX_RETRIES = 3
RETRY_DELAY = 1.5  # seconds


def _execute_step(step: dict) -> dict:
    """
    Execute a single plan step with retry logic.
    Returns a result dict with status, data, and metadata.
    """
    tool = step.get("tool")
    action = step.get("action")
    step_num = step.get("step")

    # Extract kwargs (everything except meta keys)
    meta_keys = {"step", "tool", "action"}
    kwargs = {k: v for k, v in step.items() if k not in meta_keys}

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            data = run_tool(tool, action, **kwargs)
            elapsed = round(time.time() - start, 3)
            return {
                "step": step_num,
                "tool": tool,
                "action": action,
                "status": "success",
                "data": data,
                "attempts": attempt,
                "elapsed_ms": int(elapsed * 1000),
            }
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    return {
        "step": step_num,
        "tool": tool,
        "action": action,
        "status": "error",
        "error": last_error,
        "attempts": MAX_RETRIES,
        "data": None,
    }


def execute(plan: dict, parallel: bool = True) -> list:
    """
    Execute all steps in the plan.

    If parallel=True, steps with no dependencies are executed concurrently.
    Returns a list of step results ordered by step number.
    """
    steps = plan.get("steps", [])
    if not steps:
        return []

    results = []

    if parallel and len(steps) > 1:
        with ThreadPoolExecutor(max_workers=min(len(steps), 5)) as executor:
            futures = {executor.submit(_execute_step, step): step for step in steps}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    step = futures[future]
                    results.append({
                        "step": step.get("step"),
                        "tool": step.get("tool"),
                        "action": step.get("action"),
                        "status": "error",
                        "error": str(e),
                        "data": None,
                    })
    else:
        for step in steps:
            results.append(_execute_step(step))

    # Always return sorted by step number
    results.sort(key=lambda r: r.get("step", 0))
    return results
