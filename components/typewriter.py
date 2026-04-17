"""Typewriter text animation used by the Synthesize stage."""
import html as _html


def typewriter_html(text: str, label: str = "Step 4 \u00b7 Synthesize") -> str:
    """Render LLM-style word-by-word streaming inside a gradient-bordered bubble."""
    paragraphs = text.split("\n\n")
    spans = []
    idx = 0
    for pi, para in enumerate(paragraphs):
        if pi > 0:
            spans.append("<br/><br/>")
        for word in para.split():
            delay = idx * 45
            escaped = _html.escape(word)
            spans.append(
                f'<span class="llm-word" style="animation-delay:{delay}ms">{escaped}</span>'
            )
            idx += 1
    body = " ".join(spans).replace(" <br/><br/> ", "<br/><br/>")
    return f"""
<div class="aal-synth-wrap">
  <div class="aal-synth-inner">
    <div class="aal-synth-eyebrow">{_html.escape(label)}</div>
    <h2 class="aal-synth-title">The AI stitches an answer from what it found.</h2>
    <div class="aal-message-bubble">
      <div class="aal-bubble-header">
        <span class="aal-bubble-header-dot"></span>
        AI response &middot; streaming
      </div>
      <div class="aal-bubble-body">{body}</div>
    </div>
  </div>
</div>
"""
