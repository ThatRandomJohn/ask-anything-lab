"""Presentation slide generator — main corpus findings.

Rewrites the original analyze.py outputs in slide format. Every figure is 16:9 with
title block, subtitle, source footer, and inline callouts pointing at the finding.

Outputs (in corpus/out/slides/):
- 01_headline.png         — three big stat cards
- 02_theme_distribution.png — horizontal bar with callouts
- 03_emotion_x_theme.png  — heatmap with annotations pointing at influence-at-scale
- 04_umap_map.png         — scatter with cluster anchors labeled
- 05_missing_themes.png   — "what's absent" slide
- 06_curiosity_base.png   — slide focused on curiosity-as-universal-base
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

from viz_style import (
    EMOTION_CMAP, PALETTE, THEME_COLORS, THEME_ORDER,
    add_callout, install_style, save, slide, stat_card, theme_legend,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"
OUT.mkdir(parents=True, exist_ok=True)


def load_all():
    prompts = pd.read_parquet(DATA / "prompts.parquet")
    emotions = pd.read_parquet(DATA / "emotions.parquet")
    clusters = pd.read_parquet(DATA / "clusters.parquet")
    with open(DATA / "labels.json") as f:
        labels = json.load(f)
    df = prompts.merge(emotions, on="id").merge(clusters, on="id")
    def lookup(cid: int) -> dict:
        if cid == -1:
            return {"label": "noise", "talk_theme": "unclustered"}
        return labels.get(str(cid), {"label": "?", "talk_theme": "unclustered"})
    df["talk_theme"] = df["cluster"].apply(lambda c: lookup(int(c))["talk_theme"])
    df["cluster_label"] = df["cluster"].apply(lambda c: lookup(int(c))["label"])
    return df, labels


# =========================================================================
def slide_01_headline(df):
    neu = (df["dominant_emotion"] == "neutral").mean()
    curiosity_count = (df["dominant_emotion"] == "curiosity").sum()
    noise_pct = (df["cluster"] == -1).mean()

    fig, ax = slide(
        title="What 5,000 people actually ask ChatGPT",
        subtitle="A random sample from WildChat-1M, classified for 28 emotions and clustered into 47 semantic groups.",
        source="Corpus: allenai/WildChat-1M · Emotions: SamLowe/roberta-base-go_emotions · Labeling: Claude Sonnet 4.5",
        content_rect=(0.06, 0.18, 0.88, 0.56),
    )
    ax.axis("off")

    # Three big stat cards
    w, h = 0.26, 0.38
    gap = 0.03
    total_w = 3 * w + 2 * gap
    x0 = (1 - total_w) / 2
    stat_card(fig, (x0, 0.22), (w, h),
              f"{neu*100:.0f}%", "of prompts classify as\nemotionally NEUTRAL",
              color=PALETTE["accent_cool"])
    stat_card(fig, (x0 + w + gap, 0.22), (w, h),
              f"{curiosity_count:,}", "prompts dominated by\nCURIOSITY — the next largest emotion",
              color=PALETTE["accent_warm"])
    stat_card(fig, (x0 + 2 * (w + gap), 0.22), (w, h),
              f"{noise_pct*100:.0f}%", "of prompts defy any\ntaxonomy we pre-defined",
              color=PALETTE["accent"])

    save(fig, OUT / "01_headline.png")


# =========================================================================
def slide_02_theme_distribution(df):
    fig, ax = slide(
        title="People don't come to ChatGPT the way we think they do",
        subtitle="Theme distribution across 5,000 real prompts. The emotional use cases you worry about are the rarest by volume.",
        content_rect=(0.18, 0.14, 0.50, 0.62),
    )

    counts = df["talk_theme"].value_counts()
    # Ensure every taxonomy theme shows up, even at zero
    for t in THEME_ORDER:
        if t not in counts.index:
            counts[t] = 0
    order = counts.sort_values(ascending=True)
    colors = [THEME_COLORS.get(t, PALETTE["surface_hi"]) for t in order.index]

    bars = ax.barh(range(len(order)), order.values, color=colors, edgecolor=PALETTE["bg"], linewidth=1.5, height=0.72)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order.index, fontsize=12, fontweight="medium", color=PALETTE["text"])
    ax.set_xlim(0, order.values.max() * 1.18)
    ax.set_xlabel("prompts", fontsize=11, color=PALETTE["text_dim"])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["border"])
    ax.spines["bottom"].set_color(PALETTE["border"])

    for i, (t, v) in enumerate(order.items()):
        ax.text(v + order.values.max() * 0.01, i, f"{v:,}",
                va="center", ha="left", fontsize=11, color=PALETTE["text"], fontweight="semibold")

    # Right-side takeaway panel
    panel_ax = fig.add_axes([0.72, 0.14, 0.22, 0.62])
    _ = panel_ax  # layout aligned with content_rect right edge
    panel_ax.set_facecolor(PALETTE["surface"])
    panel_ax.set_xticks([]); panel_ax.set_yticks([])
    for s in panel_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)
    panel_ax.text(0.5, 0.92, "THE STORY",
                  ha="center", va="top", fontsize=11, fontweight="bold",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)

    missing = [t for t in THEME_ORDER if t not in df["talk_theme"].values]
    panel_ax.text(0.08, 0.82,
        "low-stakes-utility\ndominates.",
        fontsize=14, fontweight="bold", color=PALETTE["text"],
        transform=panel_ax.transAxes, va="top")
    panel_ax.text(0.08, 0.68,
        "People treat AI like\na better search box —\nfor homework, code,\nemails, creative tasks.",
        fontsize=11, color=PALETTE["text_dim"],
        transform=panel_ax.transAxes, va="top")

    panel_ax.text(0.08, 0.46,
        "These never show up:",
        fontsize=11, fontweight="semibold", color=PALETTE["accent_warm"],
        transform=panel_ax.transAxes, va="top")
    missing_list = "\n".join(f"· {m}" for m in missing)
    panel_ax.text(0.08, 0.40, missing_list,
        fontsize=10, color=PALETTE["text_dim"],
        transform=panel_ax.transAxes, va="top")

    panel_ax.text(0.08, 0.12,
        "Your ER story lives in\nthe rare tail — and that's\nwhat makes it matter.",
        fontsize=10.5, fontweight="medium", color=PALETTE["text"],
        transform=panel_ax.transAxes, va="top", style="italic")

    save(fig, OUT / "02_theme_distribution.png")


# =========================================================================
def slide_03_emotion_x_theme(df):
    clustered = df[df["cluster"] >= 0].copy()
    emo_cols = [c for c in clustered.columns if c.startswith("emo_")]
    emo_names = [c.replace("emo_", "") for c in emo_cols]

    themes_present = [t for t in THEME_ORDER if t in clustered["talk_theme"].unique()]
    mat = np.zeros((len(emo_cols), len(themes_present)))
    sizes = []
    for j, theme in enumerate(themes_present):
        sub = clustered[clustered["talk_theme"] == theme]
        sizes.append(len(sub))
        if len(sub):
            mat[:, j] = sub[emo_cols].mean().values

    # Rank emotions by max signal across themes so rows with most variance rise to top
    # Exclude neutral to surface the non-neutral story
    variance = mat.std(axis=1)
    order = np.argsort(-variance)
    # Put neutral last for honesty
    neutral_i = emo_names.index("neutral")
    order = [i for i in order if i != neutral_i][:14] + [neutral_i]
    mat_s = mat[order]
    names_s = [emo_names[i] for i in order]

    fig, ax = slide(
        title="Influence-at-scale is the only emotionally loaded use case",
        subtitle="Mean emotion probability per talk theme. Neutral dominates everywhere — except where people are persuading others.",
        content_rect=(0.12, 0.20, 0.58, 0.56),
    )

    im = ax.imshow(mat_s, aspect="auto", cmap=EMOTION_CMAP, vmin=0, vmax=0.4)
    ax.set_yticks(range(len(names_s)))
    ax.set_yticklabels(names_s, fontsize=11, fontweight="medium", color=PALETTE["text"])
    ax.set_xticks(range(len(themes_present)))
    ax.set_xticklabels([f"{t}\n({sizes[i]:,})" for i, t in enumerate(themes_present)],
                       fontsize=10, color=PALETTE["text"], rotation=24, ha="right")

    # Add gridlines between themes for readability
    for x in range(1, len(themes_present)):
        ax.axvline(x - 0.5, color=PALETTE["bg"], linewidth=2)
    for y in range(1, len(names_s)):
        ax.axhline(y - 0.5, color=PALETTE["bg"], linewidth=1)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.78, pad=0.02)
    cbar.set_label("mean probability", color=PALETTE["text_dim"], fontsize=10)
    cbar.ax.yaxis.set_tick_params(color=PALETTE["text_dim"])
    cbar.outline.set_edgecolor(PALETTE["border"])
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=PALETTE["text_dim"])

    # Locate influence-at-scale column and highlight it
    if "influence-at-scale" in themes_present:
        col = themes_present.index("influence-at-scale")
        ax.add_patch(Rectangle(
            (col - 0.5, -0.5), 1, len(names_s),
            fill=False, edgecolor=PALETTE["accent"], linewidth=2.2, zorder=10,
        ))

    # Right-side takeaway panel
    panel_ax = fig.add_axes([0.74, 0.20, 0.22, 0.56])
    panel_ax.set_facecolor(PALETTE["surface"])
    panel_ax.set_xticks([]); panel_ax.set_yticks([])
    for s in panel_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    panel_ax.text(0.5, 0.94, "INFLUENCE-AT-SCALE",
                  ha="center", va="top", fontsize=10, fontweight="bold",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)
    panel_ax.text(0.08, 0.84,
        "The only column\nthat lights up.",
        fontsize=14, fontweight="bold", color=PALETTE["text"],
        transform=panel_ax.transAxes, va="top")
    panel_ax.text(0.08, 0.70,
        "amusement\ndesire\njoy\ngratitude\nlove",
        fontsize=11, color=PALETTE["accent_warm"], fontweight="semibold",
        transform=panel_ax.transAxes, va="top", linespacing=1.35)
    panel_ax.text(0.08, 0.43,
        "When people outsource\npersuasion to AI, they\nalso outsource the\nemotional texture of it —",
        fontsize=10.5, color=PALETTE["text_dim"],
        transform=panel_ax.transAxes, va="top")
    panel_ax.text(0.08, 0.19,
        "warmth, attraction,\nhumor, gratitude.",
        fontsize=11, color=PALETTE["text"], fontweight="semibold",
        transform=panel_ax.transAxes, va="top", style="italic")

    save(fig, OUT / "03_emotion_x_theme.png")


# =========================================================================
def slide_04_umap_map(df, labels):
    fig, ax = slide(
        title="A map of what people ask AI",
        subtitle="5,000 prompts embedded and projected to 2D. Colored by talk theme; gray dots are the 34% that resist any category.",
        content_rect=(0.06, 0.11, 0.68, 0.68),
    )

    # Noise layer
    noise = df[df["cluster"] == -1]
    ax.scatter(noise["umap_x"], noise["umap_y"], c=PALETTE["surface_hi"], s=6, alpha=0.55, linewidths=0)

    # Theme layers
    for theme in THEME_ORDER:
        sub = df[(df["talk_theme"] == theme) & (df["cluster"] >= 0)]
        if len(sub) == 0:
            continue
        ax.scatter(sub["umap_x"], sub["umap_y"],
                   c=THEME_COLORS[theme], s=12, alpha=0.82,
                   edgecolors="none", label=f"{theme} ({len(sub)})")

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Legend block
    legend_ax = fig.add_axes([0.76, 0.11, 0.20, 0.68])
    legend_ax.set_facecolor(PALETTE["surface"])
    legend_ax.set_xticks([]); legend_ax.set_yticks([])
    for s in legend_ax.spines.values():
        s.set_color(PALETTE["border"])
    legend_ax.text(0.5, 0.96, "THEMES PRESENT", ha="center", va="top",
                   fontsize=10, fontweight="bold", color=PALETTE["accent"],
                   transform=legend_ax.transAxes)

    present = [(t, (df["talk_theme"] == t).sum()) for t in THEME_ORDER if (df["talk_theme"] == t).sum() > 0]
    y = 0.88
    for theme, n in present:
        legend_ax.add_patch(Rectangle((0.08, y - 0.018), 0.09, 0.035,
                                      facecolor=THEME_COLORS[theme],
                                      transform=legend_ax.transAxes))
        legend_ax.text(0.22, y, f"{theme}",
                       fontsize=10, color=PALETTE["text"], fontweight="semibold",
                       transform=legend_ax.transAxes, va="center")
        legend_ax.text(0.94, y, f"{n:,}",
                       fontsize=10, color=PALETTE["text_dim"],
                       transform=legend_ax.transAxes, va="center", ha="right")
        y -= 0.06

    # Missing list
    missing = [t for t in THEME_ORDER if t not in [p[0] for p in present]]
    legend_ax.text(0.5, y - 0.02, "NOT IN SAMPLE", ha="center", va="top",
                   fontsize=9, fontweight="bold", color=PALETTE["text_muted"],
                   transform=legend_ax.transAxes)
    y -= 0.08
    for m in missing:
        legend_ax.text(0.5, y, m, fontsize=9, color=PALETTE["text_muted"],
                       transform=legend_ax.transAxes, ha="center", va="center")
        y -= 0.035

    save(fig, OUT / "04_umap_map.png")


# =========================================================================
def slide_05_curiosity_base(df):
    clustered = df[df["cluster"] >= 0]
    themes_present = [t for t in THEME_ORDER if t in clustered["talk_theme"].unique()]

    curiosity_by_theme = []
    for t in themes_present:
        sub = clustered[clustered["talk_theme"] == t]
        curiosity_by_theme.append(sub["emo_curiosity"].mean())

    fig, ax = slide(
        title="Curiosity is the universal base emotion",
        subtitle="Mean 'curiosity' probability per talk theme. Before fear, before joy, before frustration — people come to AI wondering.",
        content_rect=(0.18, 0.14, 0.50, 0.62),
    )

    order = np.argsort(curiosity_by_theme)[::-1]
    themes_sorted = [themes_present[i] for i in order]
    vals = [curiosity_by_theme[i] for i in order]
    colors = [THEME_COLORS[t] for t in themes_sorted]

    ax.barh(range(len(themes_sorted)), vals[::-1], color=colors[::-1],
            edgecolor=PALETTE["bg"], linewidth=1.2, height=0.72)
    ax.set_yticks(range(len(themes_sorted)))
    ax.set_yticklabels(themes_sorted[::-1], fontsize=12, fontweight="medium", color=PALETTE["text"])
    ax.set_xlabel("mean curiosity probability", fontsize=11, color=PALETTE["text_dim"])
    ax.set_xlim(0, max(vals) * 1.18)
    for i, v in enumerate(vals[::-1]):
        ax.text(v + max(vals) * 0.01, i, f"{v:.2f}",
                va="center", fontsize=11, color=PALETTE["text"], fontweight="semibold")

    # Big quote panel on the right
    q = fig.add_axes([0.72, 0.14, 0.22, 0.62])
    q.set_facecolor(PALETTE["bg"])
    q.set_xticks([]); q.set_yticks([])
    for s in q.spines.values():
        s.set_visible(False)
    q.text(0.0, 0.95, "“",
           fontsize=96, fontweight="black", color=PALETTE["accent"],
           transform=q.transAxes, va="top")
    q.text(0.0, 0.78,
        "People don't\ncome to AI\nafraid.",
        fontsize=22, fontweight="black", color=PALETTE["text"],
        transform=q.transAxes, va="top", linespacing=1.1)
    q.text(0.0, 0.50,
        "They come\nwondering.",
        fontsize=22, fontweight="black", color=PALETTE["accent_warm"],
        transform=q.transAxes, va="top", linespacing=1.1)
    q.text(0.0, 0.22,
        "The intervention moment\nis before fluency\nbecomes trust.",
        fontsize=11, color=PALETTE["text_dim"],
        transform=q.transAxes, va="top")

    save(fig, OUT / "05_curiosity_base.png")


# =========================================================================
def main():
    install_style()
    df, labels = load_all()
    print(f"[slides_main] {len(df):,} rows loaded")
    slide_01_headline(df)
    slide_02_theme_distribution(df)
    slide_03_emotion_x_theme(df)
    slide_04_umap_map(df, labels)
    slide_05_curiosity_base(df)
    print(f"[slides_main] all slides written to {OUT}")


if __name__ == "__main__":
    main()
