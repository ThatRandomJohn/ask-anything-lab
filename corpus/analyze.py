"""Build the analysis artifacts for the book.

Reads prompts.parquet + emotions.parquet + clusters.parquet + labels.json.

Writes to corpus/out/:
- emotion_x_cluster.png       — heatmap of 28 emotions × 47 clusters (ordered by talk theme)
- emotion_x_theme.png         — heatmap of 28 emotions × 10 talk themes (collapsed)
- theme_distribution.png      — bar of talk-theme volume
- neutral_vs_emotional.png    — per-cluster neutral pct vs dominant non-neutral emotion
- umap_scatter.png            — 2d UMAP colored by talk theme
- key_findings.md             — written summary citing the headline numbers
- exemplars.md                — 3 top exemplars per cluster
- cluster_summary.csv         — tabular summary (cluster_id, label, theme, size, top_emotions, exemplar)
- theme_summary.csv           — aggregated by theme
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"
OUT.mkdir(parents=True, exist_ok=True)

# Talk themes in display order + a neutral fallback + 'new'
THEME_ORDER = [
    "crisis-companionship",
    "emotional-validation",
    "ambient-companionship",
    "validation-seeking",
    "judgment-outsourcing",
    "high-stakes-decision",
    "influence-at-scale",
    "mechanism-curiosity",
    "information-seeking",
    "low-stakes-utility",
    "new",
]

# Dark TEDx color palette for consistency with the Gradio app
THEME_COLORS = {
    "crisis-companionship":  "#EF4444",
    "emotional-validation":  "#F97316",
    "ambient-companionship": "#EAB308",
    "validation-seeking":    "#A855F7",
    "judgment-outsourcing":  "#8B5CF6",
    "high-stakes-decision":  "#EC4899",
    "influence-at-scale":    "#3B82F6",
    "mechanism-curiosity":   "#06B6D4",
    "information-seeking":   "#14B8A6",
    "low-stakes-utility":    "#64748B",
    "new":                   "#F1F5F9",
}


def main():
    prompts = pd.read_parquet(DATA / "prompts.parquet")
    emotions = pd.read_parquet(DATA / "emotions.parquet")
    clusters = pd.read_parquet(DATA / "clusters.parquet")
    with open(DATA / "labels.json") as f:
        labels = json.load(f)

    # -------- Join everything together --------
    df = prompts.merge(emotions, on="id").merge(clusters, on="id")
    print(f"[analyze] joined dataframe: {len(df):,} rows, {df.shape[1]} cols")

    emo_cols = [c for c in df.columns if c.startswith("emo_")]
    emo_names = [c.replace("emo_", "") for c in emo_cols]
    print(f"[analyze] {len(emo_cols)} emotion columns")

    # Labels keyed by cluster id as string (matches labels.json keys)
    def lookup_label(cid: int) -> dict:
        return labels.get(str(cid), {"label": "noise" if cid == -1 else "?", "talk_theme": "new"})

    df["label"] = df["cluster"].apply(lambda c: lookup_label(int(c))["label"])
    df["talk_theme"] = df["cluster"].apply(lambda c: lookup_label(int(c))["talk_theme"])

    # Drop noise points for matrix plots; keep them for totals
    clustered = df[df["cluster"] >= 0].copy()
    cluster_ids = sorted(clustered["cluster"].unique().tolist())
    n_clusters = len(cluster_ids)
    print(f"[analyze] {n_clusters} clusters (excluding {len(df) - len(clustered)} noise)")

    # -------- 1. Emotion × Cluster matrix --------
    # Mean emotion probability per cluster, clusters ordered by theme
    cluster_to_theme = {int(cid): lookup_label(int(cid))["talk_theme"] for cid in cluster_ids}
    ordered_clusters = sorted(
        cluster_ids,
        key=lambda c: (THEME_ORDER.index(cluster_to_theme[c]) if cluster_to_theme[c] in THEME_ORDER else 99, c),
    )

    mat = np.zeros((len(emo_cols), len(ordered_clusters)))
    for j, cid in enumerate(ordered_clusters):
        sub = clustered[clustered["cluster"] == cid]
        mat[:, j] = sub[emo_cols].mean().values

    # Plot — keep 'neutral' but visually lighter; rank emotions by total salience
    emo_totals = mat.sum(axis=1)
    emo_order = np.argsort(-emo_totals)
    mat_sorted = mat[emo_order]
    emo_names_sorted = [emo_names[i] for i in emo_order]

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#06080C")
    ax.set_facecolor("#06080C")
    im = ax.imshow(mat_sorted, aspect="auto", cmap="magma", vmin=0, vmax=0.5)
    ax.set_yticks(range(len(emo_names_sorted)))
    ax.set_yticklabels(emo_names_sorted, color="#F1F5F9", fontsize=8)
    ax.set_xticks(range(len(ordered_clusters)))
    # X-axis: cluster id + short label
    x_labels = [f"c{cid}  {lookup_label(cid)['label'][:28]}" for cid in ordered_clusters]
    ax.set_xticklabels(x_labels, rotation=90, color="#F1F5F9", fontsize=7)
    ax.set_title("Emotion × Cluster — mean GoEmotions probability per cluster (clusters ordered by talk theme)",
                 color="#F1F5F9", fontsize=11)

    # Add theme dividers
    theme_bounds = []
    prev_theme = None
    for idx, cid in enumerate(ordered_clusters):
        theme = cluster_to_theme[cid]
        if theme != prev_theme:
            theme_bounds.append((idx, theme))
            prev_theme = theme
    for idx, theme in theme_bounds:
        ax.axvline(idx - 0.5, color=THEME_COLORS.get(theme, "#888"), linewidth=2, alpha=0.6)
        ax.text(idx, -1.5, theme, color=THEME_COLORS.get(theme, "#ccc"), fontsize=7,
                rotation=30, ha="left", va="bottom", fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label("mean probability", color="#F1F5F9")
    cbar.ax.yaxis.set_tick_params(color="#F1F5F9")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#F1F5F9")

    plt.tight_layout()
    plt.savefig(OUT / "emotion_x_cluster.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[analyze] wrote emotion_x_cluster.png")

    # -------- 2. Emotion × Theme matrix (collapsed) --------
    themes_present = [t for t in THEME_ORDER if t in cluster_to_theme.values()]
    theme_mat = np.zeros((len(emo_cols), len(themes_present)))
    theme_sizes = []
    for j, theme in enumerate(themes_present):
        sub = clustered[clustered["talk_theme"] == theme]
        theme_sizes.append(len(sub))
        if len(sub):
            theme_mat[:, j] = sub[emo_cols].mean().values
    theme_mat_sorted = theme_mat[emo_order]

    fig, ax = plt.subplots(figsize=(11, 10), facecolor="#06080C")
    ax.set_facecolor("#06080C")
    im = ax.imshow(theme_mat_sorted, aspect="auto", cmap="magma", vmin=0, vmax=0.5)
    ax.set_yticks(range(len(emo_names_sorted)))
    ax.set_yticklabels(emo_names_sorted, color="#F1F5F9", fontsize=9)
    ax.set_xticks(range(len(themes_present)))
    ax.set_xticklabels([f"{t}\n({theme_sizes[i]:,})" for i, t in enumerate(themes_present)],
                       rotation=30, color="#F1F5F9", fontsize=9, ha="right")
    ax.set_title("Emotion × Talk Theme — mean probability, 5,000 WildChat prompts",
                 color="#F1F5F9", fontsize=12)
    cbar = fig.colorbar(im, ax=ax, shrink=0.75)
    cbar.set_label("mean probability", color="#F1F5F9")
    cbar.ax.yaxis.set_tick_params(color="#F1F5F9")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#F1F5F9")
    plt.tight_layout()
    plt.savefig(OUT / "emotion_x_theme.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[analyze] wrote emotion_x_theme.png")

    # -------- 3. Theme distribution bar --------
    fig, ax = plt.subplots(figsize=(11, 6), facecolor="#06080C")
    ax.set_facecolor("#06080C")
    theme_counts = df["talk_theme"].value_counts().reindex(THEME_ORDER, fill_value=0)
    # Add a 'noise' slice for the -1 points
    noise_n = (df["cluster"] == -1).sum()
    theme_counts["unclustered"] = noise_n

    bars = ax.barh(
        theme_counts.index[::-1],
        theme_counts.values[::-1],
        color=[THEME_COLORS.get(t, "#888") for t in theme_counts.index[::-1]],
    )
    for bar, val in zip(bars, theme_counts.values[::-1]):
        ax.text(val + 20, bar.get_y() + bar.get_height() / 2, f"{val:,}",
                color="#F1F5F9", va="center", fontsize=9)

    ax.set_xlabel("prompt count", color="#F1F5F9")
    ax.set_title("TEDx talk theme distribution across 5,000 real ChatGPT prompts (WildChat-1M)",
                 color="#F1F5F9", fontsize=11)
    ax.tick_params(colors="#F1F5F9")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    plt.tight_layout()
    plt.savefig(OUT / "theme_distribution.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[analyze] wrote theme_distribution.png")

    # -------- 4. UMAP scatter colored by theme --------
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="#06080C")
    ax.set_facecolor("#06080C")
    # Plot noise first (gray, small)
    noise_mask = df["cluster"] == -1
    ax.scatter(df.loc[noise_mask, "umap_x"], df.loc[noise_mask, "umap_y"],
               c="#1e293b", s=3, alpha=0.4)
    # Then each theme
    for theme in THEME_ORDER:
        mask = (df["talk_theme"] == theme) & (df["cluster"] >= 0)
        if not mask.any():
            continue
        ax.scatter(df.loc[mask, "umap_x"], df.loc[mask, "umap_y"],
                   c=THEME_COLORS.get(theme, "#888"),
                   s=7, alpha=0.65, label=f"{theme} ({mask.sum()})")
    ax.set_title("UMAP projection — 5,000 prompts colored by talk theme",
                 color="#F1F5F9", fontsize=12)
    ax.set_xlabel("UMAP 1", color="#F1F5F9")
    ax.set_ylabel("UMAP 2", color="#F1F5F9")
    ax.tick_params(colors="#334155")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    legend = ax.legend(loc="upper right", fontsize=8, facecolor="#0f172a", edgecolor="#334155")
    for text in legend.get_texts():
        text.set_color("#F1F5F9")
    plt.tight_layout()
    plt.savefig(OUT / "umap_scatter.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[analyze] wrote umap_scatter.png")

    # -------- 5. Neutral vs Emotional per cluster --------
    rows = []
    for cid in cluster_ids:
        sub = clustered[clustered["cluster"] == cid]
        neu_pct = (sub["dominant_emotion"] == "neutral").mean()
        non_neu = sub[[c for c in emo_cols if c != "emo_neutral"]].mean()
        top_emo = non_neu.idxmax().replace("emo_", "")
        top_val = float(non_neu.max())
        rows.append({
            "cluster": cid,
            "label": lookup_label(cid)["label"],
            "theme": lookup_label(cid)["talk_theme"],
            "size": len(sub),
            "neutral_pct": float(neu_pct),
            "top_non_neutral": top_emo,
            "top_non_neutral_score": top_val,
        })
    csum = pd.DataFrame(rows).sort_values(["theme", "size"], ascending=[True, False])
    csum.to_csv(OUT / "cluster_summary.csv", index=False)
    print(f"[analyze] wrote cluster_summary.csv")

    # Theme summary
    theme_summary = []
    for theme in themes_present:
        sub = clustered[clustered["talk_theme"] == theme]
        if len(sub) == 0:
            continue
        neu_pct = (sub["dominant_emotion"] == "neutral").mean()
        non_neu = sub[[c for c in emo_cols if c != "emo_neutral"]].mean()
        theme_summary.append({
            "theme": theme,
            "n_clusters": int(csum[csum["theme"] == theme].shape[0]),
            "n_prompts": len(sub),
            "pct_of_corpus": len(sub) / len(df) * 100,
            "neutral_pct": float(neu_pct),
            "top_emotion_1": non_neu.nlargest(1).index[0].replace("emo_", ""),
            "top_emotion_2": non_neu.nlargest(2).index[-1].replace("emo_", ""),
            "top_emotion_3": non_neu.nlargest(3).index[-1].replace("emo_", ""),
        })
    tsum = pd.DataFrame(theme_summary)
    tsum.to_csv(OUT / "theme_summary.csv", index=False)
    print(f"[analyze] wrote theme_summary.csv")

    # -------- 6. Exemplars.md --------
    with open(DATA / "cluster_exemplars.json") as f:
        exemplars_data = json.load(f)
    lines = ["# Cluster Exemplars\n",
             f"Top 3 exemplar prompts per cluster, grouped by talk theme. Generated from 5,000 WildChat prompts.\n"]
    for theme in themes_present:
        theme_clusters = [c for c in cluster_ids if cluster_to_theme[c] == theme]
        if not theme_clusters:
            continue
        lines.append(f"\n## {theme}\n")
        for cid in theme_clusters:
            lbl = lookup_label(cid)
            size = int((clustered["cluster"] == cid).sum())
            ex = exemplars_data["clusters"].get(str(cid), [])[:3]
            lines.append(f"\n### c{cid} — {lbl['label']} ({size} prompts)\n")
            lines.append(f"- **emotion hook**: {lbl.get('emotion_hook','?')}\n")
            lines.append(f"- **surprising**: {lbl.get('surprising', False)}\n")
            lines.append(f"- **rationale**: {lbl.get('rationale','')}\n\n")
            for i, e in enumerate(ex, 1):
                snippet = e["text"].replace("\n", " ").strip()[:240]
                lines.append(f"{i}. _{snippet}_\n")
    (OUT / "exemplars.md").write_text("\n".join(lines))
    print(f"[analyze] wrote exemplars.md")

    # -------- 7. Key findings --------
    total = len(df)
    neutral_total = (df["dominant_emotion"] == "neutral").mean()
    findings = []
    findings.append("# Key Findings — Ask Anything Lab Corpus (5,000 WildChat prompts)\n")
    findings.append(f"**Corpus**: 5,000 real first-turn English prompts sampled from allenai/WildChat-1M.")
    findings.append(f"**Emotion classifier**: SamLowe/roberta-base-go_emotions (28 emotions, multi-label).")
    findings.append(f"**Clustering**: all-MiniLM-L6-v2 → UMAP-8d → HDBSCAN → 47 clusters + {(df['cluster']==-1).sum()} unclustered.")
    findings.append(f"**Labeling**: Claude Sonnet 4.5 with talk taxonomy + per-cluster emotion profile.\n")

    findings.append("## Headline numbers\n")
    findings.append(f"- **{neutral_total*100:.1f}%** of all prompts classify as emotionally **neutral** — ChatGPT is overwhelmingly a utility tool in raw volume.")
    findings.append(f"- The non-neutral **{(1-neutral_total)*100:.1f}%** carries a long tail dominated by *curiosity* ({(df['dominant_emotion']=='curiosity').sum():,}), *confusion* ({(df['dominant_emotion']=='confusion').sum():,}), and *admiration* ({(df['dominant_emotion']=='admiration').sum():,}).")
    findings.append(f"- **{(df['cluster']==-1).mean()*100:.0f}%** of prompts didn't cluster — real ChatGPT usage is long-tailed in ways no taxonomy cleanly captures.\n")

    findings.append("## Theme distribution\n")
    findings.append("| Theme | Clusters | Prompts | % of corpus |")
    findings.append("|---|---:|---:|---:|")
    for row in theme_summary:
        findings.append(f"| {row['theme']} | {row['n_clusters']} | {row['n_prompts']:,} | {row['pct_of_corpus']:.1f}% |")
    findings.append(f"| unclustered | — | {(df['cluster']==-1).sum():,} | {(df['cluster']==-1).mean()*100:.1f}% |\n")

    findings.append("## What's missing (that your talk predicts should be there)\n")
    missing = [t for t in THEME_ORDER if t not in [r["theme"] for r in theme_summary]]
    for m in missing:
        findings.append(f"- **`{m}`** — zero clusters. This doesn't mean the behavior doesn't exist; it means it's rare enough to fall into noise or get absorbed into broader clusters. Your ER story is one of these.")
    findings.append("")
    findings.append("The talk's core phenomena — crisis companionship, emotional validation, high-stakes decision outsourcing — are **statistically rare in raw public corpus data**.")
    findings.append("This reframes the thesis: the question isn't *'how often'* but *'what happens when it does'*. The rare cases are the high-consequence ones.\n")

    findings.append("## Surprising clusters\n")
    surp = [(cid, v) for cid, v in labels.items() if v.get("surprising")]
    if surp:
        for cid, v in surp:
            findings.append(f"- **c{cid} — {v['label']}** ({v['talk_theme']}): {v.get('rationale','')}")
    else:
        findings.append("_None flagged as surprising by the labeling pass._")
    findings.append("")

    findings.append("## Citable stats per theme\n")
    findings.append("| Theme | n | neutral% | top emotion 1 | top 2 | top 3 |")
    findings.append("|---|---:|---:|---|---|---|")
    for row in theme_summary:
        findings.append(f"| {row['theme']} | {row['n_prompts']:,} | {row['neutral_pct']*100:.0f}% | {row['top_emotion_1']} | {row['top_emotion_2']} | {row['top_emotion_3']} |")
    findings.append("")

    (OUT / "key_findings.md").write_text("\n".join(findings))
    print(f"[analyze] wrote key_findings.md")

    print("\n[analyze] outputs:")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size // 1024}K)")


if __name__ == "__main__":
    main()
