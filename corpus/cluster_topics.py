"""Cluster prompts with UMAP + HDBSCAN.

UMAP reduces 384-dim embeddings to ~8 dims for better HDBSCAN density estimation.
HDBSCAN with min_cluster_size tuned for ~30-60 clusters over 5K prompts.

Outputs corpus/data/clusters.parquet with [id, cluster, umap_x, umap_y]
and corpus/data/cluster_exemplars.json — 10 closest-to-centroid exemplars per cluster.
"""
import json
import sys
import time
from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap

HERE = Path(__file__).parent
PROMPTS = HERE / "data" / "prompts.parquet"
EMB = HERE / "data" / "embeddings.npy"
OUT_CLUSTERS = HERE / "data" / "clusters.parquet"
OUT_EXEMPLARS = HERE / "data" / "cluster_exemplars.json"

UMAP_DIMS = 8
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.0
HDBSCAN_MIN_CLUSTER = 30
HDBSCAN_MIN_SAMPLES = 5
EXEMPLARS_PER_CLUSTER = 10
SEED = 42


def main():
    if not PROMPTS.exists() or not EMB.exists():
        print("[cluster] prompts.parquet and/or embeddings.npy not found")
        sys.exit(1)

    df = pd.read_parquet(PROMPTS)
    emb = np.load(EMB)
    print(f"[cluster] {len(df):,} prompts, embeddings {emb.shape}")

    # UMAP reduction for clustering (higher dim than viz)
    t0 = time.time()
    print(f"[cluster] UMAP → {UMAP_DIMS}d ...")
    reducer = umap.UMAP(
        n_components=UMAP_DIMS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric="cosine",
        random_state=SEED,
    )
    emb_reduced = reducer.fit_transform(emb)
    print(f"[cluster] UMAP done in {time.time() - t0:.1f}s")

    # Separate UMAP to 2d just for visualization/exports
    t0 = time.time()
    print("[cluster] UMAP → 2d (for viz) ...")
    viz = umap.UMAP(
        n_components=2,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=0.1,
        metric="cosine",
        random_state=SEED,
    ).fit_transform(emb)
    print(f"[cluster] viz UMAP done in {time.time() - t0:.1f}s")

    # HDBSCAN over reduced space
    t0 = time.time()
    print(f"[cluster] HDBSCAN min_cluster={HDBSCAN_MIN_CLUSTER} ...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(emb_reduced)
    print(f"[cluster] HDBSCAN done in {time.time() - t0:.1f}s")

    n_clusters = int(labels.max()) + 1
    n_noise = int((labels == -1).sum())
    print(f"[cluster] → {n_clusters} clusters, {n_noise} noise ({100*n_noise/len(labels):.1f}%)")

    # Save cluster assignment + 2d coordinates
    out = pd.DataFrame({
        "id": df["id"].values,
        "cluster": labels,
        "umap_x": viz[:, 0],
        "umap_y": viz[:, 1],
    })
    out.to_parquet(OUT_CLUSTERS, index=False)
    print(f"[cluster] wrote → {OUT_CLUSTERS}")

    # Exemplars: for each cluster, take the points with highest membership probability
    exemplars = {}
    probs = clusterer.probabilities_
    for cid in range(n_clusters):
        mask = labels == cid
        if not mask.any():
            continue
        idxs = np.where(mask)[0]
        # Sort by HDBSCAN membership probability desc, then take top-K
        order = idxs[np.argsort(-probs[idxs])][:EXEMPLARS_PER_CLUSTER]
        exemplars[str(cid)] = [
            {
                "id": str(df.iloc[int(i)]["id"]),
                "text": str(df.iloc[int(i)]["text"])[:500],
                "prob": float(probs[int(i)]),
            }
            for i in order
        ]

    with open(OUT_EXEMPLARS, "w") as f:
        json.dump({
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "total": len(labels),
            "clusters": exemplars,
        }, f, indent=2)
    print(f"[cluster] wrote exemplars → {OUT_EXEMPLARS}")

    # Cluster size summary
    sizes = pd.Series(labels).value_counts().sort_index()
    print(f"\n[cluster] cluster size distribution:")
    print(f"  noise (-1): {sizes.get(-1, 0)}")
    in_clusters = sizes[sizes.index >= 0]
    if len(in_clusters):
        print(f"  clusters 0..{in_clusters.index.max()}: min={in_clusters.min()} median={int(in_clusters.median())} max={in_clusters.max()} mean={in_clusters.mean():.0f}")


if __name__ == "__main__":
    main()
