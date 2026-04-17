"""Aggregate comparison visualization — shows how your results stack up."""
import html as _html

_STAGE_LABELS = {
    "embed": "Embedding",
    "retrieve": "Retrieval",
    "synthesize": "Synthesis",
    "influence": "Influence Analysis",
    "none": "Nothing",
}
_STAGE_COLORS = {
    "embed": "#F97316",
    "retrieve": "#06B6D4",
    "synthesize": "#A78BFA",
    "influence": "#F59E0B",
    "none": "#64748B",
}

_INF_LABELS = {
    "therapy_language": ("Therapy Language", "#A78BFA"),
    "emotional_mirroring": ("Emotional Mirroring", "#F97316"),
    "trust_anchors": ("Trust Anchors", "#06B6D4"),
    "persuasion_patterns": ("Persuasion Patterns", "#F59E0B"),
}


def render_audience_compare(stats: dict) -> str:
    total = stats.get("total", 0)
    surprising = stats.get("surprising", {})
    trust_before = stats.get("trust_before_avg", 0)
    trust_after = stats.get("trust_after_avg", 0)
    inf_avg = stats.get("influence_avg", {})

    # Surprising stage bars
    max_surprising = max(surprising.values()) if surprising and max(surprising.values()) > 0 else 1
    surprise_bars = []
    for key in ["embed", "retrieve", "synthesize", "influence", "none"]:
        count = surprising.get(key, 0)
        pct = int(round((count / max_surprising) * 100)) if max_surprising else 0
        color = _STAGE_COLORS.get(key, "#64748B")
        label = _STAGE_LABELS.get(key, key)
        votes_pct = int(round((count / total) * 100)) if total else 0
        surprise_bars.append(f"""
        <div class="aal-agg-bar-row">
          <div class="aal-agg-bar-label">{label}</div>
          <div class="aal-agg-bar-track">
            <div class="aal-agg-bar-fill" style="width:{pct}%; background:{color};"></div>
          </div>
          <div class="aal-agg-bar-val" style="color:{color};">{votes_pct}%</div>
        </div>
        """)

    # Trust shift
    trust_shift = round(trust_after - trust_before, 1)
    shift_sign = "+" if trust_shift > 0 else ""
    shift_color = "#34D399" if trust_shift > 0 else "#FB7185" if trust_shift < 0 else "#64748B"

    # Influence averages
    inf_bars = []
    for key, (label, color) in _INF_LABELS.items():
        score = inf_avg.get(key, 0)
        pct = int(round(score * 100))
        inf_bars.append(f"""
        <div class="aal-agg-bar-row">
          <div class="aal-agg-bar-label">{label}</div>
          <div class="aal-agg-bar-track">
            <div class="aal-agg-bar-fill" style="width:{pct}%; background:{color};"></div>
          </div>
          <div class="aal-agg-bar-val" style="color:{color};">{pct}%</div>
        </div>
        """)

    participant_text = f"{total} participant{'s' if total != 1 else ''}"
    if total == 0:
        participant_text = "No participants yet"

    return f"""
<div class="aal-agg-wrap">
  <div class="aal-influence-aurora">
    <div class="aal-think-blob aal-think-blob-b" style="opacity:0.12;"></div>
    <div class="aal-think-blob aal-think-blob-a" style="opacity:0.12;"></div>
  </div>

  <div class="aal-agg-inner">
    <div class="aal-agg-eyebrow">Step 6 &middot; How Everyone Answered</div>
    <h2 class="aal-agg-title">You&rsquo;re not alone. Here&rsquo;s how others reacted.</h2>
    <p class="aal-agg-subtitle">{participant_text} have completed this experience so far.</p>

    <div class="aal-agg-grid">
      <div class="aal-agg-card">
        <div class="aal-agg-card-title">Most Surprising Stage</div>
        <div class="aal-agg-card-body">
          {"".join(surprise_bars)}
        </div>
      </div>

      <div class="aal-agg-card">
        <div class="aal-agg-card-title">Trust Shift</div>
        <div class="aal-agg-card-body aal-agg-trust">
          <div class="aal-trust-row">
            <div class="aal-trust-label">Before seeing the pipeline</div>
            <div class="aal-trust-val">{trust_before:.1f}<span class="aal-trust-max"> / 5</span></div>
          </div>
          <div class="aal-trust-row">
            <div class="aal-trust-label">After seeing the pipeline</div>
            <div class="aal-trust-val">{trust_after:.1f}<span class="aal-trust-max"> / 5</span></div>
          </div>
          <div class="aal-trust-shift" style="color:{shift_color};">
            {shift_sign}{trust_shift} shift
          </div>
        </div>
      </div>

      <div class="aal-agg-card aal-agg-card-wide">
        <div class="aal-agg-card-title">Average Influence Scores Across All Responses</div>
        <div class="aal-agg-card-body">
          {"".join(inf_bars)}
        </div>
        <div class="aal-agg-card-footnote">
          Higher = more persuasion techniques detected in AI responses.
        </div>
      </div>
    </div>
  </div>
</div>
"""
