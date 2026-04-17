"""Label each cluster with Claude Sonnet 4.5 using both semantic exemplars AND emotion profile.

For each cluster, Claude receives:
- 10 exemplar prompts (closest to cluster centroid)
- The cluster's top 5 non-neutral emotions by mean probability
- The pct of prompts dominated by neutral vs non-neutral
- The full TEDx talk taxonomy

Claude returns: label, talk_theme, emotion_hook, rationale, surprising (bool).

Output: corpus/data/labels.json
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

HERE = Path(__file__).parent
EXEMPLARS = HERE / "data" / "cluster_exemplars.json"
EMOTIONS = HERE / "data" / "emotions.parquet"
CLUSTERS = HERE / "data" / "clusters.parquet"
OUT = HERE / "data" / "labels.json"

MODEL = "claude-sonnet-4-5-20250929"

# Exact talk vocabulary from the TEDx draft.
TALK_THEMES = {
    "crisis-companionship":  "User is in acute distress (fear, panic, pain, grief) and turns to AI for reassurance right now. 2am / ER / chest tightness energy.",
    "information-seeking":   "Factual or how-to question replacing a search engine. User wants a definitive answer, not feelings.",
    "emotional-validation":  "User shares feelings or a situation and is implicitly asking AI to say 'that makes sense you'd feel that way'.",
    "judgment-outsourcing":  "User explicitly asks AI to choose for them: 'should I…', 'what would you do', 'tell me what to pick'.",
    "mechanism-curiosity":   "User is asking about how AI itself works, or about models, embeddings, LLMs, prompts, hallucination.",
    "influence-at-scale":    "Marketing, persuasion, branding, audience, copywriting, political messaging, advertising.",
    "ambient-companionship": "Non-crisis loneliness, boredom, chit-chat, roleplay, social substitute. 'Talk to me' energy.",
    "high-stakes-decision":  "Health, money, legal, child-raising, relationship — real consequences if the answer is wrong.",
    "low-stakes-utility":    "Recipes, trivia, homework help, code snippets, quick tasks where being wrong barely matters.",
    "validation-seeking":    "User already has a belief and is asking AI to confirm it. 'Am I right that…'.",
}


SYSTEM_PROMPT = """You are analyzing clusters of real user prompts sent to ChatGPT for a TEDx talk and upcoming book titled "Ask Anything: AI, Emotion, and Influence" by John Patterson.

The talk's core argument: people don't just ask AI for information — they ask for emotional presence, and the risk is that fluent, confident, emotionally-aligned AI responses cause us to outsource our judgment without noticing.

For each cluster you'll receive:
1. Ten exemplar prompts (the ones closest to the cluster centroid)
2. The cluster's emotion profile — both the fraction of prompts classified as "neutral" and the top 5 non-neutral emotions ranked by mean probability
3. A fixed taxonomy of 10 themes from the talk

Your job — respond ONLY with JSON matching this exact schema:

{
  "label": "3-6 word concrete description of what's in this cluster",
  "talk_theme": "crisis-companionship | information-seeking | emotional-validation | judgment-outsourcing | mechanism-curiosity | influence-at-scale | ambient-companionship | high-stakes-decision | low-stakes-utility | validation-seeking | new",
  "emotion_hook": "which specific emotion signal matters here (or 'flat' if it really is neutral utility) — one short phrase",
  "rationale": "one sentence explaining your theme pick, referencing both exemplar wording AND the emotion profile",
  "surprising": true | false
}

"surprising" = true ONLY IF this cluster reveals something the talk didn't anticipate, or reveals an emotion-topic pairing that contradicts common assumptions (e.g., utility prompts carrying heavy frustration, or factual questions loaded with fear). Otherwise false.

Do not add any text before or after the JSON."""


def compute_cluster_emotion_profile(cluster_id: int, clusters_df: pd.DataFrame, emotions_df: pd.DataFrame) -> dict:
    ids_in_cluster = clusters_df.loc[clusters_df["cluster"] == cluster_id, "id"].tolist()
    sub = emotions_df[emotions_df["id"].isin(ids_in_cluster)]
    if len(sub) == 0:
        return {"neutral_pct": 0.0, "top_non_neutral": [], "size": 0}

    # Percentage of prompts where neutral is dominant
    neutral_dom = (sub["dominant_emotion"] == "neutral").mean()

    # Mean probabilities across all 28 emotions for this cluster
    emo_cols = [c for c in sub.columns if c.startswith("emo_")]
    means = sub[emo_cols].mean().sort_values(ascending=False)
    # Top 5 non-neutral
    non_neutral = [(c.replace("emo_", ""), float(means[c])) for c in means.index if c != "emo_neutral"][:5]

    return {
        "size": int(len(sub)),
        "neutral_pct": float(neutral_dom),
        "top_non_neutral": non_neutral,
    }


def build_user_prompt(cluster_id: int, exemplars: list, emo_profile: dict) -> str:
    ex_block = "\n".join(f"{i+1}. {e['text'][:400]}" for i, e in enumerate(exemplars))
    theme_block = "\n".join(f"- {k}: {v}" for k, v in TALK_THEMES.items())

    emo_list = "\n".join(
        f"  - {name}: {score:.3f}" for name, score in emo_profile["top_non_neutral"]
    )
    emo_block = f"""Cluster size: {emo_profile['size']} prompts
Neutral-dominant: {emo_profile['neutral_pct']*100:.0f}% of prompts in this cluster classify as emotionally neutral
Top 5 non-neutral emotions (mean probability across cluster):
{emo_list}"""

    return f"""TALK TAXONOMY:
{theme_block}

EMOTION PROFILE FOR CLUSTER {cluster_id}:
{emo_block}

TEN EXEMPLAR PROMPTS FROM THIS CLUSTER:
{ex_block}

Return JSON only."""


def main():
    load_dotenv("/Users/johnpatterson/Documents/Ask Anything Lab/.env")

    if not EXEMPLARS.exists():
        print(f"[label] {EXEMPLARS} not found — run cluster_topics.py first")
        sys.exit(1)
    if not EMOTIONS.exists() or not CLUSTERS.exists():
        print("[label] emotions.parquet and clusters.parquet required")
        sys.exit(1)

    with open(EXEMPLARS) as f:
        data = json.load(f)
    clusters_map = data["clusters"]
    print(f"[label] {len(clusters_map)} clusters to label with {MODEL}")

    clusters_df = pd.read_parquet(CLUSTERS)
    emotions_df = pd.read_parquet(EMOTIONS)

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    labels: dict[str, dict] = {}
    t0 = time.time()
    total_in = 0
    total_out = 0
    for i, (cid, exemplars) in enumerate(clusters_map.items()):
        cluster_id = int(cid)
        profile = compute_cluster_emotion_profile(cluster_id, clusters_df, emotions_df)
        user = build_user_prompt(cluster_id, exemplars, profile)
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user}],
            )
            txt = resp.content[0].text.strip()
            if txt.startswith("```"):
                txt = txt.split("```")[1]
                if txt.startswith("json"):
                    txt = txt[4:]
                txt = txt.strip()
            parsed = json.loads(txt)
            parsed["size"] = profile["size"]
            parsed["neutral_pct"] = profile["neutral_pct"]
            parsed["top_non_neutral"] = profile["top_non_neutral"]
            labels[cid] = parsed
            total_in += resp.usage.input_tokens
            total_out += resp.usage.output_tokens
            marker = " SURPRISING" if parsed.get("surprising") else ""
            print(f"  [{i+1:2d}/{len(clusters_map)}] c{cluster_id:>2} n={profile['size']:>3} neu={profile['neutral_pct']*100:>3.0f}%  {parsed['talk_theme']:>22}  {parsed['label'][:42]:42}{marker}")
        except Exception as e:
            print(f"  [{i+1:2d}/{len(clusters_map)}] c{cluster_id}: FAILED {type(e).__name__}: {str(e)[:140]}")
            labels[cid] = {"label": "unlabeled", "talk_theme": "new", "rationale": f"error: {e}", "size": profile["size"]}

    dt = time.time() - t0
    # Haiku/sonnet cost estimate — Sonnet 4.5 is $3/M in, $15/M out
    est_cost = total_in / 1_000_000 * 3.0 + total_out / 1_000_000 * 15.0
    print(f"\n[label] done in {dt:.0f}s  |  {total_in:,} in tokens, {total_out:,} out tokens  |  ~${est_cost:.3f}")

    with open(OUT, "w") as f:
        json.dump(labels, f, indent=2)
    print(f"[label] wrote → {OUT}")

    # Summary: theme distribution
    from collections import Counter
    theme_counts = Counter(v["talk_theme"] for v in labels.values())
    print("\n[label] theme distribution across clusters:")
    for t, c in theme_counts.most_common():
        total_prompts = sum(v.get("size", 0) for v in labels.values() if v.get("talk_theme") == t)
        print(f"  {t:>25}  {c:>3} clusters  {total_prompts:>5} prompts")

    # Surprising clusters
    surp = [(cid, v) for cid, v in labels.items() if v.get("surprising")]
    if surp:
        print(f"\n[label] {len(surp)} SURPRISING clusters:")
        for cid, v in surp:
            print(f"  c{cid}: {v['label']}  ({v['talk_theme']}) — {v.get('rationale','')[:120]}")


if __name__ == "__main__":
    main()
