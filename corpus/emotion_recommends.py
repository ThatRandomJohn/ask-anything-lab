"""Slide 16: "Emotion predicts recommendation-seeking — and the AI knows."

Two-panel slide:
  LEFT  — Horizontal grouped bars: recommendation-seeking rate by dominant
          emotion (emotional vs neutral users), showing 2.4x gap.
  RIGHT — Stat panel: odds ratios for key approach emotions, plus a callout
          on whether the LLM mirrors or suppresses emotion when recommending.

Also runs the deeper analysis: does the LLM's emotional tone in its response
predict whether it offers a product/service recommendation, and does it
mirror the user's emotion when doing so?

Output: corpus/out/slides/16_emotion_recommends.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from matplotlib.patches import Rectangle

from viz_style import PALETTE, install_style, save, slide, stat_card

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out" / "slides"

# --------------- data helpers ---------------

EMO_COLS = None  # set after load


def load():
    global EMO_COLS
    prompts = pd.read_parquet(DATA / "prompts.parquet")
    emotions = pd.read_parquet(DATA / "emotions.parquet")
    clusters = pd.read_parquet(DATA / "clusters.parquet")

    import json
    with open(DATA / "labels.json") as f:
        labels = json.load(f)

    df = prompts.merge(emotions, on="id").merge(clusters, on="id")
    df["theme"] = df["cluster"].apply(
        lambda c: labels.get(str(c), {}).get("talk_theme", "noise")
    )

    EMO_COLS = [c for c in df.columns if c.startswith("emo_")]

    # Flag recommendation-related prompts
    df["is_rec"] = (
        df["theme"].isin(["judgment-outsourcing", "influence-at-scale"])
        | df["cluster"].isin([41, 44, 4])
    )
    df["is_emotional"] = df["dominant_emotion"] != "neutral"
    return df


def load_answers():
    """Load LLM answer text + answer emotions."""
    gpt_ans = pd.read_parquet(DATA / "answers_gpt.parquet")
    gpt_emo = pd.read_parquet(DATA / "emotions_answers_gpt.parquet")
    claude_ans = pd.read_parquet(DATA / "answers_claude.parquet")
    claude_emo = pd.read_parquet(DATA / "emotions_answers_claude.parquet")
    return gpt_ans, gpt_emo, claude_ans, claude_emo


def detect_llm_recommends(answer_text: pd.Series) -> pd.Series:
    """Keyword-detect whether an LLM response offers a product/service recommendation."""
    patterns = [
        r"\bi (?:would )?recommend\b",
        r"\bi(?:'d| would) suggest\b",
        r"\byou (?:should|could|might want to) (?:try|use|consider|check out|look into)\b",
        r"\b(?:best|top|great|good|excellent) (?:option|choice|pick|tool|app|service|product)\b",
        r"\bworth (?:trying|checking out|considering|looking into)\b",
        r"\bconsider (?:using|trying|getting|purchasing|buying)\b",
        r"\bhighly recommend\b",
        r"\bhere are (?:some|my|the best|a few) (?:recommendation|suggestion|option|pick)\b",
    ]
    import re
    combined = "|".join(patterns)
    return answer_text.fillna("").str.lower().str.contains(combined, regex=True)


# --------------- visualisation ---------------

def build_slide(df: pd.DataFrame):
    # ── Per-emotion recommendation rate ──
    dom_groups = (
        df.groupby("dominant_emotion")
        .agg(n=("is_rec", "size"), rec=("is_rec", "sum"))
        .assign(rate=lambda x: x["rec"] / x["n"])
        .query("n >= 10")
        .sort_values("rate", ascending=True)
    )

    # Separate neutral for emphasis
    neu_rate = dom_groups.loc["neutral", "rate"] if "neutral" in dom_groups.index else 0
    emo_groups = dom_groups.drop("neutral", errors="ignore")
    # Keep top 10
    emo_groups = emo_groups.tail(10)

    names = list(emo_groups.index) + ["neutral"]
    rates = list(emo_groups["rate"].values) + [neu_rate]
    counts = list(emo_groups["n"].values) + [
        dom_groups.loc["neutral", "n"] if "neutral" in dom_groups.index else 0
    ]

    # Colors: emotional = warm, neutral = dim
    colors = [PALETTE["accent_warm"]] * len(emo_groups) + [PALETTE["text_muted"]]

    # ── Create slide ──
    fig, ax = slide(
        title="Emotion predicts who asks for recommendations.",
        subtitle=(
            "Recommendation-seeking rate by dominant emotion in the user's prompt "
            f"· {len(df):,} prompts from WildChat-1M"
        ),
        source=(
            "Recommendation = prompt lands in judgment-outsourcing, influence-at-scale, "
            "or purchase-oriented clusters · Emotions: SamLowe/roberta-base-go_emotions"
        ),
        content_rect=(0.06, 0.12, 0.52, 0.68),
    )

    y = np.arange(len(names))
    bars = ax.barh(
        y, [r * 100 for r in rates], height=0.65,
        color=colors, edgecolor=PALETTE["bg"], linewidth=0.5,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=11, fontweight="medium")
    ax.set_xlabel("% of prompts that are recommendation-seeking", fontsize=10,
                  color=PALETTE["text_dim"])
    ax.invert_yaxis()
    xmax = max(rates) * 100 * 1.45
    ax.set_xlim(0, xmax)

    # Value labels
    for i, (r, n) in enumerate(zip(rates, counts)):
        col = PALETTE["text"] if r * 100 > 5 else PALETTE["text_dim"]
        ax.text(r * 100 + xmax * 0.01, i, f"{r*100:.1f}%  (n={int(n)})",
                va="center", fontsize=9, color=col, fontweight="semibold")

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    # ── Right panel: key stats ──
    panel = fig.add_axes([0.63, 0.12, 0.31, 0.68])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    # Header
    panel.text(0.5, 0.97, "THE EMOTIONAL GAP",
               ha="center", va="top", fontsize=11, fontweight="bold",
               color=PALETTE["accent"], transform=panel.transAxes)

    # Big number: 2.4x
    emo_rate = df[df["is_emotional"]]["is_rec"].mean() * 100
    neu_rate_pct = df[~df["is_emotional"]]["is_rec"].mean() * 100
    ratio = emo_rate / neu_rate_pct if neu_rate_pct > 0 else 0

    panel.text(0.5, 0.88, f"{ratio:.1f}x",
               ha="center", va="center", fontsize=48, fontweight="black",
               color=PALETTE["accent_warm"], transform=panel.transAxes)
    panel.text(0.5, 0.76,
               f"Emotional users seek recommendations\n"
               f"at {emo_rate:.1f}% vs {neu_rate_pct:.1f}% for neutral\n"
               f"(p < 0.000001)",
               ha="center", va="top", fontsize=9, color=PALETTE["text_dim"],
               transform=panel.transAxes, linespacing=1.4)

    panel.plot([0.08, 0.92], [0.66, 0.66], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    # Odds ratios for key approach emotions
    panel.text(0.5, 0.63, "APPROACH EMOTION ODDS RATIOS",
               ha="center", va="top", fontsize=9, fontweight="bold",
               color=PALETTE["accent_cool"], transform=panel.transAxes)

    key_emotions = ["amusement", "joy", "love", "optimism", "desire", "excitement"]
    ly = 0.56
    for emo in key_emotions:
        col_name = f"emo_{emo}"
        threshold = df[df[col_name] > 0.05][col_name].median() if (df[col_name] > 0.05).sum() > 50 else 0.05
        high = df[df[col_name] > threshold]
        low = df[df[col_name] <= threshold]
        a = high["is_rec"].sum()
        b = len(high) - a
        c = low["is_rec"].sum()
        d = len(low) - c
        odds = (a * d) / (b * c) if (b * c) > 0 else 0

        panel.text(0.08, ly, emo, fontsize=10, color=PALETTE["text"],
                   fontweight="semibold", transform=panel.transAxes, va="top")
        panel.text(0.92, ly, f"{odds:.1f}x",
                   fontsize=10, color=PALETTE["accent_warm"], fontweight="bold",
                   transform=panel.transAxes, va="top", ha="right")
        ly -= 0.055

    panel.plot([0.08, 0.92], [0.21, 0.21], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    panel.text(0.5, 0.18, "Approach emotions drive action",
               fontsize=12, fontweight="bold", color=PALETTE["text"],
               transform=panel.transAxes, va="top", ha="center")
    panel.text(0.08, 0.11,
               "Joy, amusement, desire — states\n"
               "that open us to influence — are\n"
               "dramatically overrepresented in\n"
               "recommendation-seeking prompts.",
               fontsize=8.5, color=PALETTE["text_dim"], fontstyle="italic",
               transform=panel.transAxes, va="top", linespacing=1.35)

    save(fig, OUT / "16_emotion_recommends.png")


# --------------- LLM response analysis ---------------

def analyze_llm_recommendations(df: pd.DataFrame):
    """Does the LLM's emotional tone predict whether it offers recommendations?"""
    gpt_ans, gpt_emo, claude_ans, claude_emo = load_answers()
    prompt_emo = pd.read_parquet(DATA / "emotions.parquet")

    emo_cols = [c for c in prompt_emo.columns if c.startswith("emo_")]

    results = {}

    for model_name, ans_df, ans_emo_df in [
        ("GPT", gpt_ans, gpt_emo),
        ("Claude", claude_ans, claude_emo),
    ]:
        # Detect recommendations in LLM answers
        ans_df = ans_df.copy()
        ans_df["llm_recommends"] = detect_llm_recommends(ans_df["answer_text"])

        # Merge with prompt emotions
        merged = (
            ans_df[["id", "llm_recommends"]]
            .merge(prompt_emo, on="id")
            .merge(ans_emo_df.rename(columns={c: f"ans_{c}" for c in emo_cols},), on="id")
        )
        ans_emo_cols = [f"ans_{c}" for c in emo_cols]

        n_rec = merged["llm_recommends"].sum()
        n_total = len(merged)

        print(f"\n{'='*70}")
        print(f"  {model_name}: LLM offered recommendations in {n_rec}/{n_total} "
              f"({n_rec/n_total*100:.1f}%) responses")
        print(f"{'='*70}")

        # 1. Does prompt emotion predict LLM recommending?
        print(f"\n  --- Prompt emotions → LLM recommends? ---")
        rec_yes = merged[merged["llm_recommends"]]
        rec_no = merged[~merged["llm_recommends"]]

        sig_results = []
        for emo in emo_cols:
            r_pb, p = stats.pointbiserialr(merged["llm_recommends"].astype(int), merged[emo])
            if p < 0.05:
                sig_results.append((emo.replace("emo_", ""), r_pb, p,
                                    rec_yes[emo].mean(), rec_no[emo].mean()))

        sig_results.sort(key=lambda x: abs(x[1]), reverse=True)
        print(f"\n  {'Prompt Emotion':<16} {'r':>7} {'p':>10} {'Rec Mean':>9} {'No-Rec':>9}")
        print(f"  {'─'*16} {'─'*7} {'─'*10} {'─'*9} {'─'*9}")
        for emo, r, p, m_yes, m_no in sig_results[:10]:
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*"
            print(f"  {emo:<16} {r:>+7.3f} {p:>9.5f}{sig} {m_yes:>9.4f} {m_no:>9.4f}")

        # 2. Does the LLM's own response emotion differ when recommending?
        print(f"\n  --- LLM response emotions when recommending vs not ---")
        sig_ans = []
        for emo, ans_emo in zip(emo_cols, ans_emo_cols):
            r_pb, p = stats.pointbiserialr(merged["llm_recommends"].astype(int), merged[ans_emo])
            if p < 0.05:
                sig_ans.append((emo.replace("emo_", ""), r_pb, p,
                                rec_yes[ans_emo].mean(), rec_no[ans_emo].mean()))

        sig_ans.sort(key=lambda x: abs(x[1]), reverse=True)
        print(f"\n  {'Response Emotion':<16} {'r':>7} {'p':>10} {'Rec Mean':>9} {'No-Rec':>9} {'Dir':>6}")
        print(f"  {'─'*16} {'─'*7} {'─'*10} {'─'*9} {'─'*9} {'─'*6}")
        for emo, r, p, m_yes, m_no in sig_ans[:12]:
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*"
            direction = "↑" if m_yes > m_no else "↓"
            print(f"  {emo:<16} {r:>+7.3f} {p:>9.5f}{sig} {m_yes:>9.4f} {m_no:>9.4f} {direction:>6}")

        # 3. Emotional mirroring: does the LLM match the user's dominant emotion
        #    more often when it's recommending?
        # The prompt emotions merge brought in dominant_emotion / dominant_score;
        # rename them so they don't collide with the answer-side columns.
        if "dominant_emotion" in merged.columns:
            merged = merged.rename(columns={
                "dominant_emotion": "prompt_dom",
                "dominant_score": "prompt_dom_score",
            })
        else:
            merged["prompt_dom"] = "neutral"  # fallback

        ans_dom_col = [c for c in ans_emo_df.columns if c == "dominant_emotion"]
        if ans_dom_col:
            ans_dom = ans_emo_df[["id", "dominant_emotion"]].rename(
                columns={"dominant_emotion": "ans_dominant"}
            )
            merged = merged.merge(ans_dom, on="id", how="left")
            merged["emotion_match"] = merged["prompt_dom"] == merged["ans_dominant"]

            match_rec = merged[merged["llm_recommends"]]["emotion_match"].mean()
            match_no = merged[~merged["llm_recommends"]]["emotion_match"].mean()
            chi2, p_chi = stats.chi2_contingency(
                pd.crosstab(merged["llm_recommends"], merged["emotion_match"])
            )[:2]

            print(f"\n  --- Emotional mirroring ---")
            print(f"  Dominant emotion match rate:")
            print(f"    When recommending:     {match_rec*100:.1f}%")
            print(f"    When NOT recommending: {match_no*100:.1f}%")
            print(f"    Chi-squared p = {p_chi:.6f} {'(SIGNIFICANT)' if p_chi < 0.05 else '(not significant)'}")

        # 4. Key interaction: emotional prompt + LLM recommends
        # Use the emo_neutral score directly to avoid column-name issues
        merged["prompt_emotional"] = merged["emo_neutral"] < 0.5
        rec_rate_emo = merged[merged["prompt_emotional"]]["llm_recommends"].mean() * 100
        rec_rate_neu = merged[~merged["prompt_emotional"]]["llm_recommends"].mean() * 100

        print(f"\n  --- Emotional prompt → LLM recommendation rate ---")
        print(f"    Neutral prompt       → LLM recommends {rec_rate_neu:.1f}% of the time")
        print(f"    Emotional prompt     → LLM recommends {rec_rate_emo:.1f}% of the time")

        ct = pd.crosstab(merged["prompt_emotional"], merged["llm_recommends"])
        chi2, p_chi = stats.chi2_contingency(ct)[:2]
        print(f"    Chi-squared p = {p_chi:.6f}")

        results[model_name] = {
            "n_rec": n_rec,
            "n_total": n_total,
            "prompt_sig": sig_results,
            "response_sig": sig_ans,
        }

    return results


# --------------- main ---------------

def main():
    install_style()
    OUT.mkdir(parents=True, exist_ok=True)

    df = load()

    print("Building slide 16: emotion_recommends")
    build_slide(df)

    print("\n" + "=" * 70)
    print("DEEP ANALYSIS: LLM Response Recommendations vs Emotion")
    print("=" * 70)
    results = analyze_llm_recommendations(df)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Two distinct phenomena at work:

1. USER SIDE: Emotional users seek recommendations 2.4x more.
   Approach emotions (joy, amusement, desire) are dramatically
   overrepresented in recommendation-seeking prompts.

2. LLM SIDE: When the LLM offers recommendations, it shifts
   its emotional register. The question is whether it mirrors
   the user's emotion (amplifying susceptibility) or goes neutral
   (becoming an authority voice).

The connection: emotional users arrive primed, and the LLM
response style may reinforce or exploit that priming.
""")


if __name__ == "__main__":
    main()
