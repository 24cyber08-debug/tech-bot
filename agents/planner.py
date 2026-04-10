"""
Planner Agent — receives a natural-language task and produces a
structured JSON execution plan using Mistral.
"""
import json
from llm import call_llm

PLANNER_SYSTEM = """
You are the Planner Agent for an AI Operations Assistant.

Your ONLY job is to convert a user's natural-language task into a structured JSON execution plan.

GitHubTool
  • search_repos(query: str, sort: str = "stars", limit: int = 3)
      → search repositories by keyword/language
  • trending_repos(language: str = "", limit: int = 3)
      → repos with most stars created in last 7 days
  • get_repo(owner: str, repo: str)
      → details for a specific repo (stars, forks, issues)

WeatherTool
  • get_weather(city: str, units: str = "metric")
      → current temperature, condition, wind speed
  • get_forecast(city: str, days: int = 3, units: str = "metric")
      → day-by-day forecast

FactsTool
  • get_facts(limit: int = 5)
      → list of interesting facts
  • get_fact()
      → one random interesting fact

AbstractTool
  • verify_ip(ip_address: str)
      → get details and validation for an IP address
  • verify_email(email: str)
      → Check if an email address is valid
  • verify_phone(phone: str)
      → validate a phone number

Examples:
- "get weather in London" -> use WeatherTool.get_weather with city="London"
- "fetch some facts" -> use FactsTool.get_facts with limit=5
- "get interesting facts" -> use FactsTool.get_facts with limit=5
- "verify email user@example.com" -> use AbstractTool.verify_email with email="user@example.com"
- "verify phone +1234567890" -> use AbstractTool.verify_phone with phone="+1234567890"
- "check IP 8.8.8.8" -> use AbstractTool.verify_ip with ip_address="8.8.8.8"
- "get posts" -> use PostsTool.get_posts with limit=5
- "get user info" -> use PostsTool.get_user with user_id=1
- "weather in Delhi and facts" -> use WeatherTool.get_weather AND FactsTool.get_facts
- "find top Python repos on GitHub"->use GitHubTool.search_repos with query="Python"
- "trending JavaScript repos"-> use GitHubTool.trending_repos with language="JavaScript"
- "get details for microsoft/vscode repo"-> use GitHubTool.get_repo with owner="microsoft" repo="vscode"
Output ONLY valid JSON. No markdown, no explanation, no preamble.

Schema:
{
  "task_summary": "<one-sentence summary>",
  "steps": [
    {
      "step": <integer>,
      "tool": "<ToolName>",
      "action": "<action_name>",
      "<param1>": <value1>
    }
  ]
}

Rules:
- ALWAYS try to match the user request to one of the available tools above.
- Each step must reference exactly one tool and one action.
- Include only parameters relevant to the action.
- Order steps logically.
- NEVER return empty steps if the task can be matched to any available tool.
"""


def plan(task: str) -> dict:
    prompt = f"{PLANNER_SYSTEM}\n\nUser task: {task}"
    raw = call_llm(prompt, expect_json=True)
    plan_data = json.loads(raw)

    if "steps" not in plan_data:
        raise ValueError("Planner response missing 'steps' key")
    for i, step in enumerate(plan_data["steps"]):
        for required_key in ("step", "tool", "action"):
            if required_key not in step:
                raise ValueError(f"Step {i} missing required key '{required_key}'")

    return plan_data
