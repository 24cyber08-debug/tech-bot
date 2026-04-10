# AI Operations Assistant
### CodeWar 2.0 · Track: Generative AI & Agentic Systems

A three-agent AI pipeline that accepts natural-language tasks, decomposes them into structured plans, executes real third-party APIs, and returns verified structured answers.

---

## Architecture

```
User Task
   │
   ▼
┌──────────────┐     JSON Plan      ┌───────────────┐    Tool Results   ┌──────────────┐
│ Planner Agent│ ─────────────────► │ Executor Agent│ ────────────────► │Verifier Agent│
│  (Gemini LLM)│                    │  (Parallel ✓) │                   │  (Gemini LLM)│
└──────────────┘                    └───────────────┘                   └──────────────┘
                                           │                                    │
                                    GitHubTool                         Final JSON Answer
                                    WeatherTool                          + Summary
                                    NewsTool
```

**Three distinct agents, each with its own LLM prompt and responsibility:**

| Agent | File | Responsibility |
|---|---|---|
| Planner | `agents/planner.py` | Converts natural language → structured JSON plan |
| Executor | `agents/executor.py` | Calls tools with retry logic + parallel execution |
| Verifier | `agents/verifier.py` | Validates results, formats final answer |

---

## Setup

### 1. Clone & install

```bash
cd ai_ops_assistant
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

Required keys:
| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `OPENWEATHER_API_KEY` | [OpenWeatherMap](https://openweathermap.org/api) (free tier) |
| `NEWSAPI_KEY` | [NewsAPI.org](https://newsapi.org) (free tier) |
| `GITHUB_TOKEN` | [GitHub Settings → Tokens](https://github.com/settings/tokens) (optional, raises rate limit) |

### 3. Run

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** for the Web UI dashboard.

---

## API

### `POST /run`

```json
{
  "task": "Find top 3 Python repos and weather in Amsterdam",
  "parallel": true
}
```

**Response:**
```json
{
  "run_id": "a1b2c3d4",
  "task": "...",
  "plan": { "task_summary": "...", "steps": [...] },
  "execution": [ { "step": 1, "tool": "GitHubTool", "status": "success", "data": {...}, "elapsed_ms": 312 } ],
  "answer": {
    "summary": "Found 3 repos. Weather in Amsterdam: 14°C, cloudy.",
    "results": { ... },
    "verified": true,
    "total_steps": 2,
    "successful_steps": 2
  },
  "meta": {
    "elapsed_sec": 4.2,
    "estimated_cost_usd": 0.000182,
    "parallel": true,
    "timeline": [...]
  }
}
```

### `GET /history` — last 20 runs
### `GET /health` — health check

---

## Bonus Features Implemented

| Feature | Status |
|---|---|
| Caching API responses | ✅ In-memory TTL cache (300–600s) in all tools |
| Cost tracking | ✅ Estimated token cost per request in `meta.estimated_cost_usd` |
| Parallel tool execution | ✅ `ThreadPoolExecutor` in Executor Agent |
| Web UI dashboard | ✅ Real-time pipeline visualization at `/` |

---

## Project Structure

```
ai_ops_assistant/
├── agents/
│   ├── planner.py       # LLM → JSON plan
│   ├── executor.py      # Parallel tool execution + retry
│   └── verifier.py      # LLM result validation
├── tools/
│   ├── github_tool.py   # GitHub REST API
│   ├── weather_tool.py  # OpenWeatherMap API
│   └── news_tool.py     # NewsAPI.org
├── llm/
│   └── gemini_client.py # Gemini 1.5 Flash wrapper
├── static/
│   └── index.html       # Web UI dashboard
├── main.py              # FastAPI app
├── requirements.txt
└── .env.example
```
