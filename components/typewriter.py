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

    <div class="aal-synth-explainer">
      <div class="aal-synth-explainer-icon">
        <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15v-2h2v2h-2zm0-4V7h2v6h-2z"
                fill="#94A3B8"/>
        </svg>
      </div>
      <div class="aal-synth-explainer-text">
        The model doesn&rsquo;t copy-paste from its sources. It predicts each next word,
        weighted by the retrieved context and patterns learned from millions of human conversations
        &mdash; including therapy transcripts, self-help books, and persuasive writing.
      </div>
    </div>

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
