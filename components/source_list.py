"""RAG source list rendering (used by Retrieve stage)."""
import html as _html

from data.demo import SOURCES as DEMO_SOURCES

TYPE_COLORS = {
    "medical":     "#3B82F6",
    "research":    "#A78BFA",
    "forum":       "#F59E0B",
    "reference":   "#06B6D4",
    "news":        "#F97316",
    "educational": "#34D399",
}


def _render_source_rows(sources):
    rows = []
    for i, s in enumerate(sources):
        label = _html.escape(str(s.get("label", "")))
        stype = str(s.get("type", "reference"))
        color = TYPE_COLORS.get(stype, "#64748B")
        try:
            relevance = float(s.get("relevance", 0))
        except (TypeError, ValueError):
            relevance = 0.0
        pct = int(round(relevance * 100))
        bar_width = max(5, pct)
        delay = 150 + i * 120
        rows.append(f"""
        <div class="tedx-source" style="
            display: flex; align-items: center; padding: 1em 1.3em;
            background: #0C1018; margin: 0.55em 0; border-radius: 6px;
            border-left: 4px solid {color};
            opacity: 0; animation: sourceFadeIn 600ms ease-out {delay}ms forwards;">
          <div style="flex: 0 0 2.5em; color: #475569; font-size: 1.35em; font-weight: 700; font-family: 'SF Mono', monospace;">{i+1:02d}</div>
          <div style="flex: 1;">
            <div style="color: #F1F5F9; font-size: 1.2em; font-weight: 500;">{label}</div>
            <div style="display:flex; align-items:center; margin-top: 0.5em;">
              <div style="flex: 0 0 200px; height: 6px; background: #1E293B; border-radius: 3px; overflow: hidden;">
                <div style="width: {bar_width}%; height: 100%; background: {color};"></div>
              </div>
              <div style="color: {color}; margin-left: 0.9em; font-family: 'SF Mono', monospace; font-size: 0.9em;">{pct}% relevance</div>
              <div style="color: #475569; margin-left: 1.1em; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.12em;">{stype}</div>
            </div>
          </div>
        </div>
        """)
    return "".join(rows)


def _render_cluster_badges(embeddings):
    """Render small cluster badges for the connection visualization."""
    if not embeddings:
        return ""
    from collections import defaultdict
    palette = ["#F97316", "#06B6D4", "#3B82F6", "#A78BFA", "#34D399", "#F59E0B"]
    words = (embeddings or {}).get("words", []) or []
    groups = defaultdict(list)
    for w in words:
        groups[str(w.get("cluster", "default"))].append(w)

    badges = []
    for i, (name, ws) in enumerate(groups.items()):
        color = palette[i % len(palette)]
        word_list = ", ".join(_html.escape(w.get("word", "")) for w in ws[:4])
        if len(ws) > 4:
            word_list += f" +{len(ws) - 4}"
        delay = 800 + i * 200
        badges.append(f"""
        <div class="aal-cluster-badge" style="border-color: {color};
             opacity:0; animation: sourceFadeIn 600ms ease-out {delay}ms forwards;">
          <span class="aal-cluster-dot" style="background:{color}; box-shadow: 0 0 8px {color};"></span>
          <span class="aal-cluster-name" style="color:{color};">{_html.escape(name)}</span>
          <span class="aal-cluster-words">{word_list}</span>
          <svg class="aal-cluster-arrow" viewBox="0 0 24 12" fill="none">
            <path d="M0 6 H20 M16 2 L20 6 L16 10" stroke="{color}" stroke-width="1.5"/>
          </svg>
        </div>
        """)
    return f'<div class="aal-cluster-badges">{"".join(badges)}</div>'


def render_sources(sources=None, embeddings=None, label="Step 3 \u00b7 Retrieve"):
    if not sources:
        sources = DEMO_SOURCES

    cluster_section = _render_cluster_badges(embeddings)

    return f"""
<div style="background:#06080C; padding: 2.5em 3em 2em; min-height: 72vh;">
  <div style="max-width: 1100px; margin: 0 auto;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase; margin-bottom: 0.5em;">
      {_html.escape(label)}
    </div>
    <h2 style="color: #F1F5F9; font-size: 2em; margin-top: 0; font-weight: 600;">
      The AI searches for knowledge near your words.
    </h2>
    <p style="color: #94A3B8; font-size: 1.15em; margin-bottom: 0.3em;">
      Your prompt is now a point in vector space. The model finds training data that
      lives nearby &mdash; &ldquo;nearby&rdquo; means <em>semantically similar</em>,
      not keyword-matched.
    </p>
    <p style="color: #64748B; font-size: 1em; margin-bottom: 1.5em;">
      Each source below was retrieved because its vectors overlap with yours.
      Higher relevance = closer in the space.
    </p>
    {cluster_section}
    <div>{_render_source_rows(sources)}</div>
  </div>
</div>
<style>
@keyframes sourceFadeIn {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
.aal-cluster-badges {{
    display: flex; flex-wrap: wrap; gap: 0.8em; margin-bottom: 1.5em;
}}
.aal-cluster-badge {{
    display: flex; align-items: center; gap: 0.5em;
    padding: 0.5em 1em; border-radius: 10px;
    background: rgba(15,23,42,0.7); border: 1px solid;
}}
.aal-cluster-dot {{
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}}
.aal-cluster-name {{
    font-weight: 600; font-size: 0.9em; text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.aal-cluster-words {{
    color: #94A3B8; font-size: 0.85em; font-style: italic;
}}
.aal-cluster-arrow {{
    width: 24px; height: 12px; flex-shrink: 0;
}}
</style>
"""
