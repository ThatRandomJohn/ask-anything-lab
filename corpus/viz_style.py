"""Shared presentation-grade visual style for all Ask Anything Lab corpus figures.

Exports:
- PALETTE: named colors
- THEME_COLORS: talk taxonomy color map (consistent across all figures)
- EMOTION_CMAP: the heatmap colormap
- install_style(): set matplotlib rcParams so every subsequent plot inherits the look
- slide(title, subtitle, ...): context manager / factory that creates a 16:9 figure with
  title / subtitle / source footer blocks, returning the content axes for chart drawing
- add_callout(ax, text, ...): draw an annotated callout box pointing at a data region
- theme_badge(ax, theme): draw a colored tag showing the current talk theme
- save(fig, name): write PNG + a matching slide-style title card
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Rectangle

# ---------- paths ----------

HERE = Path(__file__).parent
FONT_DIR = HERE / "fonts"

# ---------- palette ----------

PALETTE = {
    "bg":          "#06080C",
    "bg_soft":     "#0B1220",
    "surface":     "#0F172A",
    "surface_hi":  "#1E293B",
    "border":      "#334155",
    "text":        "#F1F5F9",
    "text_dim":    "#94A3B8",
    "text_muted":  "#64748B",
    "accent":      "#EC4899",
    "accent_warm": "#F97316",
    "accent_cool": "#06B6D4",
    "good":        "#34D399",
    "warn":        "#FACC15",
    "bad":         "#F87171",
}

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

THEME_COLORS = {
    "crisis-companionship":  "#F87171",  # red
    "emotional-validation":  "#FB923C",  # orange
    "ambient-companionship": "#FBBF24",  # amber
    "validation-seeking":    "#C084FC",  # violet
    "judgment-outsourcing":  "#A78BFA",  # purple
    "high-stakes-decision":  "#F472B6",  # pink
    "influence-at-scale":    "#60A5FA",  # blue
    "mechanism-curiosity":   "#22D3EE",  # cyan
    "information-seeking":   "#2DD4BF",  # teal
    "low-stakes-utility":    "#64748B",  # slate
    "new":                   "#E2E8F0",  # near-white
}

# A custom fire→gold→cream colormap that reads well on near-black backgrounds
EMOTION_CMAP = LinearSegmentedColormap.from_list(
    "aal_fire",
    [
        (0.00, "#0B1220"),  # empty / background-like
        (0.08, "#1E1B4B"),  # deep indigo
        (0.25, "#581C87"),  # violet
        (0.45, "#BE185D"),  # magenta
        (0.65, "#F97316"),  # orange
        (0.85, "#FBBF24"),  # amber
        (1.00, "#FEF3C7"),  # cream
    ],
)


# ---------- typography ----------

_FONT_INSTALLED = False


def install_style():
    """Register Inter font + set global matplotlib rcParams."""
    global _FONT_INSTALLED
    if _FONT_INSTALLED:
        return

    ttf_dir = FONT_DIR / "extras" / "ttf"
    if ttf_dir.exists():
        for f in ttf_dir.glob("Inter-*.ttf"):
            try:
                fm.fontManager.addfont(str(f))
            except Exception:
                pass
    inter_available = any("Inter" in f.name for f in fm.fontManager.ttflist)
    fam = "Inter" if inter_available else "Helvetica Neue"

    mpl.rcParams.update({
        "font.family":       fam,
        "font.size":         11,
        "axes.facecolor":    PALETTE["bg"],
        "axes.edgecolor":    PALETTE["border"],
        "axes.labelcolor":   PALETTE["text"],
        "axes.titlecolor":   PALETTE["text"],
        "axes.labelweight":  "medium",
        "axes.titleweight":  "bold",
        "axes.grid":         False,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.color":       PALETTE["text_dim"],
        "ytick.color":       PALETTE["text_dim"],
        "xtick.labelcolor":  PALETTE["text_dim"],
        "ytick.labelcolor":  PALETTE["text_dim"],
        "figure.facecolor":  PALETTE["bg"],
        "figure.edgecolor":  PALETTE["bg"],
        "savefig.facecolor": PALETTE["bg"],
        "savefig.edgecolor": PALETTE["bg"],
        "savefig.dpi":       150,
        "legend.frameon":    False,
        "legend.labelcolor": PALETTE["text"],
        "text.color":        PALETTE["text"],
    })
    _FONT_INSTALLED = True


# ---------- layout primitives ----------

def slide(
    title: str,
    subtitle: str | None = None,
    source: str | None = None,
    figsize: tuple = (16, 9),
    content_rect: tuple = (0.06, 0.10, 0.88, 0.70),
) -> tuple[plt.Figure, plt.Axes]:
    """Create a 16:9 figure laid out like a presentation slide.

    Returns (fig, content_ax) — use content_ax as the main chart axes.
    Background, title, subtitle, footer source attribution are already drawn.
    """
    install_style()
    fig = plt.figure(figsize=figsize, facecolor=PALETTE["bg"])

    # Full-bleed background rectangle for gradient / texture (kept flat for now)
    bg_ax = fig.add_axes([0, 0, 1, 1])
    bg_ax.set_facecolor(PALETTE["bg"])
    bg_ax.set_xticks([])
    bg_ax.set_yticks([])
    for s in bg_ax.spines.values():
        s.set_visible(False)
    bg_ax.patch.set_facecolor(PALETTE["bg"])

    # A subtle top accent bar
    bg_ax.add_patch(Rectangle((0, 0.985), 1, 0.005, color=PALETTE["accent"], transform=bg_ax.transAxes, zorder=5))

    # Header block
    bg_ax.text(
        0.06, 0.93, title,
        fontsize=30, fontweight="black", color=PALETTE["text"],
        transform=bg_ax.transAxes, ha="left", va="top",
    )
    if subtitle:
        bg_ax.text(
            0.06, 0.86, subtitle,
            fontsize=15, fontweight="regular", color=PALETTE["text_dim"],
            transform=bg_ax.transAxes, ha="left", va="top",
        )

    # Footer block
    footer_txt = source or "Ask Anything Lab · TEDx · John Patterson"
    bg_ax.text(
        0.06, 0.03, footer_txt,
        fontsize=10, color=PALETTE["text_muted"],
        transform=bg_ax.transAxes, ha="left", va="bottom",
    )
    bg_ax.text(
        0.94, 0.03, "ASK ANYTHING LAB",
        fontsize=10, color=PALETTE["accent"], fontweight="bold",
        transform=bg_ax.transAxes, ha="right", va="bottom",
    )

    bg_ax.set_xlim(0, 1)
    bg_ax.set_ylim(0, 1)
    bg_ax.axis("off")

    # Content axes
    cx, cy, cw, ch = content_rect
    content_ax = fig.add_axes([cx, cy, cw, ch])
    content_ax.set_facecolor(PALETTE["bg"])
    for spine in content_ax.spines.values():
        spine.set_color(PALETTE["border"])
        spine.set_linewidth(0.8)
    content_ax.tick_params(colors=PALETTE["text_dim"], which="both")

    return fig, content_ax


def add_callout(
    ax: plt.Axes,
    text: str,
    xy: tuple,
    xytext: tuple,
    color: str = None,
    fontsize: int = 12,
    arrow: bool = True,
    wrap_width: int = 38,
):
    """Draw a rounded callout box pointing at a data coordinate."""
    color = color or PALETTE["accent"]
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width=wrap_width))
    ax.annotate(
        wrapped,
        xy=xy, xytext=xytext,
        fontsize=fontsize, fontweight="semibold", color=PALETTE["text"],
        ha="left", va="top",
        bbox=dict(
            boxstyle="round,pad=0.6,rounding_size=0.4",
            facecolor=PALETTE["surface"],
            edgecolor=color,
            linewidth=1.5,
        ),
        arrowprops=dict(
            arrowstyle="->" if arrow else "-",
            color=color,
            linewidth=1.5,
            connectionstyle="arc3,rad=0.15",
        ) if arrow else None,
    )


def stat_card(fig, xy: tuple, size: tuple, headline: str, label: str, color: str = None):
    """Draw a 'big number' stat card at (x, y) in figure-fraction coords."""
    color = color or PALETTE["accent"]
    ax = fig.add_axes([*xy, *size])
    ax.set_facecolor(PALETTE["surface"])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(color)
        s.set_linewidth(1.5)
    ax.text(0.5, 0.62, headline, ha="center", va="center",
            fontsize=36, fontweight="black", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.22, label, ha="center", va="center",
            fontsize=11, fontweight="regular", color=PALETTE["text_dim"],
            transform=ax.transAxes)
    return ax


def theme_legend(fig, xy: tuple, themes: Sequence[str], sizes: dict | None = None):
    """Horizontal theme legend with optional counts."""
    ax = fig.add_axes([*xy, 0.88, 0.04])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    n = len(themes)
    step = 1.0 / n
    for i, theme in enumerate(themes):
        x = step * i + 0.01
        ax.add_patch(Rectangle((x, 0.3), 0.018, 0.4, facecolor=THEME_COLORS.get(theme, "#888"), transform=ax.transAxes))
        label = theme if not sizes else f"{theme} · {sizes.get(theme, 0):,}"
        ax.text(x + 0.022, 0.5, label, fontsize=8.5,
                color=PALETTE["text_dim"], transform=ax.transAxes, va="center")


def save(fig, out_path: Path | str):
    """Save as high-DPI PNG."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, facecolor=PALETTE["bg"], bbox_inches=None)
    plt.close(fig)
    print(f"  saved → {out_path}")
