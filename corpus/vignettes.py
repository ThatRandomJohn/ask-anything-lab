"""Sonnet-written literary vignettes for the three surprising clusters.

For each surprising cluster (c5, c11, c25) we ask Claude Sonnet 4.5 to write
a ~450-word second-person book vignette — an empathetic literary portrait of
the kind of person who sends that kind of prompt. The point is humanization,
not analysis.

Output:
  corpus/data/vignettes.json         (cached Sonnet output)
  corpus/out/slides/09_vignette_ghostwriter.png
  corpus/out/slides/10_vignette_patricia.png
  corpus/out/slides/11_vignette_collaborator.png
"""
from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from matplotlib.patches import Rectangle

from viz_style import (
    PALETTE, THEME_COLORS, install_style, save, slide,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

MODEL = "claude-sonnet-4-5-20250929"

# Hand-picked titles that match each cluster's emotional hook
SURPRISING = [
    {
        "cluster_id": 5,
        "slide_num": 9,
        "title": "The Ghostwriter",
        "deck_title": "The ghostwriter",
        "deck_subtitle": "Cluster 5 · 115 prompts · amusement masking social anxiety",
        "slug": "ghostwriter",
    },
    {
        "cluster_id": 11,
        "slide_num": 10,
        "title": "Patricia Bertier",
        "deck_title": "Patricia Bertier",
        "deck_subtitle": "Cluster 11 · 46 prompts · sadness as narrative device",
        "slug": "patricia",
    },
    {
        "cluster_id": 25,
        "slide_num": 11,
        "title": "The Collaborator",
        "deck_title": "The collaborator",
        "deck_subtitle": "Cluster 25 · 49 prompts · admiration, optimism, creative hope",
        "slug": "collaborator",
    },
]


# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a literary essayist writing short vignettes for a TEDx talk and companion book titled "Ask Anything: AI, Emotion, and Influence" by John Patterson.

The book's project is to humanize the people behind AI prompts — not to analyze them like data points, but to portray them the way a good novelist would: with empathy, specificity, and the texture of an inner life. Each vignette is a short book passage written in second-person, present-tense, addressed to an imagined reader who recognizes themselves in it.

You will receive a cluster of real ChatGPT prompts scraped from an open dataset, along with the cluster's dominant emotions and a title chosen by the author. Your job is to write the vignette.

STRICT REQUIREMENTS:
- Exactly one passage. Between 420 and 470 words. No headers. No bullet points. No lists.
- Second-person, present-tense ("You are sitting at your desk..."). Never use "I".
- Concrete, sensory, novelistic. Objects. Light. Weather. Specific times of day. A body in a room.
- Do NOT mention ChatGPT, AI, LLMs, prompts, models, or clusters by name. The reader knows the context — you are writing the *inside* of it.
- Do NOT moralize, judge, or explain the sociology. Trust the reader to feel it.
- Never sensationalize, never caricature. If the cluster is uncomfortable, sit inside the person's honest need rather than mocking it.
- Start the passage with a concrete physical action or sensory detail, not an idea.
- End with a small, specific image — never a thesis.

Respond ONLY with valid JSON matching this schema:

{
  "vignette": "The 420–470 word passage as a single string with \\n between paragraphs."
}

No markdown, no code fences, no commentary — just the JSON object."""


def build_user_message(cluster_info: dict, exemplars: list[dict], label: dict, title: str) -> str:
    emo_lines = []
    for name, val in label.get("top_non_neutral", [])[:5]:
        emo_lines.append(f"  · {name}: {val:.2f}")
    emo_block = "\n".join(emo_lines)

    ex_lines = []
    for ex in exemplars[:8]:
        t = ex["text"].strip().replace("\n", " ")
        if len(t) > 220:
            t = t[:220] + "…"
        ex_lines.append(f"  · {t}")
    ex_block = "\n".join(ex_lines)

    return f"""CLUSTER TITLE (author's chosen title for this vignette): {title}

CLUSTER LABEL: {label["label"]}
CLUSTER SIZE: {label["size"]} prompts
NEUTRAL SHARE: {label["neutral_pct"]:.0%}
EMOTION HOOK (the thing that makes it surprising): {label["emotion_hook"]}

TOP NON-NEUTRAL EMOTIONS:
{emo_block}

EXEMPLAR PROMPTS FROM THIS CLUSTER:
{ex_block}

Write the 420–470 word second-person vignette for this cluster. Return JSON only."""


# --------------------------------------------------------------------------

def generate_vignettes() -> dict:
    cache = DATA / "vignettes.json"
    if cache.exists():
        print(f"[vignettes] cached → {cache}")
        return json.loads(cache.read_text())

    load_dotenv(str(HERE.parent / ".env"))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — can't generate vignettes.")

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    labels = json.loads((DATA / "labels.json").read_text())
    exemplars_all = json.loads((DATA / "cluster_exemplars.json").read_text())["clusters"]

    out = {}
    for spec in SURPRISING:
        cid = spec["cluster_id"]
        label = labels[str(cid)]
        exemplars = exemplars_all[str(cid)]
        user_msg = build_user_message(spec, exemplars, label, spec["title"])

        print(f"[vignettes] asking Sonnet for c{cid} ({spec['title']})...")
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text.strip()
        # strip code fences if any
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  ! JSON parse failed for c{cid}, raw first 400 chars:\n{text[:400]}")
            raise
        out[str(cid)] = {
            "title": spec["title"],
            "vignette": data["vignette"],
        }
        wc = len(data["vignette"].split())
        print(f"  ← c{cid} done ({wc} words)")

    cache.write_text(json.dumps(out, indent=2))
    print(f"[vignettes] wrote → {cache}")
    return out


# --------------------------------------------------------------------------

def _wrap_paragraphs(paragraphs: list[str], width: int) -> list[str]:
    """Return a list of wrapped lines, with empty strings marking paragraph breaks."""
    lines = []
    for i, p in enumerate(paragraphs):
        wrapped = textwrap.wrap(p, width=width)
        lines.extend(wrapped)
        if i < len(paragraphs) - 1:
            lines.append("")  # blank line between paragraphs
    return lines


def _split_lines_into_columns(lines: list[str], n_cols: int) -> list[list[str]]:
    """Split wrapped lines into roughly-equal columns, preferring to break at
    blank lines (paragraph boundaries)."""
    total = len(lines)
    target = total / n_cols
    cols: list[list[str]] = []
    i = 0
    for c in range(n_cols - 1):
        want_end = int(round((c + 1) * target))
        # expand search to nearest blank line within ±3 of target
        best = want_end
        for d in range(0, 4):
            if want_end + d < total and lines[want_end + d] == "":
                best = want_end + d
                break
            if want_end - d >= i and lines[want_end - d] == "":
                best = want_end - d
                break
        cols.append(lines[i:best])
        i = best
        # skip the blank line that we broke on
        if i < total and lines[i] == "":
            i += 1
    cols.append(lines[i:])
    return cols


def _load_ai_answer_for_cluster(exemplars: list[dict]) -> tuple[dict | None, list[tuple[str, float]]]:
    """Look up the first exemplar's GPT answer + top emotions in the answer.

    Returns (answer_row_dict, [(emo_name, prob), ...]) or (None, []) if missing.
    """
    import pandas as pd  # local import — vignettes may run before parquets exist
    answers_path = DATA / "answers_gpt.parquet"
    emo_path = DATA / "emotions_answers_gpt.parquet"
    if not answers_path.exists() or not emo_path.exists():
        return None, []
    answers = pd.read_parquet(answers_path)
    emo = pd.read_parquet(emo_path)
    emo_cols = [c for c in emo.columns if c.startswith("emo_")]
    for ex in exemplars:
        eid = ex.get("id")
        if not eid:
            continue
        a_row = answers[answers["id"] == eid]
        if len(a_row) == 0:
            continue
        text = (a_row.iloc[0]["answer_text"] or "").strip()
        if not text:
            continue
        e_row = emo[emo["id"] == eid]
        top: list[tuple[str, float]] = []
        if len(e_row) > 0:
            vals = e_row.iloc[0][emo_cols]
            # Drop neutral, take top 3
            vals_dict = {k.replace("emo_", ""): float(v) for k, v in vals.items()}
            vals_dict.pop("neutral", None)
            top = sorted(vals_dict.items(), key=lambda kv: -kv[1])[:3]
        return {
            "id": eid,
            "text": text,
            "model": a_row.iloc[0].get("model_name", "gpt"),
        }, top
    return None, []


def _truncate_excerpt(text: str, target_words: int = 80) -> str:
    """Return the first ~target_words of text, truncated to a clean break."""
    text = text.strip().replace("\n\n", " ").replace("\n", " ")
    # Collapse multiple spaces
    text = " ".join(text.split())
    # Strip surrounding quote characters so we can wrap consistently
    text = text.lstrip("\"'\u201c\u201d ").rstrip("\"'\u201c\u201d ")
    words = text.split()
    if len(words) <= target_words:
        return text
    snippet = " ".join(words[:target_words])
    # Prefer ending at the last full sentence before the cutoff
    for punct in (". ", "? ", "! "):
        idx = snippet.rfind(punct)
        if idx > len(snippet) * 0.5:
            return snippet[: idx + 1].strip() + " …"
    return snippet.rstrip(",;:") + " …"


def _register_label(top: list[tuple[str, float]]) -> str:
    if not top:
        return "unknown"
    names = {n for n, _ in top}
    if names & {"approval", "admiration", "caring", "gratitude", "love"}:
        return "warm-neutral"
    if names & {"optimism", "excitement", "joy", "amusement"}:
        return "bright"
    if names & {"curiosity", "realization", "confusion"}:
        return "inquisitive"
    if names & {"sadness", "grief", "disappointment", "remorse"}:
        return "somber"
    if names & {"nervousness", "fear", "embarrassment"}:
        return "cautious"
    return "neutral"


def render_vignette_slide(spec: dict, vignette_text: str, label: dict, exemplars: list[dict]):
    """Render one slide with vignette as a 2-column book page on the left,
    a cluster metadata card on the upper right, and an AI-answer excerpt on
    the lower right."""
    fig, base_ax = slide(
        title=spec["deck_title"],
        subtitle=spec["deck_subtitle"],
        source='A literary vignette by Claude Sonnet 4.5, written from cluster exemplars and emotion profile · not verbatim user text',
        content_rect=(0.06, 0.08, 0.88, 0.74),
    )
    base_ax.axis("off")

    # Left panel: the vignette, laid out as a 2-column book page
    vx, vy, vw, vh = 0.06, 0.08, 0.60, 0.74
    v_ax = fig.add_axes([vx, vy, vw, vh])
    v_ax.set_facecolor(PALETTE["surface"])
    v_ax.set_xticks([]); v_ax.set_yticks([])
    for s in v_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.5)

    # Title line inside the panel
    v_ax.text(
        0.035, 0.955, spec["title"].upper(),
        fontsize=12, fontweight="bold", color=PALETTE["accent"],
        transform=v_ax.transAxes, va="top",
    )
    v_ax.plot([0.035, 0.22], [0.925, 0.925],
              color=PALETTE["accent"], linewidth=1.5,
              transform=v_ax.transAxes)

    # Body: 2 columns
    paragraphs = [p.strip() for p in vignette_text.split("\n") if p.strip()]
    lines = _wrap_paragraphs(paragraphs, width=44)
    cols = _split_lines_into_columns(lines, n_cols=2)

    col_xs = [0.035, 0.515]
    col_top = 0.885
    for cx, col_lines in zip(col_xs, cols):
        body = "\n".join(col_lines)
        v_ax.text(
            cx, col_top, body,
            fontsize=9.2, color=PALETTE["text"], fontweight="regular",
            transform=v_ax.transAxes, va="top", ha="left",
            linespacing=1.42, fontstyle="italic",
        )

    # Right column splits into two stacked panels:
    #   top: Field Notes metadata (compressed)
    #   bottom: What the AI said back (new)
    px = 0.70
    pw = 0.24
    top_box  = (px, 0.46, pw, 0.36)  # field notes
    bot_box  = (px, 0.08, pw, 0.36)  # AI answer

    # ---------- Top panel: Field Notes (condensed) ----------
    p_ax = fig.add_axes(list(top_box))
    p_ax.set_facecolor(PALETTE["surface"])
    p_ax.set_xticks([]); p_ax.set_yticks([])
    for s in p_ax.spines.values():
        s.set_color(PALETTE["accent_cool"]); s.set_linewidth(1.2)

    theme = label.get("talk_theme", "new")
    theme_color = THEME_COLORS.get(theme, PALETTE["accent_cool"])

    # Header
    p_ax.text(0.5, 0.93, "FIELD NOTES",
              ha="center", va="top", fontsize=9.5, fontweight="bold",
              color=PALETTE["accent_cool"], transform=p_ax.transAxes)

    # Big count + label on one line row
    p_ax.text(0.08, 0.80, f"{label['size']}",
              ha="left", va="center", fontsize=34, fontweight="black",
              color=PALETTE["accent_cool"], transform=p_ax.transAxes)
    p_ax.text(0.50, 0.80, "prompts\nin this\ncluster",
              ha="left", va="center", fontsize=9, color=PALETTE["text_dim"],
              transform=p_ax.transAxes, linespacing=1.1)

    # Divider
    p_ax.plot([0.06, 0.94], [0.60, 0.60], color=PALETTE["border"],
              linewidth=0.8, transform=p_ax.transAxes)

    # Theme tag row
    p_ax.text(0.06, 0.52, "THEME",
              fontsize=8, fontweight="bold", color=PALETTE["accent_warm"],
              transform=p_ax.transAxes, va="top")
    p_ax.add_patch(Rectangle((0.06, 0.415), 0.055, 0.035,
                             facecolor=theme_color,
                             transform=p_ax.transAxes))
    p_ax.text(0.14, 0.435, theme,
              fontsize=9, color=PALETTE["text"], fontweight="medium",
              transform=p_ax.transAxes, va="center")

    # Emotion hook
    p_ax.text(0.06, 0.34, "EMOTION HOOK",
              fontsize=8, fontweight="bold", color=PALETTE["accent_warm"],
              transform=p_ax.transAxes, va="top")
    hook = label.get("emotion_hook", "")
    hook_wrapped = "\n".join(textwrap.wrap(hook, width=24))
    p_ax.text(0.06, 0.26, hook_wrapped,
              fontsize=9, color=PALETTE["text"], fontweight="medium",
              transform=p_ax.transAxes, va="top", linespacing=1.25,
              fontstyle="italic")

    # ---------- Bottom panel: What the AI said back ----------
    ai, top_answer_emos = _load_ai_answer_for_cluster(exemplars)

    a_ax = fig.add_axes(list(bot_box))
    a_ax.set_facecolor(PALETTE["surface"])
    a_ax.set_xticks([]); a_ax.set_yticks([])
    for s in a_ax.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    a_ax.text(0.5, 0.93, "WHAT THE AI SAID BACK",
              ha="center", va="top", fontsize=9.5, fontweight="bold",
              color=PALETTE["accent"], transform=a_ax.transAxes)

    if ai is None:
        a_ax.text(0.5, 0.55, "(no matching answer)",
                  ha="center", va="center", fontsize=10,
                  color=PALETTE["text_muted"], fontstyle="italic",
                  transform=a_ax.transAxes)
    else:
        excerpt = _truncate_excerpt(ai["text"], target_words=36)
        wrapped = "\n".join(textwrap.wrap(excerpt, width=30))
        a_ax.text(0.06, 0.82, f"\u201c{wrapped}\u201d",
                  fontsize=7.8, color=PALETTE["text"], fontstyle="italic",
                  transform=a_ax.transAxes, va="top", linespacing=1.35)

        # Top emotions in the answer
        a_ax.text(0.06, 0.30, "TOP EMOTIONS IN THIS ANSWER",
                  fontsize=7.5, fontweight="bold", color=PALETTE["accent_warm"],
                  transform=a_ax.transAxes, va="top")
        if top_answer_emos:
            emo_line = "  ·  ".join(n for n, _ in top_answer_emos)
        else:
            emo_line = "—"
        a_ax.text(0.06, 0.235, emo_line,
                  fontsize=9.5, color=PALETTE["text"], fontweight="semibold",
                  transform=a_ax.transAxes, va="top")

        # Register label
        register = _register_label(top_answer_emos)
        a_ax.text(0.06, 0.13, "AI's register:",
                  fontsize=7.5, fontweight="bold", color=PALETTE["text_dim"],
                  transform=a_ax.transAxes, va="top")
        a_ax.text(0.38, 0.13, register,
                  fontsize=9, fontweight="bold", color=PALETTE["accent"],
                  transform=a_ax.transAxes, va="top", fontstyle="italic")

    out_path = OUT / f"{spec['slide_num']:02d}_vignette_{spec['slug']}.png"
    save(fig, out_path)


# --------------------------------------------------------------------------

def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)
    vignettes = generate_vignettes()

    labels = json.loads((DATA / "labels.json").read_text())
    exemplars_all = json.loads((DATA / "cluster_exemplars.json").read_text())["clusters"]

    for spec in SURPRISING:
        cid = spec["cluster_id"]
        v = vignettes[str(cid)]
        label = labels[str(cid)]
        exemplars = exemplars_all[str(cid)]
        render_vignette_slide(spec, v["vignette"], label, exemplars)


if __name__ == "__main__":
    main()
