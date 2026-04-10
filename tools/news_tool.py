"""
FactsTool — uses catfact.ninja (no API key, no network restrictions)
Returns fun facts as a creative "news" source.
"""
import time
import requests

BASE = "https://catfact.ninja"
_cache: dict = {}
CACHE_TTL = 300

def _get(url: str, params: dict = None) -> dict:
    cache_key = url + str(params)
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _cache[cache_key] = (time.time(), data)
    return data

def get_facts(limit: int = 5) -> list:
    data = _get(f"{BASE}/facts", {"limit": limit})
    return [{"fact": f["fact"], "length": f["length"]} for f in data.get("data", [])]

def get_fact() -> dict:
    data = _get(f"{BASE}/fact")
    return {"fact": data["fact"], "length": data["length"]}

def run(action: str, **kwargs) -> dict:
    actions = {"get_facts": get_facts, "get_fact": get_fact}
    if action not in actions:
        raise ValueError(f"FactsTool: unknown action '{action}'")
    return actions[action](**kwargs)