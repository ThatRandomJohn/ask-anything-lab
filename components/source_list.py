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


def render_sources(sources=None, label="Step 3 \u00b7 Retrieve"):
    if not sources:
        sources = DEMO_SOURCES
    return f"""
<div style="background:#06080C; padding: 2.5em 3em 2em; min-height: 72vh;">
  <div style="max-width: 1100px; margin: 0 auto;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase; margin-bottom: 0.5em;">
      {_html.escape(label)}
    </div>
    <h2 style="color: #F1F5F9; font-size: 2em; margin-top: 0; font-weight: 600;">
      The AI pulls from nearby knowledge.
    </h2>
    <p style="color: #64748B; font-size: 1.15em; margin-bottom: 1.5em;">
      Each source lives near your prompt in vector space. Proximity = relevance.
    </p>
    <div>{_render_source_rows(sources)}</div>
  </div>
</div>
<style>
@keyframes sourceFadeIn {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""
