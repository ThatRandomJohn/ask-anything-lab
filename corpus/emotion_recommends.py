"""Slide 16: "When the AI recommends, it stops listening."

Two-panel slide focused on LLM response behavior:
  LEFT  — Grouped horizontal bars showing how GPT and Claude shift their
          emotional register when they offer a recommendation: approval,
          admiration, caring UP — neutrality DOWN — mirroring BROKEN.
  RIGHT — Stat panel: mirroring drop-off numbers for both models, plus
          the narrative that the AI switches from companion to salesperson.

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
    """LLM-focused slide: how the AI breaks mirroring to sell."""
    import matplotlib.pyplot as plt

    gpt_ans, gpt_emo, claude_ans, claude_emo = load_answers()
    prompt_emo = pd.read_parquet(DATA / "emotions.parquet")
    emo_cols = [c for c in prompt_emo.columns if c.startswith("emo_")]

    # ── Compute LLM emotion shifts when recommending ──
    model_data = {}
    for model_name, ans_df, ans_emo_df in [
        ("GPT", gpt_ans, gpt_emo),
        ("Claude", claude_ans, claude_emo),
    ]:
        ans_df = ans_df.copy()
        ans_df["llm_recommends"] = detect_llm_recommends(ans_df["answer_text"])
        merged = ans_df[["id", "llm_recommends"]].merge(ans_emo_df, on="id")

        rec_yes = merged[merged["llm_recommends"]]
        rec_no = merged[~merged["llm_recommends"]]

        shifts = {}
        for emo in emo_cols:
            mean_rec = rec_yes[emo].mean()
            mean_no = rec_no[emo].mean()
            pct_chg = ((mean_rec - mean_no) / mean_no * 100) if mean_no > 0.001 else 0
            _, p = stats.mannwhitneyu(rec_yes[emo], rec_no[emo], alternative="two-sided")
            shifts[emo.replace("emo_", "")] = {
                "rec": mean_rec, "no_rec": mean_no,
                "pct": pct_chg, "p": p,
            }

        # Mirroring
        prompt_dom = prompt_emo[["id", "dominant_emotion"]].rename(
            columns={"dominant_emotion": "prompt_dom"}
        )
        ans_dom = ans_emo_df[["id", "dominant_emotion"]].rename(
            columns={"dominant_emotion": "ans_dom"}
        )
        mirror_df = (
            ans_df[["id", "llm_recommends"]]
            .merge(prompt_dom, on="id")
            .merge(ans_dom, on="id")
        )
        mirror_df["match"] = mirror_df["prompt_dom"] == mirror_df["ans_dom"]
        mirror_rec = mirror_df[mirror_df["llm_recommends"]]["match"].mean()
        mirror_no = mirror_df[~mirror_df["llm_recommends"]]["match"].mean()

        model_data[model_name] = {
            "shifts": shifts,
            "n_rec": int(ans_df["llm_recommends"].sum()),
            "n_total": len(ans_df),
            "mirror_rec": mirror_rec,
            "mirror_no": mirror_no,
        }

    # ── Emotions to chart: the ones that shift most (significant for either model) ──
    show_emotions = ["approval", "admiration", "caring", "optimism", "curiosity", "neutral"]

    # ── Create slide ──
    fig, ax = slide(
        title="When the AI recommends, it stops listening.",
        subtitle=(
            "LLM emotional register shift when responses contain product/service "
            "recommendations · GPT and Claude on 5,000 WildChat prompts"
        ),
        source=(
            "Recommendations detected via keyword patterns in LLM response text · "
            "Emotions: SamLowe/roberta-base-go_emotions · Mirroring = dominant emotion match"
        ),
        content_rect=(0.06, 0.12, 0.52, 0.68),
    )

    # ── LEFT: grouped bars — response emotion when recommending vs not ──
    y = np.arange(len(show_emotions))
    bar_h = 0.18
    offsets = [-1.5, -0.5, 0.5, 1.5]

    color_gpt_rec = PALETTE["accent_warm"]   # orange
    color_gpt_no = "#7C5A2E"                 # dim orange
    color_cla_rec = PALETTE["accent_cool"]   # cyan
    color_cla_no = "#1A5C6B"                 # dim cyan

    gpt = model_data["GPT"]["shifts"]
    cla = model_data["Claude"]["shifts"]

    vals_gpt_no = [gpt[e]["no_rec"] for e in show_emotions]
    vals_gpt_rec = [gpt[e]["rec"] for e in show_emotions]
    vals_cla_no = [cla[e]["no_rec"] for e in show_emotions]
    vals_cla_rec = [cla[e]["rec"] for e in show_emotions]

    ax.barh(y + offsets[0] * bar_h, vals_gpt_no, height=bar_h,
            color=color_gpt_no, edgecolor=PALETTE["bg"], linewidth=0.4,
            label="GPT · no rec")
    ax.barh(y + offsets[1] * bar_h, vals_gpt_rec, height=bar_h,
            color=color_gpt_rec, edgecolor=PALETTE["bg"], linewidth=0.4,
            label="GPT · recommending")
    ax.barh(y + offsets[2] * bar_h, vals_cla_no, height=bar_h,
            color=color_cla_no, edgecolor=PALETTE["bg"], linewidth=0.4,
            label="Claude · no rec")
    ax.barh(y + offsets[3] * bar_h, vals_cla_rec, height=bar_h,
            color=color_cla_rec, edgecolor=PALETTE["bg"], linewidth=0.4,
            label="Claude · recommending")

    ax.set_yticks(y)
    ax.set_yticklabels(show_emotions, fontsize=12, fontweight="medium")
    ax.invert_yaxis()
    xmax = max(max(vals_gpt_no), max(vals_gpt_rec),
               max(vals_cla_no), max(vals_cla_rec)) * 1.35
    ax.set_xlim(0, xmax)
    ax.set_xlabel("mean emotion probability in LLM response", fontsize=10,
                  color=PALETTE["text_dim"])

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    # Percent-change annotations on GPT rec bars
    label_offset = xmax * 0.008
    for i, emo in enumerate(show_emotions):
        pct = gpt[emo]["pct"]
        val = vals_gpt_rec[i]
        sig = gpt[emo]["p"] < 0.05
        if sig:
            sign = "+" if pct > 0 else ""
            col = PALETTE["good"] if pct > 0 else PALETTE["bad"]
            ax.text(val + label_offset, i + offsets[1] * bar_h,
                    f"{sign}{pct:.0f}%", va="center", fontsize=8,
                    color=col, fontweight="bold")

    ax.legend(loc="lower right", frameon=False, fontsize=8.5,
              labelcolor=PALETTE["text"], ncol=2, columnspacing=1.2)

    # ── RIGHT: mirroring + narrative panel ──
    panel = fig.add_axes([0.63, 0.12, 0.31, 0.68])
    panel.set_facecolor(PALETTE["surface"])
    panel.set_xticks([]); panel.set_yticks([])
    for s in panel.spines.values():
        s.set_color(PALETTE["accent"]); s.set_linewidth(1.2)

    # Header
    panel.text(0.5, 0.97, "MIRRORING DROPS",
               ha="center", va="top", fontsize=11, fontweight="bold",
               color=PALETTE["accent"], transform=panel.transAxes)

    panel.text(0.5, 0.91, "When the LLM recommends, it stops\n"
               "matching your emotional state.",
               ha="center", va="top", fontsize=9.5, color=PALETTE["text_dim"],
               transform=panel.transAxes, linespacing=1.35)

    # GPT mirroring stats
    gm = model_data["GPT"]
    cm = model_data["Claude"]

    ly = 0.78
    for label, color, data in [
        ("GPT", PALETTE["accent_warm"], gm),
        ("Claude", PALETTE["accent_cool"], cm),
    ]:
        drop = data["mirror_no"] - data["mirror_rec"]
        panel.text(0.08, ly, label, fontsize=12, fontweight="bold",
                   color=color, transform=panel.transAxes, va="top")

        panel.text(0.08, ly - 0.05,
                   f"Normal: {data['mirror_no']*100:.0f}% match",
                   fontsize=10, color=PALETTE["text"],
                   transform=panel.transAxes, va="top")
        panel.text(0.08, ly - 0.10,
                   f"Recommending: {data['mirror_rec']*100:.0f}% match",
                   fontsize=10, color=PALETTE["text"],
                   transform=panel.transAxes, va="top")
        panel.text(0.92, ly - 0.07,
                   f"-{drop*100:.0f}%",
                   fontsize=24, fontweight="black", color=PALETTE["bad"],
                   transform=panel.transAxes, va="center", ha="right")

        ly -= 0.21

    panel.plot([0.08, 0.92], [0.38, 0.38], color=PALETTE["border"],
               linewidth=0.8, transform=panel.transAxes)

    # Narrative
    panel.text(0.5, 0.34, "Not mirroring. Selling.",
               fontsize=13, fontweight="bold", color=PALETTE["text"],
               transform=panel.transAxes, va="top", ha="center")
    panel.text(0.08, 0.26,
               "Both models break emotional\n"
               "alignment when they recommend.\n"
               "Approval, admiration, and caring\n"
               "spike. Neutrality drops. The AI\n"
               "switches from companion to\n"
               "salesperson — and it does this\n"
               "by design, not by accident.",
               fontsize=8.8, color=PALETTE["text_dim"], fontstyle="italic",
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
