"""
Mistral LLM client — wraps mistralai for all agents.
"""
import os
import json
import re
import time
from mistralai import Mistral

_client = None

def _get_client():
    global _client
    if _client is None:
        key = os.getenv("MISTRAL_API_KEY", "")
        if not key:
            raise RuntimeError("MISTRAL_API_KEY not set in .env file")
        _client = Mistral(api_key=key)
    return _client

def call_llm(prompt: str, expect_json: bool = False, retries: int = 3) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            response = response = _get_client().chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content.strip()
            if expect_json:
                text = _extract_json(text)
                json.loads(text)
            return text
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_err}")

def _extract_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()
