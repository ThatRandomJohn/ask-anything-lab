"""Slide: "The AI answers warmer than you ask."

Grouped horizontal bar chart comparing mean emotion probability across
three populations on the same 5,000 prompts:
  · user prompts          (emotions.parquet)
  · GPT answers           (emotions_answers_gpt.parquet)
  · Claude Sonnet answers (emotions_answers_claude.parquet)

Plus a stat card panel showing neutral rates and the biggest deltas.

Output: corpus/out/slides/12_answer_warmth.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from viz_style import PALETTE, install_style, save, slide

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

TOP_N = 10


def load_means():
    prompts_emo = pd.read_parquet(DATA / "emotions.parquet")
    gpt_emo = pd.read_parquet(DATA / "emotions_answers_gpt.parquet")
    claude_path = DATA / "emotions_answers_claude.parquet"
    claude_emo = pd.read_parquet(claude_path) if claude_path.exists() else None

    emo_cols = [c for c in prompts_emo.columns if c.startswith("emo_")]
    emo_names = [c.replace("emo_", "") for c in emo_cols]

    prompt_mean = prompts_emo[emo_cols].mean().values
    gpt_mean = gpt_emo[emo_cols].mean().values
    claude_mean = claude_emo[emo_cols].mean().values if claude_emo is not None else None

    return emo_names, prompt_mean, gpt_mean, claude_mean, len(prompts_emo), len(gpt_emo), (len(claude_emo) if claude_emo is not None else 0)


def build_slide():
    emo_names, pm, gm, cm, n_prompts, n_gpt, n_claude = load_means()
    has_claude = cm is not None

    # Drop neutral from the bar comparison — put it on its own card
    neu_i = emo_names.index("neutral")
    keep = [i for i in range(len(emo_names)) if i != neu_i]

    # Rank emotions by a score that favors where the answer is warmest
    if has_claude:
        score = np.maximum(gm, cm) + 0.25 * pm
    else:
        score = gm + 0.25 * pm
    ranked = sorted(keep, key=lambda i: -score[i])[:TOP_N]
    names = [emo_names[i] for i in ranked]
    p_vals = [pm[i] for i in ranked]
    g_vals = [gm[i] for i in ranked]
    c_vals = [cm[i] for i in ranked] if has_claude else None

    neu_p, neu_g = pm[neu_i], gm[neu_i]
    neu_c = cm[neu_i] if has_claude else None

    subtitle_n = f"Mean per-prompt emotion probability · {n_prompts:,} prompts"
    if has_claude:
        subtitle_n += f" · {n_gpt:,} GPT answers · {n_claude:,} Claude answers"
    else:
        subtitle_n += f" · {n_gpt:,} GPT answers"

    fig, ax = slide(
        title="The AI answers warmer than you ask.",
        subtitle=(
            "Users ask questions (curiosity, confusion). The model replies with "
            "approval, admiration, and care. " + subtitle_n + "."
        ),
        source="Sources: WildChat-1M prompts + GPT answers · Claude Sonnet 4.5 answers · Emotions: SamLowe/roberta-base-go_emotions",
        content_rect=(0.18, 0.13, 0.50, 0.66),
    )

    y = np.arange(len(names))
    bar_h = 0.26 if has_claude else 0.36

    n_bars = 3 if has_claude else 2
    offsets = np.linspace(-(n_bars - 1) / 2, (n_bars - 1) / 2, n_bars) * bar_h

    color_prompt = PALETTE["accent"]       # magenta
    color_gpt    = PALETTE["accent_cool"]  # cyan
    color_claude = PALETTE["accent_warm"]  # orange

    ax.barh(y + offsets[0], p_vals, height=bar_h,
            color=color_prompt, edgecolor=PALETTE["bg"], linewidth=0.6,
            label=f"prompt · {n_prompts:,}")
    ax.barh(y + offsets[1], g_vals, height=bar_h,
            color=color_gpt, edgecolor=PALETTE["bg"], linewidth=0.6,
            label=f"GPT answer · {n_gpt:,}")
    if has_claude:
        ax.barh(y + offsets[2], c_vals, height=bar_h,
                color=color_claude, edgecolor=PALETTE["bg"], linewidth=0.6,
                label=f"Claude answer · {n_claude:,}")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=12, color=PALETTE["text"], fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel("mean probability", color=PALETTE["text_dim"], fontsize=11)
    xmax = max(max(p_vals), max(g_vals), max(c_vals) if has_claude else 0) * 1.22
    ax.set_xlim(0, xmax)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["border"])
    ax.spines["bottom"].set_color(PALETTE["border"])

    # Value labels on each bar
    label_offset = xmax * 0.008
    for i, pv in enumerate(p_vals):
        ax.text(pv + label_offset, i + offsets[0], f"{pv:.2f}",
                va="center", fontsize=8, color=color_prompt, fontweight="semibold")
    for i, gv in enumerate(g_vals):
        ax.text(gv + label_offset, i + offsets[1], f"{gv:.2f}",
                va="center", fontsize=8, color=color_gpt, fontweight="semibold")
    if has_claude:
        for i, cv in enumerate(c_vals):
            ax.text(cv + label_offset, i + offsets[2], f"{cv:.2f}",
                    va="center", fontsize=8, color=color_claude, fontweight="semibold")

    ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=PALETTE["text"])

    # -------- Right panel: neutral rates + deltas --------
    panel = fig.add_axes([0.72, 0.13, 0.22, 0.66])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    panel.text(0.5, 0.965, "NEUTRAL RATE",
               ha="center", va="top", fontsize=10, fontweight="bold",
               color=PALETTE["accent"], transform=panel.transAxes)

    # Three-column neutral display
    if has_claude:
        cols = [
            (0.18, f"{neu_p*100:.0f}%", "prompts", color_prompt),
            (0.50, f"{neu_g*100:.0f}%", "GPT", color_gpt),
            (0.82, f"{neu_c*100:.0f}%", "Claude", color_claude),
        ]
    else:
        cols = [
            (0.28, f"{neu_p*100:.0f}%", "prompts", color_prompt),
            (0.72, f"{neu_g*100:.0f}%", "GPT", color_gpt),
        ]

    for x, big, lbl, col in cols:
        panel.text(x, 0.88, big,
                   ha="center", va="center", fontsize=26, fontweight="black",
                   color=col, transform=panel.transAxes)
        panel.text(x, 0.76, lbl,
                   ha="center", va="center", fontsize=9.5, color=PALETTE["text_dim"],
                   transform=panel.transAxes)

    panel.plot([0.08, 0.92], [0.695, 0.695], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    # Biggest warmth deltas — GPT answer minus prompt (on non-neutral emotions)
    deltas = [(names[i], g_vals[i] - p_vals[i]) for i in range(len(names))]
    deltas.sort(key=lambda x: x[1], reverse=True)
    top3 = deltas[:3]

    panel.text(0.5, 0.655, "BIGGEST WARMTH LIFTS",
               fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
               transform=panel.transAxes, va="top", ha="center")
    panel.text(0.5, 0.625, "(GPT answer − prompt)",
               fontsize=7.5, color=PALETTE["text_muted"], fontstyle="italic",
               transform=panel.transAxes, va="top", ha="center")

    ly = 0.565
    for name, d in top3:
        panel.text(0.08, ly, name,
                   fontsize=11, color=PALETTE["text"], fontweight="semibold",
                   transform=panel.transAxes, va="top")
        sign = "+" if d >= 0 else "−"
        dcol = color_gpt if d >= 0 else color_prompt
        panel.text(0.92, ly, f"{sign}{abs(d):.2f}",
                   fontsize=11, color=dcol, fontweight="bold",
                   transform=panel.transAxes, va="top", ha="right")
        ly -= 0.07

    panel.plot([0.08, 0.92], [0.30, 0.30], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    panel.text(0.5, 0.27, "The warmest voice\nin the room",
               fontsize=13, fontweight="bold", color=PALETTE["text"],
               transform=panel.transAxes, va="top", ha="center", linespacing=1.2)
    panel.text(0.08, 0.17,
               "You come in blank. The AI\ncomes in warm. RLHF\noptimizes for satisfaction\n— this is what it looks like.\nApproval, admiration, care.\nBy design.",
               fontsize=8.8, color=PALETTE["text_dim"], fontstyle="italic",
               transform=panel.transAxes, va="top", linespacing=1.35)

    save(fig, OUT / "12_answer_warmth.png")


def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)
    build_slide()


if __name__ == "__main__":
    main()
