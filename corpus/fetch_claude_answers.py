"""Generate Claude Sonnet 4.5 answers for each prompt in prompts.parquet.

- Concurrency: ThreadPoolExecutor(max_workers=10)
- Retry: exponential backoff on RateLimitError / APIConnectionError / OverloadedError
- Incremental cache: append-only JSONL after every completion so crashes resume
- Idempotent: if answers_claude.parquet already exists, only Claude is only
  called for missing IDs.

Output: corpus/data/answers_claude.parquet with [id, answer_text, model_name]
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

HERE = Path(__file__).parent
DATA = HERE / "data"
PROMPTS = DATA / "prompts.parquet"
OUT = DATA / "answers_claude.parquet"
PARTIAL = DATA / "answers_claude_partial.jsonl"

MODEL = "claude-sonnet-4-5-20250929"
MAX_WORKERS = 10
MAX_TOKENS = 1024
TEMPERATURE = 0.7
MAX_ATTEMPTS = 5
BASE_BACKOFF = 2.0

SYSTEM_PROMPT = (
    "You are a helpful, honest assistant. Answer the user's question clearly and "
    "concisely. Be direct, friendly, and useful."
)


def load_existing_ids() -> set[str]:
    """Return the set of IDs we've already completed (parquet + partial jsonl)."""
    done: set[str] = set()
    if OUT.exists():
        df = pd.read_parquet(OUT)
        done.update(df["id"].astype(str).tolist())
    if PARTIAL.exists():
        with PARTIAL.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    done.add(str(row["id"]))
                except Exception:
                    pass
    return done


def load_partial_rows() -> list[dict]:
    rows: list[dict] = []
    if PARTIAL.exists():
        with PARTIAL.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def call_claude(client, prompt_id: str, prompt_text: str) -> dict:
    """Call Claude with retries. Returns row dict or raises after max attempts."""
    import anthropic

    last_err: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt_text}],
            )
            text = msg.content[0].text if msg.content else ""
            return {
                "id": prompt_id,
                "answer_text": text,
                "model_name": MODEL,
            }
        except (
            anthropic.RateLimitError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        ) as e:
            last_err = e
            wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1.0)
            print(f"  [retry] {prompt_id[:10]}… {type(e).__name__} attempt {attempt+1}/{MAX_ATTEMPTS} sleeping {wait:.1f}s")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            # 529 overloaded, 503 service unavailable — retry
            if getattr(e, "status_code", 0) in (429, 503, 529):
                last_err = e
                wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1.0)
                print(f"  [retry] {prompt_id[:10]}… status {e.status_code} attempt {attempt+1}/{MAX_ATTEMPTS} sleeping {wait:.1f}s")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed after {MAX_ATTEMPTS} attempts: {last_err}")


def main():
    load_dotenv(str(HERE.parent / ".env"))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[claude_answers] ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if not PROMPTS.exists():
        print(f"[claude_answers] {PROMPTS} not found")
        sys.exit(1)

    prompts_df = pd.read_parquet(PROMPTS)
    print(f"[claude_answers] {len(prompts_df):,} prompts loaded")

    done_ids = load_existing_ids()
    print(f"[claude_answers] {len(done_ids):,} already complete (resume)")

    todo_df = prompts_df[~prompts_df["id"].astype(str).isin(done_ids)]
    print(f"[claude_answers] {len(todo_df):,} to fetch")

    if len(todo_df) == 0:
        print("[claude_answers] nothing to do — merging partials into parquet")
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        DATA.mkdir(parents=True, exist_ok=True)
        partial_f = PARTIAL.open("a", buffering=1)  # line-buffered

        t0 = time.time()
        completed = 0
        total = len(todo_df)

        items = list(todo_df[["id", "text"]].itertuples(index=False, name=None))

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {
                ex.submit(call_claude, client, str(pid), ptext): str(pid)
                for pid, ptext in items
            }
            for fut in as_completed(futs):
                pid = futs[fut]
                try:
                    row = fut.result()
                except Exception as e:
                    print(f"  ! FAILED id={pid[:10]}… {type(e).__name__}: {e}")
                    continue
                partial_f.write(json.dumps(row) + "\n")
                completed += 1
                if completed % 25 == 0 or completed == total:
                    elapsed = time.time() - t0
                    rate = completed / elapsed if elapsed else 0
                    eta = (total - completed) / rate if rate else 0
                    print(f"  [{completed:>5}/{total:,}]  {rate:.1f}/s  eta {eta:.0f}s")

        partial_f.close()
        print(f"[claude_answers] completed {completed:,}/{total:,} in {time.time()-t0:.1f}s")

    # Merge all partials into the final parquet
    rows = load_partial_rows()
    if OUT.exists():
        prev = pd.read_parquet(OUT)
        prev_rows = prev.to_dict("records")
        # dedupe: rows from partials override prev
        by_id = {r["id"]: r for r in prev_rows}
        for r in rows:
            by_id[r["id"]] = r
        merged = list(by_id.values())
    else:
        merged = rows

    if not merged:
        print("[claude_answers] no rows to write")
        sys.exit(1)

    df = pd.DataFrame(merged)
    # Keep ordering aligned with prompts.parquet
    df = df.set_index("id").reindex(prompts_df["id"].astype(str)).reset_index()
    df = df.dropna(subset=["answer_text"])
    df.to_parquet(OUT, index=False)
    print(f"[claude_answers] wrote {len(df):,} rows → {OUT}")
    print()
    print("[claude_answers] sample answer:")
    sample = df.iloc[0]
    print(f"  id: {sample['id']}")
    print(f"  text: {sample['answer_text'][:200]}...")


if __name__ == "__main__":
    main()
