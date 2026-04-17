"""Overlay live audience prompts (from Supabase tedx_study) on the corpus UMAP map.

For each audience prompt, we embed it with the same sentence-transformer, find
the 5 nearest corpus neighbors in embedding space, and place the audience point
at the centroid of those neighbors' UMAP coordinates. This approximates UMAP
projection without requiring the original fitted model.

The slide works for any audience count (including 1). During the live talk, as
more rows arrive in Supabase, re-running this script will re-render the slide.

Output: corpus/out/slides/08_audience_overlay.png
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from matplotlib.patches import FancyBboxPatch, Rectangle
from sentence_transformers import SentenceTransformer

from viz_style import (
    PALETTE, THEME_COLORS, THEME_ORDER, install_style, save, slide,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
K_NEAREST = 5


# --------------------------------------------------------------------------

def fetch_audience() -> pd.DataFrame:
    load_dotenv(str(Path(__file__).parent.parent / ".env"))
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from services.supabase_client import _get_client
    sb = _get_client()
    resp = sb.table("tedx_study").select("*").order("created_at", desc=False).execute()
    rows = resp.data or []
    # Drop test rows
    rows = [r for r in rows if "TEST" not in (r.get("prompt") or "").upper()]
    df = pd.DataFrame(rows)
    return df


def load_corpus():
    prompts = pd.read_parquet(DATA / "prompts.parquet")
    clusters = pd.read_parquet(DATA / "clusters.parquet")
    emb = np.load(DATA / "embeddings.npy")
    df = prompts.merge(clusters, on="id")
    # Attach labels to theme
    import json
    labels = json.load(open(DATA / "labels.json"))
    def lookup(cid):
        if cid == -1:
            return "unclustered"
        return labels.get(str(cid), {}).get("talk_theme", "unclustered")
    df["talk_theme"] = df["cluster"].apply(lambda c: lookup(int(c)))
    return df, emb


def project_audience(audience_texts: list[str], corpus_emb: np.ndarray,
                     corpus_df: pd.DataFrame) -> np.ndarray:
    print(f"[audience] embedding {len(audience_texts)} prompts")
    model = SentenceTransformer(MODEL_ID)
    aud_emb = model.encode(audience_texts, normalize_embeddings=True,
                           show_progress_bar=False)

    # Cosine sim = dot product since both normalized
    sims = aud_emb @ corpus_emb.T  # (A, C)
    coords = np.zeros((len(audience_texts), 2), dtype=np.float32)
    for i in range(len(audience_texts)):
        top_k = np.argsort(-sims[i])[:K_NEAREST]
        coords[i, 0] = corpus_df.iloc[top_k]["umap_x"].mean()
        coords[i, 1] = corpus_df.iloc[top_k]["umap_y"].mean()
    return coords


# --------------------------------------------------------------------------

def slide_08_audience_overlay(corpus_df, audience_df, audience_xy):
    n = len(audience_df)

    fig, ax = slide(
        title="Where the audience lands",
        subtitle=(
            f"{n} prompt{'s' if n != 1 else ''} from tonight's audience, projected onto the WildChat map. "
            "Each live star sits near the corpus questions it most resembles."
        ),
        source="Audience prompts captured live from the Ask Anything Lab Gradio study · k=5 nearest neighbors in embedding space",
        content_rect=(0.06, 0.12, 0.68, 0.68),
    )

    # Background: all corpus points, faded
    noise = corpus_df[corpus_df["cluster"] == -1]
    ax.scatter(noise["umap_x"], noise["umap_y"], c=PALETTE["surface_hi"],
               s=5, alpha=0.35, linewidths=0)

    for theme in THEME_ORDER:
        sub = corpus_df[(corpus_df["talk_theme"] == theme) & (corpus_df["cluster"] >= 0)]
        if len(sub) == 0:
            continue
        ax.scatter(sub["umap_x"], sub["umap_y"],
                   c=THEME_COLORS[theme], s=8, alpha=0.38, linewidths=0)

    # Audience stars — big, glowing, pink
    for i, (px, py) in enumerate(audience_xy):
        # outer glow
        for r, a in [(420, 0.12), (260, 0.22), (150, 0.38)]:
            ax.scatter([px], [py], s=r, c=PALETTE["accent"], alpha=a,
                       linewidths=0, marker="o")
        # core star
        ax.scatter([px], [py], s=220, c="white", marker="*",
                   edgecolors=PALETTE["accent"], linewidths=1.5, zorder=10)

    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Callouts — one per audience prompt, max 3 callouts visible
    max_callouts = min(3, n)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xspan = xlim[1] - xlim[0]
    yspan = ylim[1] - ylim[0]

    callout_targets = [
        (xlim[0] + xspan * 0.05, ylim[1] - yspan * 0.10),
        (xlim[1] - xspan * 0.05, ylim[1] - yspan * 0.10),
        (xlim[1] - xspan * 0.05, ylim[0] + yspan * 0.10),
    ]
    for i in range(max_callouts):
        px, py = audience_xy[i]
        tx, ty = callout_targets[i]
        text = audience_df.iloc[i]["prompt"]
        wrapped = "\n".join(textwrap.wrap(f'"{text}"', width=28))
        ax.annotate(
            wrapped,
            xy=(px, py), xytext=(tx, ty),
            fontsize=11, color=PALETTE["text"], fontweight="medium",
            ha="left" if i == 0 else "right", va="top",
            bbox=dict(
                boxstyle="round,pad=0.55,rounding_size=0.35",
                facecolor=PALETTE["surface"],
                edgecolor=PALETTE["accent"],
                linewidth=1.5,
            ),
            arrowprops=dict(
                arrowstyle="->",
                color=PALETTE["accent"],
                linewidth=1.5,
                connectionstyle="arc3,rad=0.15",
            ),
            zorder=20,
        )

    # Right-side stats panel
    panel_ax = fig.add_axes([0.76, 0.12, 0.20, 0.68])
    panel_ax.set_facecolor(PALETTE["surface"])
    panel_ax.set_xticks([]); panel_ax.set_yticks([])
    for s in panel_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    panel_ax.text(0.5, 0.95, "LIVE AUDIENCE",
                  ha="center", va="top", fontsize=11, fontweight="bold",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)

    panel_ax.text(0.5, 0.82, f"{n}",
                  ha="center", va="center", fontsize=56, fontweight="black",
                  color=PALETTE["accent"], transform=panel_ax.transAxes)
    panel_ax.text(0.5, 0.66, "prompt" + ("s" if n != 1 else ""),
                  ha="center", va="center", fontsize=11, color=PALETTE["text_dim"],
                  transform=panel_ax.transAxes)

    # Aggregate where the audience landed
    if n > 0:
        # For each audience prompt, find their nearest neighbor's theme
        panel_ax.text(0.08, 0.55, "NEAREST NEIGHBORS",
                      fontsize=9, fontweight="bold", color=PALETTE["accent_warm"],
                      transform=panel_ax.transAxes, va="top")
        ly = 0.48
        for i, (px, py) in enumerate(audience_xy[:4]):
            # find nearest corpus theme
            d2 = (corpus_df["umap_x"] - px)**2 + (corpus_df["umap_y"] - py)**2
            nn = corpus_df.iloc[d2.values.argmin()]
            theme = nn["talk_theme"]
            color = THEME_COLORS.get(theme, PALETTE["text_dim"])
            panel_ax.add_patch(Rectangle((0.08, ly - 0.015), 0.06, 0.025,
                                         facecolor=color,
                                         transform=panel_ax.transAxes))
            panel_ax.text(0.17, ly, theme,
                          fontsize=9, color=PALETTE["text"],
                          transform=panel_ax.transAxes, va="center")
            ly -= 0.055

    # Bottom note
    panel_ax.text(0.08, 0.14,
                  "Watch this space.\nAs the talk progresses,\nevery submitted prompt\nlands here in real time.",
                  fontsize=9.5, color=PALETTE["text_dim"], fontstyle="italic",
                  transform=panel_ax.transAxes, va="top", linespacing=1.35)

    save(fig, OUT / "08_audience_overlay.png")


# --------------------------------------------------------------------------

def main():
    install_style()
    audience_df = fetch_audience()
    print(f"[audience] fetched {len(audience_df)} prompts")
    if len(audience_df) == 0:
        print("[audience] no prompts — slide will be empty")
        return

    corpus_df, corpus_emb = load_corpus()
    audience_xy = project_audience(audience_df["prompt"].tolist(), corpus_emb, corpus_df)
    slide_08_audience_overlay(corpus_df, audience_df, audience_xy)


if __name__ == "__main__":
    main()
