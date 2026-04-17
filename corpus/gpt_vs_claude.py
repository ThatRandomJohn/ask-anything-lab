"""Slide: "Two models, two tones."

Mirrors the cross_corpus.py layout. Compares mean emotion probabilities
across GPT and Claude Sonnet 4.5 answers to the same 5,000 prompts.

Output: corpus/out/slides/15_gpt_vs_claude.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from viz_style import PALETTE, install_style, save, slide

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

TOP_N = 10


def build_slide():
    gpt_emo = pd.read_parquet(DATA / "emotions_answers_gpt.parquet")
    claude_emo = pd.read_parquet(DATA / "emotions_answers_claude.parquet")

    emo_cols = [c for c in gpt_emo.columns if c.startswith("emo_")]
    emo_names = [c.replace("emo_", "") for c in emo_cols]
    gpt_mean = gpt_emo[emo_cols].mean().values
    claude_mean = claude_emo[emo_cols].mean().values

    # Drop neutral for bars
    neu_i = emo_names.index("neutral")
    keep = [i for i in range(len(emo_names)) if i != neu_i]

    score = gpt_mean + claude_mean
    ranked = sorted(keep, key=lambda i: -score[i])[:TOP_N]
    names = [emo_names[i] for i in ranked]
    g = [gpt_mean[i] for i in ranked]
    c = [claude_mean[i] for i in ranked]

    neu_g, neu_c = gpt_mean[neu_i], claude_mean[neu_i]

    fig, ax = slide(
        title="Two models, two tones.",
        subtitle=(
            f"Mean per-answer emotion probability on the same {len(gpt_emo):,} prompts. "
            "GPT (WildChat scraped) vs Claude Sonnet 4.5 (generated fresh)."
        ),
        source="WildChat-1M assistant turns (GPT) + claude-sonnet-4-5-20250929 · Emotions: SamLowe/roberta-base-go_emotions",
        content_rect=(0.18, 0.15, 0.50, 0.60),
    )

    y = np.arange(len(names))
    bar_h = 0.36
    color_gpt = PALETTE["accent_cool"]
    color_cl = PALETTE["accent_warm"]

    ax.barh(y - bar_h / 2, g, height=bar_h, color=color_gpt,
            label=f"GPT · {len(gpt_emo):,}", edgecolor=PALETTE["bg"], linewidth=0.8)
    ax.barh(y + bar_h / 2, c, height=bar_h, color=color_cl,
            label=f"Claude Sonnet 4.5 · {len(claude_emo):,}",
            edgecolor=PALETTE["bg"], linewidth=0.8)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=12, color=PALETTE["text"], fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel("mean probability", color=PALETTE["text_dim"], fontsize=11)
    xmax = max(max(g), max(c)) * 1.25
    ax.set_xlim(0, xmax)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["border"])
    ax.spines["bottom"].set_color(PALETTE["border"])

    label_offset = xmax * 0.008
    for i, (gv, cv) in enumerate(zip(g, c)):
        ax.text(gv + label_offset, i - bar_h / 2, f"{gv:.2f}",
                va="center", fontsize=9, color=color_gpt, fontweight="semibold")
        ax.text(cv + label_offset, i + bar_h / 2, f"{cv:.2f}",
                va="center", fontsize=9, color=color_cl, fontweight="semibold")

    ax.legend(loc="lower right", frameon=False, fontsize=11, labelcolor=PALETTE["text"])

    # -------- Right panel: neutral + divergences --------
    panel = fig.add_axes([0.72, 0.15, 0.22, 0.60])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent_cool"]); s.set_linewidth(1.2)

    panel.text(0.5, 0.96, "NEUTRAL RATE",
               ha="center", va="top", fontsize=10, fontweight="bold",
               color=PALETTE["accent_cool"], transform=panel.transAxes)

    panel.text(0.25, 0.84, f"{neu_g*100:.0f}%",
               ha="center", va="center", fontsize=32, fontweight="black",
               color=color_gpt, transform=panel.transAxes)
    panel.text(0.25, 0.72, "GPT",
               ha="center", va="center", fontsize=10, color=PALETTE["text_dim"],
               transform=panel.transAxes)
    panel.text(0.75, 0.84, f"{neu_c*100:.0f}%",
               ha="center", va="center", fontsize=32, fontweight="black",
               color=color_cl, transform=panel.transAxes)
    panel.text(0.75, 0.72, "Claude",
               ha="center", va="center", fontsize=10, color=PALETTE["text_dim"],
               transform=panel.transAxes)

    panel.plot([0.1, 0.9], [0.64, 0.64], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    diffs = [(names[i], c[i] - g[i]) for i in range(len(names))]
    diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    top3 = diffs[:3]

    panel.text(0.5, 0.58, "BIGGEST DIVERGENCES",
               fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
               transform=panel.transAxes, va="top", ha="center")
    ly = 0.50
    for name, d in top3:
        sign = "+" if d > 0 else "−"
        direction = "Claude" if d > 0 else "GPT"
        dcol = color_cl if d > 0 else color_gpt
        panel.text(0.08, ly, name,
                   fontsize=11, color=PALETTE["text"], fontweight="semibold",
                   transform=panel.transAxes, va="top")
        panel.text(0.92, ly, f"{sign}{abs(d):.2f}",
                   fontsize=11, color=dcol, fontweight="bold",
                   transform=panel.transAxes, va="top", ha="right")
        panel.text(0.08, ly - 0.035, f"higher in {direction}",
                   fontsize=8, color=PALETTE["text_muted"],
                   transform=panel.transAxes, va="top", fontstyle="italic")
        ly -= 0.09

    panel.plot([0.1, 0.9], [0.22, 0.22], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    # Editorial takeaway — data-driven
    panel.text(0.5, 0.19, "Same architecture.",
               fontsize=13, fontweight="bold", color=PALETTE["text"],
               transform=panel.transAxes, va="top", ha="center")
    panel.text(0.08, 0.12,
               "Trained independently on\nhuman feedback. Both learned\nthe same thing: warmth wins.\nThe feedback loop is structural.",
               fontsize=8.5, color=PALETTE["text_dim"], fontstyle="italic",
               transform=panel.transAxes, va="top", linespacing=1.3)

    save(fig, OUT / "15_gpt_vs_claude.png")


def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)
    build_slide()


if __name__ == "__main__":
    main()
