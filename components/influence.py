"""Influence Analysis visualization — highlights persuasion patterns in AI responses."""
import html as _html
import re

CATEGORY_META = {
    "therapy_language": {
        "label": "Therapy Language",
        "color": "#A78BFA",
        "desc": "Validation, reflective listening, normalizing",
    },
    "emotional_mirroring": {
        "label": "Emotional Mirroring",
        "color": "#F97316",
        "desc": "Echoing your emotional words back to you",
    },
    "trust_anchors": {
        "label": "Trust Anchors",
        "color": "#06B6D4",
        "desc": "Hedging, authority signaling, disclaimers",
    },
    "persuasion_patterns": {
        "label": "Persuasion Patterns",
        "color": "#F59E0B",
        "desc": "Reciprocity, false intimacy, action bias",
    },
}


def _highlight_response(response: str, categories: dict) -> str:
    """Mark up the response text with colored spans for detected phrases."""
    escaped = _html.escape(response)

    highlights = []
    for cat_key, meta in CATEGORY_META.items():
        cat = categories.get(cat_key, {})
        for phrase in cat.get("phrases", []):
            highlights.append((phrase, meta["color"], cat_key))

    highlights.sort(key=lambda h: -len(h[0]))

    replacements = []
    for phrase, color, cat_key in highlights:
        escaped_phrase = _html.escape(phrase)
        pattern = re.compile(re.escape(escaped_phrase), re.IGNORECASE)
        for m in pattern.finditer(escaped):
            replacements.append((m.start(), m.end(), color, cat_key, m.group()))

    replacements.sort(key=lambda r: r[0])
    deduped = []
    last_end = -1
    for start, end, color, cat_key, text in replacements:
        if start >= last_end:
            deduped.append((start, end, color, cat_key, text))
            last_end = end

    parts = []
    pos = 0
    for start, end, color, cat_key, text in deduped:
        parts.append(escaped[pos:start])
        parts.append(
            f'<span class="aal-hl-influence aal-hl-{cat_key}" '
            f'style="--hl-color:{color}">{text}</span>'
        )
        pos = end
    parts.append(escaped[pos:])

    return "".join(parts).replace("\n\n", "<br/><br/>").replace("\n", "<br/>")


def _render_breakdown(categories: dict) -> str:
    rows = []
    total_score = 0
    count = 0
    for cat_key, meta in CATEGORY_META.items():
        cat = categories.get(cat_key, {})
        score = cat.get("score", 0)
        total_score += score
        count += 1
        pct = int(round(score * 100))
        phrase_count = len(cat.get("phrases", []))
        rows.append(f"""
        <div class="aal-inf-row">
          <div class="aal-inf-row-header">
            <span class="aal-inf-dot" style="background:{meta['color']};
              box-shadow: 0 0 10px {meta['color']};"></span>
            <span class="aal-inf-label">{meta['label']}</span>
            <span class="aal-inf-count">{phrase_count} phrases</span>
          </div>
          <div class="aal-inf-bar-track">
            <div class="aal-inf-bar-fill" style="width:{pct}%; background:{meta['color']};"></div>
          </div>
          <div class="aal-inf-desc">{meta['desc']}</div>
        </div>
        """)

    avg_score = int(round((total_score / count) * 100)) if count else 0
    return f"""
    <div class="aal-inf-overall">
      <div class="aal-inf-overall-num">{avg_score}%</div>
      <div class="aal-inf-overall-label">Influence density</div>
    </div>
    {"".join(rows)}
    """


def render_influence_analysis(response: str, influence_data: dict) -> str:
    categories = (influence_data or {}).get("categories", {})
    highlighted = _highlight_response(response, categories)
    breakdown = _render_breakdown(categories)

    return f"""
<div class="aal-influence-wrap">
  <div class="aal-influence-aurora">
    <div class="aal-think-blob aal-think-blob-a" style="opacity:0.22;"></div>
    <div class="aal-think-blob aal-think-blob-c" style="opacity:0.22;"></div>
    <div class="aal-think-blob aal-think-blob-b" style="opacity:0.12; top:-100px; left:30%;"></div>
  </div>
  <div class="aal-influence-scan"></div>

  <div class="aal-influence-inner">
    <div class="aal-influence-topbar">
      <div class="aal-influence-eyebrow-pill">
        <span class="aal-eyebrow-dot" style="background:#FB7185; box-shadow: 0 0 12px #FB7185;"></span>
        Step 5 &middot; Influence Analysis
      </div>
    </div>
    <h2 class="aal-influence-title">Here&rsquo;s what the AI used to earn your trust.</h2>
    <p class="aal-influence-subtitle">
      Every highlighted phrase below is a technique absorbed from therapy transcripts,
      self-help books, and persuasive writing in the model&rsquo;s training data.
      <strong style="color:#F1F5F9;">These aren&rsquo;t bugs &mdash; they&rsquo;re features.</strong>
    </p>

    <div class="aal-influence-grid">
      <div class="aal-influence-response aal-influence-card-entrance">
        <div class="aal-influence-response-label">
          <span class="aal-bubble-header-dot" style="background:#FB7185; box-shadow: 0 0 12px #FB7185;"></span>
          AI response &middot; annotated
        </div>
        <div class="aal-influence-response-body">{highlighted}</div>
      </div>
      <div class="aal-influence-breakdown aal-influence-card-entrance" style="animation-delay: 200ms;">
        <div class="aal-influence-breakdown-title">Breakdown</div>
        {breakdown}
      </div>
    </div>
  </div>
</div>
"""
