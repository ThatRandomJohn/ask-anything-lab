"""Embed each prompt with sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast, local).

Outputs corpus/data/embeddings.npy — a (N, 384) float32 array.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).parent
PROMPTS = HERE / "data" / "prompts.parquet"
OUT = HERE / "data" / "embeddings.npy"
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64


def main():
    if not PROMPTS.exists():
        print(f"[embed] {PROMPTS} not found — run fetch_corpus.py first")
        sys.exit(1)

    df = pd.read_parquet(PROMPTS)
    print(f"[embed] {len(df):,} prompts loaded")

    print(f"[embed] loading {MODEL_ID} ...")
    model = SentenceTransformer(MODEL_ID)
    # The model auto-picks device (MPS on Mac).
    print(f"[embed] device: {model.device}")

    t0 = time.time()
    embeddings = model.encode(
        df["text"].tolist(),
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(f"[embed] shape={embeddings.shape}  dtype={embeddings.dtype}  took {time.time() - t0:.1f}s")

    np.save(OUT, embeddings)
    print(f"[embed] wrote → {OUT}")


if __name__ == "__main__":
    main()
