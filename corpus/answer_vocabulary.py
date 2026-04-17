"""Slide: "The model's emotional vocabulary."

Top-12 mean emotion probabilities for GPT answers (drops neutral), ranked
descending, colored by the EMOTION_CMAP gradient. Right panel: three
editorial callouts about the AI's dominant register.

Output: corpus/out/slides/13_answer_vocabulary.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from viz_style import EMOTION_CMAP, PALETTE, install_style, save, slide

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

TOP_N = 12


def build_slide():
    gpt_emo = pd.read_parquet(DATA / "emotions_answers_gpt.parquet")
    n_gpt = len(gpt_emo)

    emo_cols = [c for c in gpt_emo.columns if c.startswith("emo_")]
    means = gpt_emo[emo_cols].mean().sort_values(ascending=False)
    # Drop neutral; keep top 12 others
    means = means.drop("emo_neutral")
    top = means.head(TOP_N)
    names = [n.replace("emo_", "") for n in top.index]
    vals = top.values

    fig, ax = slide(
        title="The model's emotional vocabulary.",
        subtitle=(
            f"Mean per-answer emotion probability across {n_gpt:,} GPT "
            "answers. Neutral excluded to reveal what the AI actually leans on."
        ),
        source="WildChat-1M assistant turns · Emotions: SamLowe/roberta-base-go_emotions",
        content_rect=(0.08, 0.13, 0.55, 0.66),
    )

    # Horizontal bars, colored along EMOTION_CMAP by rank (top = warmest color)
    y = np.arange(len(names))
    # Map rank to [0.35, 0.95] range of the colormap so the colors read
    cmap_ts = np.linspace(0.95, 0.38, len(names))
    colors = [EMOTION_CMAP(t) for t in cmap_ts]

    ax.barh(y, vals, color=colors, edgecolor=PALETTE["bg"], linewidth=0.8, height=0.72)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=12.5, color=PALETTE["text"], fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel("mean probability in GPT answer", color=PALETTE["text_dim"], fontsize=11)
    xmax = float(vals.max()) * 1.18
    ax.set_xlim(0, xmax)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["border"])
    ax.spines["bottom"].set_color(PALETTE["border"])

    # Value labels
    for i, v in enumerate(vals):
        ax.text(v + xmax * 0.01, i, f"{v:.2f}",
                va="center", fontsize=10, color=PALETTE["text"], fontweight="semibold")

    # -------- Right panel: three editorial callouts --------
    panel = fig.add_axes([0.68, 0.13, 0.26, 0.66])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent_warm"]); s.set_linewidth(1.2)

    panel.text(0.5, 0.965, "THREE READINGS",
               ha="center", va="top", fontsize=10, fontweight="bold",
               color=PALETTE["accent_warm"], transform=panel.transAxes)

    top3 = [(names[i], vals[i]) for i in range(3)]
    top3_txt = ", ".join(f"{n}" for n, _ in top3)

    # Least-used (the ones the model avoids)
    bottom = means.tail(5)
    bottom_names = [n.replace("emo_", "") for n in bottom.index][:5]
    avoided_txt = ", ".join(bottom_names[:4])

    callouts = [
        {
            "kicker": "THE TOP THREE",
            "headline": top3_txt,
            "body": "These three emotions show up in nearly every answer. The AI's center of gravity is curious approval.",
            "color": PALETTE["accent"],
        },
        {
            "kicker": "WHAT IT DOESN'T SAY",
            "headline": "almost never: disgust, anger, grief",
            "body": f"Rarest non-neutral labels across all answers: {avoided_txt}. The model has a vocabulary, and an anti-vocabulary.",
            "color": PALETTE["accent_cool"],
        },
        {
            "kicker": "PRESENCE WITHOUT JUDGMENT",
            "headline": "a warm and blameless voice",
            "body": "It cannot feel disgust. It cannot feel anger. It cannot feel grief. It can only approve, admire, and care. That's not wisdom. That's comfort.",
            "color": PALETTE["accent_warm"],
        },
    ]

    cy = 0.905
    for c in callouts:
        panel.text(0.07, cy, c["kicker"],
                   fontsize=8.5, fontweight="bold", color=c["color"],
                   transform=panel.transAxes, va="top")
        panel.text(0.07, cy - 0.030, c["headline"],
                   fontsize=11.5, fontweight="bold", color=PALETTE["text"],
                   transform=panel.transAxes, va="top", linespacing=1.2)
        # Wrap body to fit panel width
        import textwrap
        wrapped = "\n".join(textwrap.wrap(c["body"], width=32))
        panel.text(0.07, cy - 0.080, wrapped,
                   fontsize=8.8, color=PALETTE["text_dim"], fontstyle="italic",
                   transform=panel.transAxes, va="top", linespacing=1.35)
        cy -= 0.275

    save(fig, OUT / "13_answer_vocabulary.png")


def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)
    build_slide()


if __name__ == "__main__":
    main()
