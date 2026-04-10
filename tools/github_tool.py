"""
GitHubTool — GitHub REST API
Requires: GITHUB_TOKEN in .env
Actions: search_repos, trending_repos, get_repo
"""
import os
import requests
from tools import cache_get, cache_set

GITHUB_API = "https://api.github.com"
CACHE_TTL  = 300

def _headers() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _get(url: str, params: dict = None) -> dict:
    key  = url + str(params)
    data = cache_get(key, CACHE_TTL)
    if data is not None:
        return data
    resp = requests.get(url, headers=_headers(), params=params, timeout=8)
    resp.raise_for_status()
    data = resp.json()
    cache_set(key, data)
    return data

def search_repos(query: str, sort: str = "stars", limit: int = 3) -> list:
    data = _get(f"{GITHUB_API}/search/repositories",
                {"q": query, "sort": sort, "order": "desc", "per_page": limit})
    return [
        {
            "name":        r["full_name"],
            "stars":       r["stargazers_count"],
            "forks":       r["forks_count"],
            "description": r.get("description", ""),
            "url":         r["html_url"],
            "language":    r.get("language", "N/A"),
        }
        for r in data.get("items", [])[:limit]
    ]

def trending_repos(language: str = "", limit: int = 3) -> list:
    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    q = f"created:>{since}"
    if language:
        q += f" language:{language}"
    return search_repos(query=q, sort="stars", limit=limit)

def get_repo(owner: str, repo: str) -> dict:
    data = _get(f"{GITHUB_API}/repos/{owner}/{repo}")
    return {
        "name":        data["full_name"],
        "stars":       data["stargazers_count"],
        "forks":       data["forks_count"],
        "description": data.get("description", ""),
        "url":         data["html_url"],
        "language":    data.get("language", "N/A"),
        "open_issues": data["open_issues_count"],
        "license":     data.get("license", {}).get("name", "N/A") if data.get("license") else "N/A",
    }

def run(action: str, **kwargs) -> object:
    actions = {
        "search_repos":   search_repos,
        "trending_repos": trending_repos,
        "get_repo":       get_repo,
    }
    if action not in actions:
        raise ValueError(f"GitHubTool: unknown action '{action}'. Available: {list(actions)}")
    return actions[action](**kwargs)