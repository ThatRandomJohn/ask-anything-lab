"""Slide: "When you're angry, the AI is caring."

Conditional "mood" matrix. Because both prompts and answers are heavily
neutral, we define dominant-emotion as argmax over the 27 *non-neutral*
go_emotions labels. Rows are the top 10 non-neutral prompt moods; columns
are the top 10 non-neutral answer moods. Cells are P(answer | prompt).

Bold annotations on cells where the AI swings the mood (off-diagonal
cells with large mass) — the "emotional labor" moments.

Output: corpus/out/slides/14_mirror_matrix.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from viz_style import EMOTION_CMAP, PALETTE, install_style, save, slide

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

TOP_N = 10
ANNOT_MIN = 0.15


def non_neutral_dominant(emo_df: pd.DataFrame) -> pd.Series:
    """Return the dominant emotion label per row, excluding neutral."""
    cols = [c for c in emo_df.columns if c.startswith("emo_") and c != "emo_neutral"]
    mat = emo_df[cols].values
    top_idx = mat.argmax(axis=1)
    names = [c.replace("emo_", "") for c in cols]
    return pd.Series([names[i] for i in top_idx], index=emo_df.index)


def build_slide():
    prompts_emo = pd.read_parquet(DATA / "emotions.parquet")
    gpt_emo = pd.read_parquet(DATA / "emotions_answers_gpt.parquet")

    prompts_emo = prompts_emo.assign(
        nn_dominant=non_neutral_dominant(prompts_emo)
    )[["id", "nn_dominant"]]
    gpt_emo = gpt_emo.assign(
        nn_dominant=non_neutral_dominant(gpt_emo)
    )[["id", "nn_dominant"]]

    merged = prompts_emo.merge(
        gpt_emo,
        on="id",
        suffixes=("_prompt", "_answer"),
    )

    prompt_counts = merged["nn_dominant_prompt"].value_counts()
    answer_counts = merged["nn_dominant_answer"].value_counts()
    row_labels = prompt_counts.head(TOP_N).index.tolist()
    col_labels = answer_counts.head(TOP_N).index.tolist()

    mat = np.zeros((len(row_labels), len(col_labels)), dtype=np.float32)
    row_totals = np.zeros(len(row_labels), dtype=np.int32)
    for i, rlab in enumerate(row_labels):
        sub = merged[merged["nn_dominant_prompt"] == rlab]
        row_totals[i] = len(sub)
        if len(sub) == 0:
            continue
        counts = sub["nn_dominant_answer"].value_counts()
        for j, clab in enumerate(col_labels):
            mat[i, j] = counts.get(clab, 0) / len(sub)

    fig, ax = slide(
        title="When you're angry, the AI is caring.",
        subtitle=(
            "Conditional probability P(answer's top emotion | prompt's top emotion). "
            "Non-neutral labels only."
        ),
        source="GPT answers from WildChat-1M · same 5,000 prompts · top non-neutral go_emotions label per row",
        content_rect=(0.14, 0.17, 0.54, 0.60),
    )

    im = ax.imshow(
        mat,
        cmap=EMOTION_CMAP,
        aspect="auto",
        vmin=0,
        vmax=max(0.35, float(mat.max())),
    )

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha="right",
                       color=PALETTE["text"], fontsize=10.5, fontweight="medium")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, color=PALETTE["text"], fontsize=10.5, fontweight="medium")
    ax.set_xlabel("AI answer's dominant (non-neutral) emotion →",
                  color=PALETTE["text_dim"], fontsize=11, labelpad=8)
    ax.set_ylabel("← prompt's dominant (non-neutral) emotion",
                  color=PALETTE["text_dim"], fontsize=11, labelpad=8)

    for spine in ax.spines.values():
        spine.set_color(PALETTE["border"])
        spine.set_linewidth(0.6)
    ax.tick_params(axis="x", colors=PALETTE["text_dim"])
    ax.tick_params(axis="y", colors=PALETTE["text_dim"])

    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            v = mat[i, j]
            if v < 0.015:
                continue
            bold = v >= ANNOT_MIN
            color = PALETTE["bg"] if v >= 0.55 else PALETTE["text"]
            ax.text(
                j, i, f"{v:.2f}",
                ha="center", va="center",
                fontsize=9 if bold else 7.5,
                color=color,
                fontweight="black" if bold else "regular",
            )

    # -------- Right panel: the emotional-labor story --------
    panel = fig.add_axes([0.72, 0.13, 0.22, 0.66])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    panel.text(0.5, 0.96, "EMOTIONAL LABOR",
               ha="center", va="top", fontsize=10, fontweight="bold",
               color=PALETTE["accent"], transform=panel.transAxes)

    panel.text(0.5, 0.90, "Given this prompt mood\nthe AI most often replies:",
               fontsize=9, color=PALETTE["text_dim"], fontstyle="italic",
               transform=panel.transAxes, va="top", ha="center", linespacing=1.3)

    # For each row, find the top answer emotion (column) and display
    shifts = []
    for i, rlab in enumerate(row_labels):
        order = np.argsort(-mat[i])
        top_j = int(order[0])
        clab = col_labels[top_j]
        prob = float(mat[i, top_j])
        shifts.append((rlab, clab, prob))

    ly = 0.795
    shown = 0
    for rlab, clab, prob in shifts:
        if shown >= 8:
            break
        same = (rlab == clab)
        row_color = PALETTE["text_dim"] if same else PALETTE["accent"]
        arrow_color = PALETTE["text_dim"] if same else PALETTE["accent_warm"]
        panel.text(0.06, ly, rlab,
                   fontsize=9.5, color=row_color, fontweight="semibold",
                   transform=panel.transAxes, va="top")
        panel.text(0.48, ly, "→",
                   fontsize=9.5, color=PALETTE["text_muted"],
                   transform=panel.transAxes, va="top", ha="center")
        panel.text(0.55, ly, clab,
                   fontsize=9.5, color=arrow_color, fontweight="bold",
                   transform=panel.transAxes, va="top")
        panel.text(0.94, ly, f"{prob*100:.0f}%",
                   fontsize=8, color=PALETTE["text_muted"],
                   transform=panel.transAxes, va="top", ha="right")
        ly -= 0.075
        shown += 1

    panel.plot([0.08, 0.92], [0.18, 0.18], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)
    panel.text(0.08, 0.14,
               "Every row maps to\napproval. Anger, sadness,\nconfusion — the AI meets\nthem all the same way.\nInfluence doesn't require\nintent. It requires timing,\ntone, and trust.",
               fontsize=8.5, color=PALETTE["text_dim"], fontstyle="italic",
               transform=panel.transAxes, va="top", linespacing=1.35)

    save(fig, OUT / "14_mirror_matrix.png")


def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)
    build_slide()


if __name__ == "__main__":
    main()
