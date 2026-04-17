"""Classify each prompt with SamLowe/roberta-base-go_emotions (28 emotions, multi-label).

Outputs corpus/data/emotions.parquet with one column per emotion plus [id, dominant_emotion].
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

HERE = Path(__file__).parent
PROMPTS = HERE / "data" / "prompts.parquet"
OUT = HERE / "data" / "emotions.parquet"
MODEL_ID = "SamLowe/roberta-base-go_emotions"
BATCH_SIZE = 32
MAX_LEN = 256


def main():
    if not PROMPTS.exists():
        print(f"[emotions] {PROMPTS} not found — run fetch_corpus.py first")
        sys.exit(1)

    df = pd.read_parquet(PROMPTS)
    print(f"[emotions] {len(df):,} prompts loaded")

    print(f"[emotions] loading {MODEL_ID} ...")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()

    # Pick the best available device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    model.to(device)
    print(f"[emotions] device: {device}")

    labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]
    print(f"[emotions] {len(labels)} labels: {labels[:8]}...")

    texts = df["text"].tolist()
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

    print(f"[emotions] done in {time.time() - t0:.1f}s")

    out = pd.DataFrame(all_probs, columns=[f"emo_{l}" for l in labels])
    out.insert(0, "id", df["id"].values)
    out["dominant_emotion"] = [labels[i] for i in all_probs.argmax(axis=1)]
    out["dominant_score"] = all_probs.max(axis=1)

    out.to_parquet(OUT, index=False)
    print(f"[emotions] wrote {len(out):,} rows → {OUT}")
    print()
    print("[emotions] dominant emotion distribution:")
    print(out["dominant_emotion"].value_counts().head(15).to_string())


if __name__ == "__main__":
    main()
