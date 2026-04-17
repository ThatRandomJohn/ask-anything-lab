"""Fetch N single-turn English prompts from WildChat-1M.

WildChat-1M is a gated dataset on HuggingFace. Requires an HF token with accepted license.
Falls back to ShareGPT / LMSYS if WildChat access is denied.

Output: corpus/data/prompts.parquet with columns [id, text, source, lang, turn_count].
"""
import os
import sys
import random
from pathlib import Path

import pandas as pd
from datasets import load_dataset

HERE = Path(__file__).parent
OUT = HERE / "data" / "prompts.parquet"
N = int(os.environ.get("CORPUS_N", "5000"))
SEED = 42
MIN_LEN = 20
MAX_LEN = 2000


def load_hf_token() -> str | None:
    path = Path.home() / ".cache" / "huggingface" / "token"
    if path.exists():
        return path.read_text().strip()
    return os.environ.get("HF_TOKEN")


def try_wildchat(token: str | None):
    print("[fetch] trying allenai/WildChat-1M ...")
    # Stream so we don't download the full 1M rows. English, single-turn first user message.
    ds = load_dataset(
        "allenai/WildChat-1M",
        split="train",
        streaming=True,
        token=token,
    )
    rows = []
    seen_ids = set()
    for i, ex in enumerate(ds):
        if len(rows) >= N:
            break
        if i % 5000 == 0 and i > 0:
            print(f"  scanned {i:>7,}  kept {len(rows):>5,}")
        if ex.get("language") != "English":
            continue
        if ex.get("toxic"):
            continue
        convo = ex.get("conversation") or []
        if not convo:
            continue
        first = convo[0]
        if first.get("role") != "user":
            continue
        text = (first.get("content") or "").strip()
        if not (MIN_LEN <= len(text) <= MAX_LEN):
            continue
        cid = ex.get("conversation_hash") or ex.get("hash") or str(i)
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        rows.append({
            "id": cid,
            "text": text,
            "source": "wildchat",
            "lang": "en",
            "turn_count": len(convo),
        })
    return rows


def try_lmsys(token: str | None):
    print("[fetch] falling back to lmsys/lmsys-chat-1m ...")
    ds = load_dataset("lmsys/lmsys-chat-1m", split="train", streaming=True, token=token)
    rows = []
    for i, ex in enumerate(ds):
        if len(rows) >= N:
            break
        if ex.get("language") and ex.get("language") != "English":
            continue
        convo = ex.get("conversation") or []
        if not convo:
            continue
        first = convo[0]
        if first.get("role") != "user":
            continue
        text = (first.get("content") or "").strip()
        if not (MIN_LEN <= len(text) <= MAX_LEN):
            continue
        rows.append({
            "id": ex.get("conversation_id") or str(i),
            "text": text,
            "source": "lmsys",
            "lang": "en",
            "turn_count": len(convo),
        })
    return rows


def try_openassistant(token: str | None):
    print("[fetch] falling back to OpenAssistant/oasst1 ...")
    ds = load_dataset("OpenAssistant/oasst1", split="train", token=token)
    # Take root-level prompter messages (depth 0) in English
    rows = []
    for ex in ds:
        if len(rows) >= N:
            break
        if ex.get("role") != "prompter":
            continue
        if ex.get("parent_id") is not None:
            continue
        if ex.get("lang") != "en":
            continue
        text = (ex.get("text") or "").strip()
        if not (MIN_LEN <= len(text) <= MAX_LEN):
            continue
        rows.append({
            "id": ex.get("message_id"),
            "text": text,
            "source": "oasst",
            "lang": "en",
            "turn_count": 1,
        })
    return rows


def main():
    token = load_hf_token()
    print(f"[fetch] target N={N}, seed={SEED}")
    print(f"[fetch] token: {'present' if token else 'MISSING'}")

    rows = []
    for fn in (try_wildchat, try_lmsys, try_openassistant):
        try:
            rows = fn(token)
            if rows:
                print(f"[fetch] got {len(rows):,} from {fn.__name__}")
                break
        except Exception as e:
            print(f"[fetch] {fn.__name__} failed: {type(e).__name__}: {str(e)[:200]}")

    if not rows:
        print("[fetch] ERROR: all sources failed")
        sys.exit(1)

    random.Random(SEED).shuffle(rows)
    rows = rows[:N]

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"[fetch] wrote {len(df):,} rows → {OUT}")
    print(f"[fetch] sample:")
    for i, r in df.head(3).iterrows():
        print(f"  [{r['source']}] {r['text'][:120]}")


if __name__ == "__main__":
    main()
