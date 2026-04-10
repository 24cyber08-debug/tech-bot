"""
Verifier Agent — Tech Bot
Req 3 implementation:
  - Independently re-fetches data using the same tools as Executor
  - Compares re-fetched data with Executor results
  - Checks every plan step was executed properly
  - Reports exactly where Planner or Executor failed
  - 3-level verification: planner check, executor check, relevance check
"""
import json
from llm import call_llm
from tools import run_tool

VERIFIER_SYSTEM = """
You are the Verifier Agent for Tech Bot — an AI Operations Assistant.

You receive:
1. The original user task
2. The execution plan produced by the Planner
3. Results produced by the Executor
4. Results independently re-fetched by the Verifier (ground truth)

Your job — verify at THREE levels:

LEVEL 1 — PLANNER CHECK:
- Did the Planner break the task into the correct steps?
- Were the right tools chosen for each step?
- Were the parameters correct (right city, right query, right limit)?
- Report any planning mistakes.

LEVEL 2 — EXECUTOR CHECK:
- Did the Executor run every step in the plan?
- Did any step fail or time out?
- Compare Executor data vs Verifier re-fetched data:
  * Are values roughly the same? (small differences OK for live data)
  * Are there major discrepancies? (different city, completely different data)
- Report exactly which step failed and why.

LEVEL 3 — TASK RELEVANCE CHECK:
- Does the final combined result actually answer the user's original task?
- Is any part of the task unanswered?

Output ONLY valid JSON. No markdown, no preamble.

SCHEMA:
{
  "summary": "<2-3 sentence answer to the user task>",
  "results": { "<key>": <data> },
  "verified": true | false,
  "confidence_score": <0-100>,
  "level1_planner": {
    "passed": true|false,
    "steps_checked": <int>,
    "issues": []
  },
  "level2_executor": {
    "passed": true|false,
    "steps_checked": <int>,
    "failed_steps": [{"step": <int>, "tool": "<tool>", "reason": "<why>"}],
    "data_matches": [{"step": <int>, "match": true|false, "note": "<detail>"}],
    "issues": []
  },
  "level3_relevance": {
    "passed": true|false,
    "issues": []
  },
  "issues": [],
  "retry_suggestions": [],
  "total_steps": <int>,
  "successful_steps": <int>
}
"""


def _re_fetch_step(step: dict) -> dict:
    """Independently re-fetch data for one plan step — Verifier's own ground truth."""
    tool     = step.get("tool")
    action   = step.get("action")
    step_num = step.get("step")
    kwargs   = {k: v for k, v in step.items() if k not in {"step", "tool", "action"}}
    try:
        data = run_tool(tool, action, **kwargs)
        return {"step": step_num, "tool": tool, "action": action, "status": "success", "data": data}
    except Exception as e:
        return {"step": step_num, "tool": tool, "action": action, "status": "error", "error": str(e), "data": None}


def _check_shape(execution_results: list) -> dict:
    issues = []
    for r in execution_results:
        if r.get("status") != "success":
            issues.append(f"Step {r['step']} ({r['tool']}.{r['action']}) failed: {r.get('error')}")
            continue
        data = r.get("data")
        if data is None:
            issues.append(f"Step {r['step']} returned no data.")
        elif isinstance(data, list) and len(data) == 0:
            issues.append(f"Step {r['step']} returned empty list.")
        elif isinstance(data, dict) and len(data) == 0:
            issues.append(f"Step {r['step']} returned empty object.")
    return {"passed": len(issues) == 0, "issues": issues}


def _check_values(execution_results: list) -> dict:
    issues = []
    for r in execution_results:
        if r.get("status") != "success":
            continue
        tool = r.get("tool", "")
        data = r.get("data")
        if tool == "WeatherTool" and isinstance(data, dict):
            try:
                temp = float(data.get("temperature", "0").replace("°C", "").replace("°F", ""))
                if not (-90 <= temp <= 60):
                    issues.append(f"Step {r['step']}: temperature {temp} looks unrealistic.")
            except Exception:
                issues.append(f"Step {r['step']}: could not parse temperature.")
            if not data.get("city"):
                issues.append(f"Step {r['step']}: city name missing.")
        elif tool == "GitHubTool" and isinstance(data, list):
            for repo in data:
                if "/" not in repo.get("name", ""):
                    issues.append(f"Step {r['step']}: repo '{repo.get('name')}' looks invalid.")
        elif tool == "FactsTool" and isinstance(data, list):
            for fact in data:
                if len(fact.get("fact", "")) < 10:
                    issues.append(f"Step {r['step']}: fact too short.")
    return {"passed": len(issues) == 0, "issues": issues}


def _trim(results: list) -> list:
    trimmed = []
    for r in results:
        entry = {"step": r.get("step"), "tool": r.get("tool"), "action": r.get("action"), "status": r.get("status")}
        if r.get("status") == "success":
            data = r.get("data")
            if isinstance(data, list):
                entry["data_preview"] = data[:2]
                entry["total_items"]  = len(data)
            elif isinstance(data, dict):
                entry["data"] = data
        else:
            entry["error"] = r.get("error", "Unknown error")
        trimmed.append(entry)
    return trimmed


def verify(task: str, plan: dict, execution_results: list) -> dict:
    steps     = plan.get("steps", [])
    total     = len(execution_results)
    successes = sum(1 for r in execution_results if r.get("status") == "success")
    failures  = [r for r in execution_results if r.get("status") != "success"]

    shape_check = _check_shape(execution_results)
    value_check = _check_values(execution_results)

    # ── Re-fetch all steps independently ──────────────────────────────────
    re_fetched   = [_re_fetch_step(step) for step in steps]
    re_fetch_ok  = sum(1 for r in re_fetched if r.get("status") == "success")

    prompt = f"""{VERIFIER_SYSTEM}

Original task: {task}

Planner plan:
{json.dumps(plan, indent=2)}

Executor results:
{json.dumps(_trim(execution_results), indent=2)}

Verifier re-fetched results (independent ground truth):
{json.dumps(_trim(re_fetched), indent=2)}

Pre-computed:
- Steps planned: {len(steps)}
- Executor succeeded: {successes}/{total}
- Verifier re-fetch succeeded: {re_fetch_ok}/{len(steps)}
- Shape issues: {shape_check["issues"]}
- Value issues: {value_check["issues"]}

Compare Executor vs Verifier data. Report discrepancies step by step.
"""

    raw    = call_llm(prompt, expect_json=True)
    result = json.loads(raw)

    result["level1_planner"]  = result.get("level1_planner", {
        "passed": len(steps) > 0, "steps_checked": len(steps),
        "issues": [] if steps else ["Planner returned 0 steps."]
    })
    result["level2_executor"] = result.get("level2_executor", {
        "passed": successes == total, "steps_checked": total,
        "failed_steps": [{"step": r["step"], "tool": r["tool"], "reason": r.get("error")} for r in failures],
        "data_matches": [], "issues": shape_check["issues"] + value_check["issues"]
    })
    result["level3_relevance"] = result.get("level3_relevance", {
        "passed": successes == total, "issues": []
    })

    result.setdefault("verified", successes == total and shape_check["passed"] and value_check["passed"])
    result.setdefault("confidence_score", int(successes / total * 100) if total > 0 else 0)
    result.setdefault("total_steps", total)
    result.setdefault("successful_steps", successes)
    result.setdefault("issues", [f"Step {r['step']} ({r['tool']}.{r['action']}) failed: {r.get('error')}" for r in failures])
    result.setdefault("retry_suggestions", [f"Retry step {r['step']} ({r['tool']}.{r['action']})" for r in failures])
    result.setdefault("summary", "Task completed." if successes == total else f"{successes}/{total} steps succeeded.")
    result["verifier_re_fetch"] = _trim(re_fetched)

    return result