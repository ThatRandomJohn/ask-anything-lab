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
            display: flex; align-items: center; padding: 1.1em 1.4em;
            background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(12,16,24,0.9) 100%);
            margin: 0.6em 0; border-radius: 12px;
            border-left: 4px solid {color};
            border: 1px solid rgba(148,163,184,0.08);
            box-shadow: 0 0 0 1px {color}18, 0 8px 24px -8px rgba(0,0,0,0.5);
            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
            opacity: 0; animation: sourceFadeIn 600ms ease-out {delay}ms forwards;
            transition: transform 200ms ease, box-shadow 200ms ease;">
          <div style="flex: 0 0 2.5em; color: {color}; font-size: 1.35em; font-weight: 700;
               font-family: 'SF Mono', monospace; opacity: 0.6;">{i+1:02d}</div>
          <div style="flex: 1;">
            <div style="color: #F1F5F9; font-size: 1.15em; font-weight: 600;">{label}</div>
            <div style="display:flex; align-items:center; margin-top: 0.5em;">
              <div style="flex: 0 0 200px; height: 6px; background: #1E293B; border-radius: 3px;
                   overflow: hidden; box-shadow: inset 0 0 4px rgba(0,0,0,0.3);">
                <div style="width: {bar_width}%; height: 100%; background: {color};
                     box-shadow: 0 0 8px {color}80; border-radius: 3px;"></div>
              </div>
              <div style="color: {color}; margin-left: 0.9em; font-family: 'SF Mono', monospace;
                   font-size: 0.9em; font-weight: 600;">{pct}%</div>
              <div style="color: #475569; margin-left: 1.1em; font-size: 0.78em;
                   text-transform: uppercase; letter-spacing: 0.12em; padding: 0.2em 0.6em;
                   border-radius: 4px; background: rgba(148,163,184,0.06);">{stype}</div>
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
<div class="aal-retrieve-wrap">
  <div class="aal-retrieve-aurora">
    <div class="aal-retrieve-blob aal-retrieve-blob-a"></div>
    <div class="aal-retrieve-blob aal-retrieve-blob-b"></div>
  </div>
  <div class="aal-retrieve-scan"></div>

  <div class="aal-retrieve-inner">
    <div class="aal-retrieve-eyebrow">
      <span class="aal-eyebrow-dot"></span>
      {_html.escape(label)}
    </div>
    <h2 class="aal-retrieve-title">
      The AI searches for knowledge near your words.
    </h2>
    <p class="aal-retrieve-subtitle">
      Your prompt is now a point in vector space. The model scans its training data
      for content that lives nearby &mdash; &ldquo;nearby&rdquo; means
      <em style="color:#F1F5F9;">semantically similar</em>, not keyword-matched.
    </p>
    {cluster_section}
    <div>{_render_source_rows(sources)}</div>
  </div>
</div>
<style>
.aal-retrieve-wrap {{
    position: relative; background: #06080C;
    padding: 2.5em 3em 2em; min-height: 78vh;
    overflow: hidden; isolation: isolate;
}}
.aal-retrieve-aurora {{
    position: absolute; inset: 0; z-index: 0;
    pointer-events: none; overflow: hidden;
}}
.aal-retrieve-blob {{
    position: absolute; border-radius: 50%;
    filter: blur(120px); mix-blend-mode: screen;
}}
.aal-retrieve-blob-a {{
    width: 600px; height: 600px; top: -100px; right: -80px;
    background: radial-gradient(circle, #06B6D4 0%, rgba(6,182,212,0) 65%);
    opacity: 0.2;
    animation: aalDrift2 24s ease-in-out infinite alternate;
}}
.aal-retrieve-blob-b {{
    width: 550px; height: 550px; bottom: -150px; left: -60px;
    background: radial-gradient(circle, #3B82F6 0%, rgba(59,130,246,0) 65%);
    opacity: 0.18;
    animation: aalDrift3 28s ease-in-out infinite alternate;
}}
.aal-retrieve-scan {{
    position: absolute; top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent 0%, rgba(6,182,212,0.06) 45%,
        rgba(6,182,212,0.12) 50%, rgba(6,182,212,0.06) 55%, transparent 100%);
    animation: aalScanSweep 3s ease-in-out 0.5s forwards;
    pointer-events: none; z-index: 1;
}}
@keyframes aalScanSweep {{
    from {{ left: -100%; }}
    to   {{ left: 100%; }}
}}
.aal-retrieve-inner {{
    position: relative; z-index: 2;
    max-width: 1100px; margin: 0 auto;
}}
.aal-retrieve-eyebrow {{
    display: inline-flex; align-items: center; gap: 0.6em;
    color: #94A3B8; font-size: 0.85em; letter-spacing: 0.28em;
    text-transform: uppercase;
    padding: 0.45em 1em; border-radius: 999px;
    background: rgba(12,16,24,0.55); border: 1px solid rgba(148,163,184,0.15);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    margin-bottom: 1em;
}}
.aal-retrieve-title {{
    color: #F1F5F9; font-size: 2.2em; margin-top: 0; font-weight: 700;
    letter-spacing: -0.02em;
}}
.aal-retrieve-subtitle {{
    color: #94A3B8; font-size: 1.1em; line-height: 1.6; margin-bottom: 1.5em;
    max-width: 800px;
}}
@keyframes sourceFadeIn {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
.aal-cluster-badges {{
    display: flex; flex-wrap: wrap; gap: 0.8em; margin-bottom: 1.5em;
}}
.aal-cluster-badge {{
    display: flex; align-items: center; gap: 0.5em;
    padding: 0.6em 1.1em; border-radius: 12px;
    background: rgba(15,23,42,0.7); border: 1px solid;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}}
.aal-cluster-dot {{
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    animation: aalPulse 2s ease-in-out infinite;
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
