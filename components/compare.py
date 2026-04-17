"""Cold-vs-warm compare stage.

Renders two matched prompts side by side and lets the audience see the
same model produce radically different responses based on register alone.
The data comes from data.demo (COLD_*, WARM_*).
"""
import html as _html
import re

from components.embed_viz import stage_progress
from data.demo import (
    COMPARE_PUNCHLINE,
    COMPARE_THESIS,
    COLD_HIGHLIGHTS,
    COLD_LABEL,
    COLD_PROMPT,
    COLD_RESPONSE,
    WARM_HIGHLIGHTS,
    WARM_LABEL,
    WARM_PROMPT,
    WARM_RESPONSE,
)


def _highlight(text: str, needles, hl_class: str) -> str:
    """Case-insensitive regex highlight — wraps each matched needle in a span."""
    escaped = _html.escape(text)
    for needle in needles:
        pattern = re.compile(re.escape(_html.escape(needle)), re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f'<span class="{hl_class}">{m.group(0)}</span>',
            escaped,
        )
    # Preserve paragraph breaks
    return escaped.replace("\n\n", "</p><p>").replace("\n", "<br/>")


def render_compare_stage() -> str:
    cold_body = _highlight(COLD_RESPONSE, COLD_HIGHLIGHTS, "aal-hl-cold")
    warm_body = _highlight(WARM_RESPONSE, WARM_HIGHLIGHTS, "aal-hl-warm")

    return f"""
<div class="aal-compare-wrap">
  <div class="aal-compare-aurora">
    <div class="aal-compare-glow aal-glow-cold"></div>
    <div class="aal-compare-glow aal-glow-warm"></div>
  </div>

  <div class="aal-compare-topbar">
    <div class="aal-compare-eyebrow">Step 4 &middot; Compare</div>
    <div>{stage_progress(3)}</div>
  </div>

  <div class="aal-compare-header">
    <h1 class="aal-compare-title">{_html.escape(COMPARE_THESIS)}</h1>
    <div class="aal-compare-subtitle">
      We sent two versions of the same situation to the same model.
      One used clinical words. One used emotional words.
    </div>
  </div>

  <div class="aal-compare-grid">
    <div class="aal-compare-col aal-col-cold">
      <div class="aal-col-tag aal-tag-cold">{_html.escape(COLD_LABEL)}</div>
      <div class="aal-col-prompt">
        <div class="aal-col-prompt-label">Prompt</div>
        <p>{_html.escape(COLD_PROMPT)}</p>
      </div>
      <div class="aal-col-response">
        <div class="aal-col-response-label">
          <span class="aal-col-dot aal-dot-cold"></span>
          Claude responds
        </div>
        <div class="aal-col-body"><p>{cold_body}</p></div>
      </div>
    </div>

    <div class="aal-compare-col aal-col-warm">
      <div class="aal-col-tag aal-tag-warm">{_html.escape(WARM_LABEL)}</div>
      <div class="aal-col-prompt">
        <div class="aal-col-prompt-label">Prompt</div>
        <p>{_html.escape(WARM_PROMPT)}</p>
      </div>
      <div class="aal-col-response">
        <div class="aal-col-response-label">
          <span class="aal-col-dot aal-dot-warm"></span>
          Claude responds
        </div>
        <div class="aal-col-body"><p>{warm_body}</p></div>
      </div>
    </div>
  </div>

  <div class="aal-compare-punchline">
    {_html.escape(COMPARE_PUNCHLINE)}
  </div>
</div>
"""
