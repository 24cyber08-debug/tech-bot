# ⚡ Tech Bot
### CodeWar 2.0 · Track: Generative AI & Agentic Systems

> An AI Operations Assistant that plans, executes, and independently verifies tasks using a 3-agent pipeline powered by Mistral AI.

---

## Architecture

```
User Task
    ↓
🧠 Planner Agent  →  Converts task to JSON execution plan
    ↓
⚙️ Executor Agent  →  Calls real APIs in parallel with retry logic
    ↓
✅ Verifier Agent  →  Independently re-fetches + verifies at 3 levels
    ↓
Final Answer + Confidence Score + Human Summary
```

---

## What Makes Tech Bot Different

- **Independent Verification** — Verifier re-fetches data itself and compares with Executor results
- **3-Level Verification** — L1 Completeness · L2 Correctness · L3 Task Relevance
- **Agent Independence** — Run Planner, Executor or Verifier individually or in any combination
- **Downloadable Plans** — Export Planner JSON and reuse it anytime
- **6 Real APIs** — Weather, GitHub, Facts, Phone Validation, Email Validation, IP Geolocation
- **Zero mandatory API keys** — Core tools work out of the box with free APIs

---

## Agents

| Agent | File | Responsibility |
|---|---|---|
| 🧠 Planner | `agents/planner.py` | Natural language → structured JSON plan via Mistral |
| ⚙️ Executor | `agents/executor.py` | Executes plan steps with parallel API calls + retry |
| ✅ Verifier | `agents/verifier.py` | Re-fetches data independently + 3-level verification |

---

## Tools — 6 Real APIs

| Tool | API | Key needed? | What it does |
|---|---|---|---|
| WeatherTool | Open-Meteo | ❌ No | Current weather + forecast for any city |
| GitHubTool | GitHub REST API | ✅ Optional | Search repos, trending, repo details |
| FactsTool | CatFact API | ❌ No | Interesting random facts |
| PhoneTool | AbstractAPI Phone | ✅ Required | Validate phone numbers, get carrier + country |
| EmailTool | AbstractAPI Email | ✅ Required | Validate emails, check deliverability |
| IPTool | AbstractAPI IP | ✅ Required | Geolocate IPs, get country, city, ISP |

---

## Bonus Features ✅ All 4 Implemented

| Feature | Details |
|---|---|
| Caching | TTL cache (5-10 min) in all tools — no duplicate API calls |
| Cost tracking | Estimated USD cost per run shown in response and dashboard |
| Parallel execution | ThreadPoolExecutor — all steps run simultaneously |
| Web UI dashboard | Real-time pipeline visualization at localhost:8000 |

---

## Setup

### 1. Install dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:
```env
# Required
MISTRAL_API_KEY=your_mistral_key_here

# Optional — raises GitHub rate limit
GITHUB_TOKEN=your_github_token_here

# AbstractAPI keys (get free keys at https://app.abstractapi.com)
ABSTRACT_PHONE_KEY=your_phone_validation_key
ABSTRACT_EMAIL_KEY=your_email_validation_key
ABSTRACT_IP_KEY=your_ip_geolocation_key
```

Get free keys at:
- Mistral → https://console.mistral.ai
- AbstractAPI → https://app.abstractapi.com/dashboard
- GitHub → https://github.com/settings/tokens

### 3. Run
```bash
python3 main.py
```

Open **http://localhost:8000** for the Web UI dashboard.

---

## API Endpoints

```
POST /run      → run selected agents (planner, executor, verifier)
GET  /health   → health check + key status
GET  /history  → last 20 runs
```

### Example request
```json
POST /run
{
  "task": "Validate phone number +919876543210 and get location of IP 8.8.8.8",
  "agents": ["planner", "executor", "verifier"],
  "parallel": true
}
```

### Example response
```json
{
  "run_id": "a1b2c3d4",
  "plan": { "task_summary": "Validate phone and geolocate IP", "steps": [...] },
  "execution": [
    { "step": 1, "tool": "PhoneTool", "status": "success", "elapsed_ms": 210 },
    { "step": 2, "tool": "IPTool", "status": "success", "elapsed_ms": 183 }
  ],
  "answer": {
    "summary": "Phone is valid, registered in India with Airtel. IP 8.8.8.8 is Google DNS located in the US.",
    "verified": true,
    "confidence_score": 99,
    "level1_planner":  { "passed": true },
    "level2_executor": { "passed": true },
    "level3_relevance":{ "passed": true }
  },
  "meta": { "elapsed_sec": 3.8, "estimated_cost_usd": 0.000028 }
}
```

---

## Project Structure

```
tech-bot/
├── agents/
│   ├── planner.py       # Mistral LLM → JSON plan
│   ├── executor.py      # Parallel tool execution + retry
│   └── verifier.py      # Independent re-fetch + 3-level verification
├── tools/
│   ├── github_tool.py   # GitHub REST API
│   ├── weather_tool.py  # Open-Meteo (no key needed)
│   ├── news_tool.py     # CatFact API (no key needed)
│   ├── phone_tool.py    # AbstractAPI Phone Validation
│   ├── email_tool.py    # AbstractAPI Email Validation
│   └── ip_tool.py       # AbstractAPI IP Geolocation
├── llm/
│   └── gemini_client.py # Mistral AI client (lazy init)
├── static/
│   └── index.html       # Web UI dashboard
├── main.py              # FastAPI entrypoint
├── requirements.txt
└── .env.example
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Mistral AI — mistral-small-latest |
| Backend | FastAPI + Uvicorn |
| Parallelism | ThreadPoolExecutor |
| Weather | Open-Meteo (free, no key) |
| Code | GitHub REST API |
| Facts | CatFact (free, no key) |
| Phone Validation | AbstractAPI |
| Email Validation | AbstractAPI |
| IP Geolocation | AbstractAPI |
| Language | Python 3.13 |

---

## Demo Tasks

Try these in the dashboard:

```
Get weather in Mumbai and fetch 5 interesting facts
Find top 3 Python repositories on GitHub
Validate phone number +919876543210
Validate email address test@gmail.com
Get location of IP address 8.8.8.8
Validate phone +14155552671 and get weather in San Francisco
Check if test@yahoo.com is valid and get IP info for 1.1.1.1
```

---

## Agent Independence — Unique Feature

Tech Bot lets you run agents individually:

| Mode | Use case |
|---|---|
| Planner only | Generate and download a JSON plan |
| Executor only | Paste any JSON plan and execute it |
| Planner + Executor | Plan and execute without verification |
| All 3 agents | Full pipeline with independent verification |

---

*Built for CodeWar 2.0 — Generative AI & Agentic Systems track*  
*by Deepak Choudhary*