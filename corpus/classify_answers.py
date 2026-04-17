"""Classify answer emotions with SamLowe/roberta-base-go_emotions.

Thin wrapper over the batched inference loop. Runs over answer parquets
that have [id, answer_text, ...] columns and writes the same 31-column
schema as emotions.parquet (28 emo_<label> + id + dominant_emotion + dominant_score).

Usage:
  python classify_answers.py --input answers_gpt.parquet --output emotions_answers_gpt.parquet
  python classify_answers.py --input answers_claude.parquet --output emotions_answers_claude.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

HERE = Path(__file__).parent
DATA = HERE / "data"

MODEL_ID = "SamLowe/roberta-base-go_emotions"
BATCH_SIZE = 16  # lower than prompts (32) — longer sequences use more memory
MAX_LEN = 512    # higher than prompts (256) — answers are longer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input parquet filename under corpus/data/")
    ap.add_argument("--output", required=True, help="Output parquet filename under corpus/data/")
    ap.add_argument("--text-col", default="answer_text", help="Column holding the text to classify")
    args = ap.parse_args()

    in_path = DATA / args.input
    out_path = DATA / args.output
    if not in_path.exists():
        print(f"[classify_answers] {in_path} not found")
        sys.exit(1)

    df = pd.read_parquet(in_path)
    print(f"[classify_answers] {len(df):,} rows loaded from {in_path.name}")

    if args.text_col not in df.columns:
        print(f"[classify_answers] column '{args.text_col}' not in {df.columns.tolist()}")
        sys.exit(1)

    print(f"[classify_answers] loading {MODEL_ID} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    model.to(device)
    print(f"[classify_answers] device: {device}")

    labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]
    print(f"[classify_answers] {len(labels)} labels")

    texts = df[args.text_col].astype(str).tolist()
    n = len(texts)
    all_probs = np.zeros((n, len(labels)), dtype=np.float32)

    t0 = time.time()
    with torch.inference_mode():
        for i in range(0, n, BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            enc = tok(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_LEN,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            logits = model(**enc).logits
            probs = torch.sigmoid(logits).cpu().numpy()
            all_probs[i : i + len(batch)] = probs
            if (i // BATCH_SIZE) % 10 == 0:
                done = min(i + BATCH_SIZE, n)
                rate = done / (time.time() - t0 + 1e-6)
                eta = (n - done) / rate if rate else 0
                print(f"  [{done:>5,}/{n:,}]  {rate:.1f}/s  eta {eta:.0f}s")

    print(f"[classify_answers] done in {time.time() - t0:.1f}s")

    out = pd.DataFrame(all_probs, columns=[f"emo_{l}" for l in labels])
    out.insert(0, "id", df["id"].values)
    out["dominant_emotion"] = [labels[i] for i in all_probs.argmax(axis=1)]
    out["dominant_score"] = all_probs.max(axis=1)

    out.to_parquet(out_path, index=False)
    print(f"[classify_answers] wrote {len(out):,} rows → {out_path}")
    print()
    print("[classify_answers] dominant emotion distribution:")
    print(out["dominant_emotion"].value_counts().head(15).to_string())


if __name__ == "__main__":
    main()
