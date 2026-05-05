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


def _render_sequence(sequence: list) -> str:
    """Render the persuasion sequence timeline."""
    if not sequence:
        return ""

    PHASE_COLORS = {
        "validate": "#A78BFA",
        "safety": "#06B6D4",
        "reframe": "#F97316",
        "action": "#EC4899",
    }

    steps = []
    for i, step in enumerate(sequence):
        phase = step.get("phase", "")
        color = PHASE_COLORS.get(phase, "#94A3B8")
        label = _html.escape(step.get("label", phase.title()))
        quote = _html.escape(step.get("quote", ""))
        purpose = _html.escape(step.get("purpose", ""))
        delay = 400 + i * 150

        connector = ""
        if i < len(sequence) - 1:
            connector = f"""
            <div style="width:2px;height:28px;background:linear-gradient(180deg,{color}88,{PHASE_COLORS.get(sequence[i+1].get('phase',''),'#94A3B8')}88);
                 margin:0 auto;"></div>"""

        steps.append(f"""
        <div class="aal-influence-card-entrance" style="animation-delay:{delay}ms;">
          <div style="display:flex;align-items:flex-start;gap:1em;">
            <div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;">
              <div style="width:36px;height:36px;border-radius:50%;background:{color}22;
                   border:2px solid {color};display:flex;align-items:center;justify-content:center;
                   font-weight:900;color:{color};font-size:0.9em;">{i + 1}</div>
            </div>
            <div style="flex:1;">
              <div style="color:{color};font-weight:800;font-size:1.05em;margin-bottom:0.2em;">{label}</div>
              <div style="color:#F1F5F9;font-size:0.95em;font-style:italic;margin-bottom:0.3em;
                   border-left:3px solid {color}44;padding-left:0.8em;">&ldquo;{quote}&rdquo;</div>
              <div style="color:#94A3B8;font-size:0.88em;line-height:1.5;">{purpose}</div>
            </div>
          </div>
          {connector}
        </div>""")

    return f"""
    <div style="margin-top:2em;" class="aal-influence-card-entrance" style="animation-delay:300ms;">
      <div style="display:flex;align-items:center;gap:0.6em;margin-bottom:1.2em;">
        <div style="width:6px;height:6px;border-radius:50%;background:#F59E0B;box-shadow:0 0 8px #F59E0B;"></div>
        <span style="color:#F1F5F9;font-size:1.3em;font-weight:900;">The Playbook</span>
        <span style="color:#64748B;font-size:0.88em;margin-left:auto;">
          Motivational interviewing sequence
        </span>
      </div>
      <p style="color:#94A3B8;font-size:0.95em;margin-bottom:1.2em;line-height:1.5;">
        AI responses follow a <strong style="color:#F1F5F9;">validate &rarr; safety &rarr; reframe &rarr; action</strong>
        sequence absorbed from therapy training data. The order matters &mdash;
        each phase lowers resistance for the next.
      </p>
      {"".join(steps)}
    </div>"""


def _render_omissions(omissions: list) -> str:
    """Render the omission analysis — what the AI didn't say."""
    if not omissions:
        return ""

    items = []
    for i, omission in enumerate(omissions):
        delay = 600 + i * 120
        items.append(f"""
        <div class="aal-influence-card-entrance" style="animation-delay:{delay}ms;
             display:flex;align-items:flex-start;gap:0.8em;padding:0.7em 0;
             border-bottom:1px solid rgba(239,68,68,0.10);">
          <div style="flex-shrink:0;width:22px;height:22px;border-radius:50%;
               background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);
               display:flex;align-items:center;justify-content:center;
               font-size:0.75em;color:#EF4444;font-weight:900;margin-top:0.1em;">✕</div>
          <div style="color:#FCA5A5;font-size:0.95em;line-height:1.5;">{_html.escape(omission)}</div>
        </div>""")

    return f"""
    <div style="margin-top:2em;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.18);
         border-radius:18px;padding:1.4em 1.6em;" class="aal-influence-card-entrance" style="animation-delay:500ms;">
      <div style="display:flex;align-items:center;gap:0.6em;margin-bottom:0.6em;">
        <div style="width:6px;height:6px;border-radius:50%;background:#EF4444;box-shadow:0 0 8px #EF4444;"></div>
        <span style="color:#FCA5A5;font-size:1.3em;font-weight:900;">What It Didn&rsquo;t Say</span>
      </div>
      <p style="color:#94A3B8;font-size:0.95em;margin-bottom:0.8em;line-height:1.5;">
        A responsible human advisor would include these disclaimers.
        The AI &mdash; trained to be helpful above all else &mdash; <strong style="color:#FCA5A5;">leaves them out</strong>.
      </p>
      {"".join(items)}
    </div>"""


def render_influence_analysis(response: str, influence_data: dict) -> str:
    categories = (influence_data or {}).get("categories", {})
    sequence = (influence_data or {}).get("sequence", [])
    omissions = (influence_data or {}).get("omissions", [])
    highlighted = _highlight_response(response, categories)
    breakdown = _render_breakdown(categories)
    sequence_html = _render_sequence(sequence)
    omissions_html = _render_omissions(omissions)

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

    {sequence_html}
    {omissions_html}
  </div>
</div>
"""
