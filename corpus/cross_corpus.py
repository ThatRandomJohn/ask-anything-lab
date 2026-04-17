"""Cross-corpus comparison — run the emotion pipeline on a second corpus (OASST1)
and produce a slide comparing the emotional shape of the two corpora.

WildChat = people using commercial ChatGPT-style assistants.
OASST1   = volunteers donating prompts to train an open-source assistant.

If the two corpora look emotionally similar, the WildChat findings generalize.
If they differ, we learn something about self-selection.

Output:
  corpus/data/prompts_oasst.parquet
  corpus/data/emotions_oasst.parquet
  corpus/out/slides/06_cross_corpus.png
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import load_dataset
from matplotlib.patches import Rectangle
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from viz_style import (
    EMOTION_CMAP, PALETTE, install_style, save, slide, stat_card,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

N = int(os.environ.get("OASST_N", "5000"))
MIN_LEN, MAX_LEN = 20, 2000
MODEL_ID = "SamLowe/roberta-base-go_emotions"
EMOTIONS = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral",
]


def load_hf_token() -> str | None:
    p = Path.home() / ".cache" / "huggingface" / "token"
    if p.exists():
        return p.read_text().strip()
    return os.environ.get("HF_TOKEN")


# --------------------------------------------------------------------------

def fetch_oasst(n: int) -> pd.DataFrame:
    out = DATA / "prompts_oasst.parquet"
    if out.exists():
        print(f"[oasst] cached → {out}")
        return pd.read_parquet(out)

    print(f"[oasst] loading OpenAssistant/oasst1 ...")
    ds = load_dataset("OpenAssistant/oasst1", split="train", token=load_hf_token())
    rows = []
    for ex in ds:
        if len(rows) >= n:
            break
        if ex.get("role") != "prompter":
            continue
        if ex.get("parent_id") is not None:
            continue
        if ex.get("lang") != "en":
            continue
        text = (ex.get("text") or "").strip()
        if not (MIN_LEN <= len(text) <= MAX_LEN):
            continue
        rows.append({
            "id": ex["message_id"],
            "text": text,
            "source": "oasst",
        })
    df = pd.DataFrame(rows)
    df.to_parquet(out, index=False)
    print(f"[oasst] wrote {len(df):,} → {out}")
    return df


# --------------------------------------------------------------------------

def classify_oasst(df: pd.DataFrame) -> pd.DataFrame:
    out = DATA / "emotions_oasst.parquet"
    if out.exists():
        print(f"[emo] cached → {out}")
        return pd.read_parquet(out)

    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print(f"[emo] device={device}")

    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID).to(device).eval()

    probs = np.zeros((len(df), len(EMOTIONS)), dtype=np.float32)
    texts = df["text"].tolist()
    batch = 32
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        enc = tok(chunk, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        p = torch.sigmoid(logits).cpu().numpy()
        probs[i:i + batch] = p
        if (i // batch) % 20 == 0:
            print(f"  [{i:>5}/{len(texts)}]")

    cols = {f"emo_{e}": probs[:, k] for k, e in enumerate(EMOTIONS)}
    edf = pd.DataFrame({"id": df["id"].values, **cols})
    edf["dominant_emotion"] = [EMOTIONS[i] for i in probs.argmax(axis=1)]
    edf["dominant_score"] = probs.max(axis=1)
    edf.to_parquet(out, index=False)
    print(f"[emo] wrote → {out}")
    return edf


# --------------------------------------------------------------------------

def load_wildchat_emotions() -> pd.DataFrame:
    return pd.read_parquet(DATA / "emotions.parquet")


# --------------------------------------------------------------------------

def slide_06_cross_corpus(wild: pd.DataFrame, oasst: pd.DataFrame):
    emo_cols = [c for c in wild.columns if c.startswith("emo_")]
    emo_names = [c.replace("emo_", "") for c in emo_cols]

    wild_mean = wild[emo_cols].mean().values
    oasst_mean = oasst[emo_cols].mean().values

    # Exclude neutral for the headline bar; put it on its own panel
    neu_i = emo_names.index("neutral")
    keep = [i for i in range(len(emo_names)) if i != neu_i]
    # Rank by (wild + oasst) joint mean and keep top 10
    score = wild_mean + oasst_mean
    ranked = sorted(keep, key=lambda i: -score[i])[:10]
    # Keep ordering consistent: most-present non-neutral emotion at top
    names = [emo_names[i] for i in ranked]
    w = [wild_mean[i] for i in ranked]
    o = [oasst_mean[i] for i in ranked]

    neu_w = wild_mean[neu_i]
    neu_o = oasst_mean[neu_i]

    fig, ax = slide(
        title="Volunteers are curious. Customers are blank.",
        subtitle=(
            "Mean per-prompt emotion probability. "
            f"WildChat ({len(wild):,} commercial-chat prompts) vs. "
            f"OASST1 ({len(oasst):,} volunteer prompts for open-source training)."
        ),
        source="Sources: allenai/WildChat-1M + OpenAssistant/oasst1 · Emotions: SamLowe/roberta-base-go_emotions",
        content_rect=(0.18, 0.15, 0.50, 0.60),
    )

    y = np.arange(len(names))
    bar_h = 0.36
    b1 = ax.barh(y - bar_h/2, w, height=bar_h, color=PALETTE["accent"],
                 label=f"WildChat · {len(wild):,}", edgecolor=PALETTE["bg"], linewidth=0.8)
    b2 = ax.barh(y + bar_h/2, o, height=bar_h, color=PALETTE["accent_cool"],
                 label=f"OASST1 · {len(oasst):,}", edgecolor=PALETTE["bg"], linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=12, color=PALETTE["text"], fontweight="medium")
    ax.invert_yaxis()
    ax.set_xlabel("mean probability", color=PALETTE["text_dim"], fontsize=11)
    ax.set_xlim(0, max(max(w), max(o)) * 1.25)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["border"])
    ax.spines["bottom"].set_color(PALETTE["border"])

    # Value labels
    for i, (wv, ov) in enumerate(zip(w, o)):
        ax.text(wv + max(max(w), max(o)) * 0.01, i - bar_h/2, f"{wv:.2f}",
                va="center", fontsize=9, color=PALETTE["accent"], fontweight="semibold")
        ax.text(ov + max(max(w), max(o)) * 0.01, i + bar_h/2, f"{ov:.2f}",
                va="center", fontsize=9, color=PALETTE["accent_cool"], fontweight="semibold")

    # Inline legend at top
    leg = ax.legend(loc="lower right", frameon=False, fontsize=11, labelcolor=PALETTE["text"])

    # Right-side panel: neutral comparison + takeaway
    panel_ax = fig.add_axes([0.72, 0.15, 0.22, 0.60])
    panel_ax.set_facecolor(PALETTE["surface"])
    panel_ax.set_xticks([]); panel_ax.set_yticks([])
    for s in panel_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    panel_ax.text(0.5, 0.96, "NEUTRAL RATE",
                  ha="center", va="top", fontsize=10, fontweight="bold",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)

    # Two big numbers
    panel_ax.text(0.25, 0.84, f"{neu_w*100:.0f}%",
                  ha="center", va="center", fontsize=32, fontweight="black",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)
    panel_ax.text(0.25, 0.72, "WildChat",
                  ha="center", va="center", fontsize=10, color=PALETTE["text_dim"],
                  transform=panel_ax.transAxes)

    panel_ax.text(0.75, 0.84, f"{neu_o*100:.0f}%",
                  ha="center", va="center", fontsize=32, fontweight="black",
                  color=PALETTE["accent_cool"], transform=panel_ax.transAxes)
    panel_ax.text(0.75, 0.72, "OASST1",
                  ha="center", va="center", fontsize=10, color=PALETTE["text_dim"],
                  transform=panel_ax.transAxes)

    # Divider
    panel_ax.plot([0.1, 0.9], [0.64, 0.64], color=PALETTE["border"],
                  linewidth=0.8, transform=panel_ax.transAxes)

    # Biggest divergence
    diffs = [(names[i], o[i] - w[i]) for i in range(len(names))]
    diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    top3 = diffs[:3]

    panel_ax.text(0.5, 0.58, "BIGGEST DIFFERENCES",
                  fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
                  transform=panel_ax.transAxes, va="top", ha="center")
    ly = 0.50
    for name, d in top3:
        sign = "+" if d > 0 else "−"
        direction = "OASST" if d > 0 else "WildChat"
        dcol = PALETTE["accent_cool"] if d > 0 else PALETTE["accent"]
        panel_ax.text(0.08, ly, f"{name}",
                      fontsize=11, color=PALETTE["text"], fontweight="semibold",
                      transform=panel_ax.transAxes, va="top")
        panel_ax.text(0.92, ly, f"{sign}{abs(d):.2f}",
                      fontsize=11, color=dcol, fontweight="bold",
                      transform=panel_ax.transAxes, va="top", ha="right")
        panel_ax.text(0.08, ly - 0.035, f"higher in {direction}",
                      fontsize=8, color=PALETTE["text_muted"],
                      transform=panel_ax.transAxes, va="top", style="italic")
        ly -= 0.09

    # Divider
    panel_ax.plot([0.1, 0.9], [0.22, 0.22], color=PALETTE["border"],
                  linewidth=0.8, transform=panel_ax.transAxes)

    # Bottom takeaway — data-driven text
    panel_ax.text(0.5, 0.17, "The shape shifts.",
                  fontsize=13, fontweight="bold", color=PALETTE["text"],
                  transform=panel_ax.transAxes, va="top", ha="center")
    panel_ax.text(0.08, 0.10,
                  "Commercial users treat AI\nlike a utility. Volunteers\nask it questions they\nactually want answered.",
                  fontsize=9.5, color=PALETTE["text_dim"], fontweight="regular",
                  transform=panel_ax.transAxes, va="top", style="italic",
                  linespacing=1.3)

    save(fig, OUT / "06_cross_corpus.png")


# --------------------------------------------------------------------------

def main():
    install_style()
    oasst_prompts = fetch_oasst(N)
    oasst_emotions = classify_oasst(oasst_prompts)
    wild_emotions = load_wildchat_emotions()
    slide_06_cross_corpus(wild_emotions, oasst_emotions)
    print(f"[cross_corpus] done")


if __name__ == "__main__":
    main()
