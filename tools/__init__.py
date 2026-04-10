import time

_shared_cache: dict = {}

def cache_get(key: str, ttl: int) -> object:
    if key in _shared_cache:
        ts, data = _shared_cache[key]
        if time.time() - ts < ttl:
            return data
    return None

def cache_set(key: str, data: object):
    _shared_cache[key] = (time.time(), data)

from . import github_tool
from . import weather_tool
from . import news_tool as facts_tool
from . import abstract_tool

TOOL_REGISTRY = {
    "GitHubTool":  github_tool,
    "WeatherTool": weather_tool,
    "FactsTool":   facts_tool,
    "AbstractTool": abstract_tool,
}

def run_tool(tool_name: str, action: str, **kwargs):
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY)}"
        )
    return TOOL_REGISTRY[tool_name].run(action, **kwargs)


