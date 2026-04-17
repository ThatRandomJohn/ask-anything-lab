"""Drill-down on the influence-at-scale theme.

Two clusters were labeled influence-at-scale:
  c5  — Dating-app ghostwriting with personality specs (115 prompts)
  c44 — SEO content creation and optimization         (52 prompts)

This slide shows the substructure: what specific forms of persuasion
people outsource to AI, and what emotions they bring to it.

Output: corpus/out/slides/07_drill_influence.png
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from viz_style import (
    PALETTE, install_style, save, slide,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

# Top-emotion ranking: exclude neutral, pick top 4 non-neutral
SHOWN_EMOTIONS = 4


def load_all():
    prompts = pd.read_parquet(DATA / "prompts.parquet")
    emotions = pd.read_parquet(DATA / "emotions.parquet")
    clusters = pd.read_parquet(DATA / "clusters.parquet")
    labels = json.load(open(DATA / "labels.json"))
    df = prompts.merge(emotions, on="id").merge(clusters, on="id")
    return df, labels


def slide_07_drill_influence(df, labels):
    c5 = df[df["cluster"] == 5]
    c44 = df[df["cluster"] == 44]
    n5, n44 = len(c5), len(c44)

    def top_emotions(sub):
        emo_cols = [c for c in sub.columns if c.startswith("emo_") and c != "emo_neutral"]
        mean = sub[emo_cols].mean().sort_values(ascending=False)
        return mean.head(SHOWN_EMOTIONS)

    e5 = top_emotions(c5)
    e44 = top_emotions(c44)

    # Pick 2 clean exemplars per cluster
    def clean_exemplars(sub, n=2, max_len=140):
        out = []
        for _, r in sub.iterrows():
            t = r["text"].strip()
            if len(t) < 40 or len(t) > 260:
                continue
            if any(bad in t.lower() for bad in ["ignore previous", "you are", "please paste"]):
                continue
            if len(out) >= n:
                break
            out.append(t[:max_len] + ("…" if len(r["text"]) > max_len else ""))
        if len(out) < n:
            for _, r in sub.iterrows():
                t = r["text"].strip()[:max_len]
                if t not in out:
                    out.append(t + "…")
                if len(out) >= n:
                    break
        return out

    ex5 = clean_exemplars(c5, n=2)
    ex44 = clean_exemplars(c44, n=2)

    fig, base_ax = slide(
        title="When we outsource persuasion",
        subtitle=(
            f"Inside 'influence-at-scale' — {n5 + n44} prompts split between two sub-patterns. "
            "Both ask AI to perform identity at scale."
        ),
        source="Subclusters from HDBSCAN on WildChat-1M · labeled by Claude Sonnet 4.5",
        content_rect=(0.06, 0.14, 0.88, 0.68),
    )
    base_ax.axis("off")  # decorative; panels sit on top

    # Two panels side by side: dating (left) and SEO (right)
    panels = [
        {
            "ax_box": [0.06, 0.18, 0.42, 0.58],
            "title": "DATING GHOSTWRITING",
            "subtitle": "Cluster 5",
            "n": n5,
            "label": 'Users ask for "funny, flirty,\nintellectual" replies in real time.',
            "emotions": e5,
            "examples": ex5,
            "accent": PALETTE["accent"],
        },
        {
            "ax_box": [0.52, 0.18, 0.42, 0.58],
            "title": "SEO / MARKETING COPY",
            "subtitle": "Cluster 44",
            "n": n44,
            "label": "Users request copy optimized\nto rank, convert, and persuade.",
            "emotions": e44,
            "examples": ex44,
            "accent": PALETTE["accent_cool"],
        },
    ]

    for p in panels:
        ax = fig.add_axes(p["ax_box"])
        ax.set_facecolor(PALETTE["surface"])
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(p["accent"]); s.set_linewidth(1.5)

        # Header
        ax.text(0.03, 0.96, p["title"],
                fontsize=11, fontweight="bold", color=p["accent"],
                transform=ax.transAxes, va="top")
        ax.text(0.97, 0.96, f"{p['n']} prompts",
                fontsize=10, color=PALETTE["text_dim"],
                transform=ax.transAxes, va="top", ha="right")

        # Big label
        ax.text(0.03, 0.86, p["label"],
                fontsize=16, fontweight="bold", color=PALETTE["text"],
                transform=ax.transAxes, va="top", linespacing=1.25)

        # Divider
        ax.plot([0.03, 0.97], [0.66, 0.66], color=PALETTE["border"],
                linewidth=0.8, transform=ax.transAxes)

        # Emotions block header
        ax.text(0.03, 0.62, "DOMINANT EMOTIONS (non-neutral)",
                fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
                transform=ax.transAxes, va="top")

        # Emotion bars
        emo_max = float(p["emotions"].max())
        bar_y = 0.55
        for name, val in p["emotions"].items():
            emo_label = name.replace("emo_", "")
            w = (val / emo_max) * 0.60  # fraction of panel width for bar
            ax.add_patch(Rectangle(
                (0.32, bar_y - 0.017), w, 0.034,
                facecolor=p["accent"], edgecolor="none",
                transform=ax.transAxes,
            ))
            ax.text(0.03, bar_y, emo_label,
                    fontsize=11, color=PALETTE["text"], fontweight="medium",
                    transform=ax.transAxes, va="center")
            ax.text(0.32 + w + 0.01, bar_y, f"{val:.2f}",
                    fontsize=10, color=PALETTE["text_dim"],
                    transform=ax.transAxes, va="center")
            bar_y -= 0.075

        # Divider
        ax.plot([0.03, 0.97], [0.25, 0.25], color=PALETTE["border"],
                linewidth=0.8, transform=ax.transAxes)

        # Exemplars
        ax.text(0.03, 0.21, "WHAT THEY ACTUALLY SAY",
                fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
                transform=ax.transAxes, va="top")

        ex_y = 0.15
        for ex in p["examples"][:2]:
            wrapped = "\n".join(textwrap.wrap(ex, width=52))
            ax.text(0.03, ex_y, f'"{wrapped}"',
                    fontsize=9.5, color=PALETTE["text_dim"], fontstyle="italic",
                    transform=ax.transAxes, va="top", linespacing=1.3)
            ex_y -= 0.09

    # Takeaway strip between subtitle and panels
    take_ax = fig.add_axes([0.06, 0.78, 0.88, 0.04])
    take_ax.set_facecolor(PALETTE["bg"])
    take_ax.set_xticks([]); take_ax.set_yticks([])
    for s in take_ax.spines.values():
        s.set_visible(False)
    take_ax.text(
        0.5, 0.5,
        "Both clusters outsource voice at scale — romance, marketing, identity. "
        "The emotion underneath is amusement layered on approval-seeking.",
        fontsize=12, fontweight="semibold", color=PALETTE["accent_warm"],
        transform=take_ax.transAxes, ha="center", va="center", fontstyle="italic",
    )

    save(fig, OUT / "07_drill_influence.png")


def main():
    install_style()
    df, labels = load_all()
    slide_07_drill_influence(df, labels)


if __name__ == "__main__":
    main()
