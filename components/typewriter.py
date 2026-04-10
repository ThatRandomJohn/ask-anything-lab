"""Typewriter text animation used by the Synthesize stage."""
import html as _html


def typewriter_html(text: str, label: str = "Step 4 \u00b7 Synthesize") -> str:
    """Render text that reveals itself via a CSS clip-path sweep."""
    escaped = _html.escape(text).replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
    char_count = max(1, len(text))
    duration = max(2500, char_count * 22)
    return f"""
<div style="background:#06080C; padding: 3em 3em 2em; min-height: 72vh;">
  <div style="max-width: 1100px; margin: 0 auto;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase; margin-bottom: 0.8em;">
      {_html.escape(label)}
    </div>
    <h2 style="color:#F1F5F9; font-size:1.9em; margin-top:0; margin-bottom:1.2em; font-weight:600;">
      The AI stitches an answer from what it found.
    </h2>
    <div class="tedx-typewriter" style="
        color: #F1F5F9;
        font-size: 1.75em;
        line-height: 1.55;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        clip-path: inset(0 100% 0 0);
        animation: tedxReveal {duration}ms steps({char_count}) forwards;
    ">{escaped}</div>
  </div>
</div>
<style>
@keyframes tedxReveal {{
  from {{ clip-path: inset(0 100% 0 0); }}
  to   {{ clip-path: inset(0 0 0 0); }}
}}
</style>
"""
