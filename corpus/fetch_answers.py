"""Extract GPT assistant answers for the same 5,000 prompts in prompts.parquet.

Re-streams allenai/WildChat-1M, matches on conversation_hash, pulls the first
assistant turn. Output: corpus/data/answers_gpt.parquet with
[id, answer_text, model_name] columns.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

HERE = Path(__file__).parent
PROMPTS = HERE / "data" / "prompts.parquet"
OUT = HERE / "data" / "answers_gpt.parquet"


def load_hf_token() -> str | None:
    p = Path.home() / ".cache" / "huggingface" / "token"
    if p.exists():
        return p.read_text().strip()
    return os.environ.get("HF_TOKEN")


def main():
    if not PROMPTS.exists():
        print(f"[fetch_answers] {PROMPTS} not found — run fetch_corpus.py first")
        sys.exit(1)

    prompts_df = pd.read_parquet(PROMPTS)
    target_ids = set(prompts_df["id"].tolist())
    print(f"[fetch_answers] need answers for {len(target_ids):,} prompts")

    token = load_hf_token()
    print(f"[fetch_answers] HF token: {'present' if token else 'MISSING'}")
    print("[fetch_answers] streaming allenai/WildChat-1M ...")

    ds = load_dataset("allenai/WildChat-1M", split="train", streaming=True, token=token)

    found: dict[str, dict] = {}
    for i, ex in enumerate(ds):
        if len(found) >= len(target_ids):
            break
        if i % 5000 == 0 and i > 0:
            print(f"  scanned {i:>7,}  matched {len(found):>5,}/{len(target_ids):,}")
        cid = ex.get("conversation_hash") or ex.get("hash")
        if not cid or cid not in target_ids or cid in found:
            continue
        convo = ex.get("conversation") or []
        if len(convo) < 2:
            continue
        assistant_turn = convo[1]
        if assistant_turn.get("role") != "assistant":
            # find first assistant turn
            assistant_turn = next(
                (m for m in convo[1:] if m.get("role") == "assistant"),
                None,
            )
            if assistant_turn is None:
                continue
        answer_text = (assistant_turn.get("content") or "").strip()
        if not answer_text:
            continue
        model_name = ex.get("model") or "unknown"
        found[cid] = {
            "id": cid,
            "answer_text": answer_text,
            "model_name": model_name,
        }

    print(f"[fetch_answers] matched {len(found):,} / {len(target_ids):,}")
    missing = target_ids - set(found.keys())
    if missing:
        print(f"[fetch_answers] WARNING: {len(missing)} prompts had no usable assistant turn")

    df = pd.DataFrame(list(found.values()))
    # Preserve the ordering of prompts.parquet for clean joining
    df = df.set_index("id").reindex(prompts_df["id"]).reset_index()
    # Drop rows with no answer (NaN) but keep the id for transparency
    dropped = df["answer_text"].isna().sum()
    df = df.dropna(subset=["answer_text"])
    print(f"[fetch_answers] dropped {dropped} rows with no matched answer")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"[fetch_answers] wrote {len(df):,} rows → {OUT}")
    print()
    print("[fetch_answers] model distribution:")
    print(df["model_name"].value_counts().head(10).to_string())
    print()
    print("[fetch_answers] sample answer:")
    sample = df.iloc[0]
    print(f"  id: {sample['id']}")
    print(f"  model: {sample['model_name']}")
    print(f"  text: {sample['answer_text'][:200]}...")


if __name__ == "__main__":
    main()
