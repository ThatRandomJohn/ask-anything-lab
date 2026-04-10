"""Anthropic Claude API wrapper for audience mode.

Fires three parallel calls per submission — embeddings, sources, response.
Falls back to deterministic placeholders when ANTHROPIC_API_KEY is missing or on error.
"""
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

MODEL = "claude-sonnet-4-5-20250929"

_client = None
_tried = False
_client_lock = threading.Lock()


def _get_client():
    global _client, _tried
    with _client_lock:
        if _tried:
            return _client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("[claude] No ANTHROPIC_API_KEY set \u2014 audience mode will use fallback data.")
            _tried = True
            return None
        try:
            import anthropic
            _client = anthropic.Anthropic(api_key=api_key)
            print("[claude] Client initialized.")
        except Exception as e:
            print(f"[claude] Failed to initialize client: {e}")
            _client = None
        _tried = True
        return _client


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)


EMBED_SYSTEM = (
    "Extract 12-18 key words from the user's prompt and assign each to a semantic cluster.\n"
    "Return ONLY valid JSON:\n"
    '{"words":[{"word":"example","cluster":"category","x":0.2,"y":0.3,"size":14}]}\n'
    "Rules: 2-4 clusters. x: cluster 1 at 0.12-0.28, cluster 2 at 0.40-0.55, cluster 3 at 0.70-0.85.\n"
    "y: 0.25-0.48. size: 11-18. Short cluster names."
)

SOURCES_SYSTEM = (
    "Imagine what knowledge sources an LLM drew from to answer this. Return ONLY valid JSON:\n"
    '{"sources":[{"label":"Source \u2014 Topic","type":"category","relevance":0.95}]}\n'
    "6-8 sources. Types: medical, research, forum, reference, news, educational.\n"
    "Relevance 0.70-0.95 descending."
)


def get_embeddings(prompt: str) -> dict:
    client = _get_client()
    if client is None:
        return _fallback_embeddings(prompt)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=EMBED_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(msg.content[0].text)
    except Exception as e:
        print(f"[claude] get_embeddings error: {e}")
        return _fallback_embeddings(prompt)


def get_sources(prompt: str) -> dict:
    client = _get_client()
    if client is None:
        return _fallback_sources(prompt)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SOURCES_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(msg.content[0].text)
    except Exception as e:
        print(f"[claude] get_sources error: {e}")
        return _fallback_sources(prompt)


def get_response(prompt: str) -> str:
    client = _get_client()
    if client is None:
        return _fallback_response(prompt)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        print(f"[claude] get_response error: {e}")
        return _fallback_response(prompt)


def process_prompt_parallel(prompt: str):
    """Fire the three audience-mode calls in parallel and return (embeddings, sources, response)."""
    with ThreadPoolExecutor(max_workers=3) as ex:
        fe = ex.submit(get_embeddings, prompt)
        fs = ex.submit(get_sources, prompt)
        fr = ex.submit(get_response, prompt)
        return fe.result(), fs.result(), fr.result()


# ---------- Fallback data (no API key / error paths) ----------

def _fallback_embeddings(prompt: str) -> dict:
    tokens = [t for t in re.findall(r"[A-Za-z']+", prompt) if len(t) > 2][:15]
    if not tokens:
        tokens = ["your", "prompt", "here"]
    out = []
    third = max(1, len(tokens) // 3)
    for i, t in enumerate(tokens):
        if i < third:
            cluster, x_base = "concept", 0.15
        elif i < 2 * third:
            cluster, x_base = "subject", 0.45
        else:
            cluster, x_base = "context", 0.75
        out.append({
            "word": t,
            "cluster": cluster,
            "x": x_base + (i % 4) * 0.03,
            "y": 0.28 + (i % 3) * 0.06,
            "size": 14,
        })
    return {"words": out}


def _fallback_sources(prompt: str) -> dict:
    return {"sources": [
        {"label": "Wikipedia \u2014 General Knowledge",   "type": "reference",   "relevance": 0.92},
        {"label": "arXiv \u2014 Related Research Papers", "type": "research",    "relevance": 0.88},
        {"label": "Stack Overflow \u2014 Q&A Threads",    "type": "forum",       "relevance": 0.83},
        {"label": "Reddit \u2014 Community Discussions",  "type": "forum",       "relevance": 0.79},
        {"label": "News Archives \u2014 Recent Coverage", "type": "news",        "relevance": 0.75},
        {"label": "Textbooks \u2014 Foundational Texts",  "type": "educational", "relevance": 0.71},
    ]}


def _fallback_response(prompt: str) -> str:
    return (
        "(Fallback response \u2014 no ANTHROPIC_API_KEY set.)\n\n"
        "In live deployment, Claude would generate a full response to your prompt here. "
        "The point of the demo isn't the answer itself, but the process: your words became "
        "numbers, those numbers became coordinates, nearby coordinates were retrieved, and a "
        "response was synthesized from the overlap between your language and the model's "
        "training data."
    )
