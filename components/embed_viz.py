"""The 6-step embedding visualization.

This is the centerpiece of the TEDx talk. Every element must be readable from the
back row of a 300-seat venue. Dark background, big bold text, slow deliberate
animations, SVG so it scales to any projector.

Steps:
    0. The Sentence        (sets up: the prompt is just text)
    1. The Embedding Matrix (words become math)
    2. The Vector Space     (math becomes geometry)
    3. The Constellation    (geometry reveals meaning)
    4. The AI's Patterns    (the AI was trained on human suffering)
    5. The Bridge           (empathy is proximity)
"""
import html as _html

from data.demo import (
    PROMPT,
    USER_WORDS,
    AI_PATTERNS,
    BRIDGES,
    CLUSTERS,
    AI_CLUSTERS,
    EMBEDDING_VECTORS,
)


SVG_STYLE = """<defs><style type="text/css"><![CDATA[
  .fade-in   { opacity: 0; animation: tedxFadeIn 1000ms ease-out forwards; }
  .slow-fade { opacity: 0; animation: tedxFadeIn 1500ms ease-out forwards; }
  @keyframes tedxFadeIn { to { opacity: 1; } }
  .draw-line {
    stroke-dasharray: 2000;
    stroke-dashoffset: 2000;
    animation: tedxDraw 1500ms ease-out forwards;
  }
  @keyframes tedxDraw { to { stroke-dashoffset: 0; } }
  text { fill: #F1F5F9; }
]]></style></defs>"""


EMBED_STEP_LABELS = [
    "sentence",
    "matrix",
    "vector space",
    "constellation",
    "AI patterns",
    "bridge",
]


# ---------- main entry ----------

def render_embed_step(step: int) -> str:
    """Return the full HTML for one of the 6 embed sub-steps."""
    step = max(0, min(5, int(step)))
    inner = [
        _step_0_sentence,
        _step_1_matrix,
        _step_2_grid,
        _step_3_constellation,
        _step_4_patterns,
        _step_5_bridge,
    ][step]()
    label = EMBED_STEP_LABELS[step]
    return f"""
<div class="tedx-embed-wrapper" style="background:#06080C; width:100%; min-height: 88vh;">
  <div style="display:flex; justify-content:space-between; padding: 1.2em 2.5em 0.3em;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase;">
      Step 2 &middot; Embed &middot; {step + 1} / 6 &middot; {label}
    </div>
    <div style="color:#475569; font-size: 0.85em;">{_dots(step)}</div>
  </div>
  <svg viewBox="0 0 1500 880" xmlns="http://www.w3.org/2000/svg"
       style="width:100%; height:auto; display:block;"
       font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif">
    {SVG_STYLE}
    {inner}
  </svg>
</div>
"""


def _dots(step: int) -> str:
    out = []
    for i in range(6):
        color = "#F59E0B" if i == step else "#1E293B"
        out.append(f"<span style='display:inline-block; width:9px; height:9px; border-radius:50%; background:{color}; margin:0 3px;'></span>")
    return "".join(out)


# ---------- STEP 0: the sentence ----------

def _step_0_sentence() -> str:
    # Hardcoded line break for the demo prompt so it reads cleanly on stage.
    lines = [
        "I'm scared. My chest is tight.",
        "My heart is racing. I'm in the ER.",
        "My blood pressure is spiking.",
    ]
    out = []
    out.append('<text x="750" y="190" text-anchor="middle" font-size="26" fill="#64748B" class="slow-fade">THE PROMPT</text>')
    y0 = 340
    for i, line in enumerate(lines):
        y = y0 + i * 88
        delay = 300 + i * 280
        out.append(
            f'<text x="750" y="{y}" text-anchor="middle" font-size="54" font-style="italic" '
            f'fill="#F1F5F9" class="fade-in" style="animation-delay:{delay}ms">'
            f'&#8220;{_html.escape(line)}&#8221;</text>'
        )
    out.append(
        '<text x="750" y="720" text-anchor="middle" font-size="26" fill="#64748B" '
        'class="slow-fade" style="animation-delay:1500ms">'
        "The AI doesn&#8217;t read this as a sentence.</text>"
    )
    out.append(
        '<text x="750" y="758" text-anchor="middle" font-size="26" fill="#64748B" '
        'class="slow-fade" style="animation-delay:1800ms">'
        "It breaks it into pieces.</text>"
    )
    return "".join(out)


# ---------- STEP 1: the embedding matrix ----------

def _step_1_matrix() -> str:
    out = []
    out.append(
        '<text x="750" y="72" text-anchor="middle" font-size="34" fill="#F1F5F9" '
        'class="fade-in">Every word becomes numbers.</text>'
    )
    out.append(
        '<text x="200" y="150" font-size="18" fill="#64748B" font-weight="bold" '
        'letter-spacing="0.1em" class="fade-in">WORD</text>'
    )
    out.append(
        '<text x="500" y="150" font-size="18" fill="#64748B" font-weight="bold" '
        'letter-spacing="0.1em" class="fade-in">VECTOR (6 of thousands of dimensions)</text>'
    )
    out.append('<line x1="180" y1="170" x2="1360" y2="170" stroke="#1E293B" stroke-width="1" class="fade-in"/>')

    col_xs = [500, 650, 800, 950, 1100, 1250]
    y = 218
    for i, w in enumerate(USER_WORDS):
        delay = 300 + i * 180
        out.append(
            f'<text x="200" y="{y}" font-size="28" fill="{w["color"]}" font-weight="500" '
            f'class="fade-in" style="animation-delay:{delay}ms">{_html.escape(w["word"])}</text>'
        )
        vec = EMBEDDING_VECTORS[w["word"]]
        for j, v in enumerate(vec):
            out.append(
                f'<text x="{col_xs[j]}" y="{y}" font-size="26" fill="#F1F5F9" '
                f'font-family="SF Mono, Menlo, monospace" class="fade-in" '
                f'style="animation-delay:{delay + 80}ms">{v:+.2f}</text>'
            )
        y += 60

    out.append(
        '<text x="750" y="780" text-anchor="middle" font-size="24" fill="#64748B" '
        'class="fade-in" style="animation-delay:2200ms">'
        "Notice: &lsquo;scared&rsquo; and &lsquo;fear&rsquo; have nearly identical numbers.</text>"
    )
    out.append(
        '<text x="750" y="822" text-anchor="middle" font-size="26" fill="#F59E0B" '
        'font-weight="600" class="fade-in" style="animation-delay:2700ms">'
        "Similar numbers = similar meaning = nearby in space.</text>"
    )
    return "".join(out)


# ---------- STEP 2: the vector space grid ----------

def _step_2_grid() -> str:
    out = []
    out.append(
        '<text x="750" y="55" text-anchor="middle" font-size="32" fill="#F1F5F9" '
        'class="fade-in">Those numbers become coordinates.</text>'
    )

    # Grid background
    for gy in range(140, 441, 50):
        out.append(f'<line x1="150" y1="{gy}" x2="1380" y2="{gy}" stroke="#101827" stroke-width="1" class="fade-in"/>')
    for gx in range(150, 1381, 90):
        out.append(f'<line x1="{gx}" y1="140" x2="{gx}" y2="440" stroke="#101827" stroke-width="1" class="fade-in"/>')

    # Axes
    out.append('<line x1="150" y1="440" x2="1380" y2="440" stroke="#475569" stroke-width="2" class="fade-in"/>')
    out.append('<line x1="150" y1="140" x2="150" y2="440" stroke="#475569" stroke-width="2" class="fade-in"/>')
    out.append(
        '<text x="765" y="485" text-anchor="middle" font-size="18" fill="#64748B" '
        'class="fade-in">dimension 1 (of thousands)</text>'
    )
    out.append(
        '<text x="105" y="290" font-size="18" fill="#64748B" class="fade-in" '
        'transform="rotate(-90 105 290)" text-anchor="middle">dimension 2</text>'
    )

    # Dots + labels
    for i, w in enumerate(USER_WORDS):
        delay = 700 + i * 150
        out.append(
            f'<circle cx="{w["x"]}" cy="{w["y"]}" r="11" fill="{w["color"]}" '
            f'class="fade-in" style="animation-delay:{delay}ms"/>'
        )
        out.append(
            f'<text x="{w["x"] + 20}" y="{w["y"] + 9}" font-size="26" fill="{w["color"]}" '
            f'font-weight="500" class="fade-in" style="animation-delay:{delay}ms">{_html.escape(w["word"])}</text>'
        )

    # Dashed line between scared and fear
    scared = next(w for w in USER_WORDS if w["word"] == "scared")
    fear = next(w for w in USER_WORDS if w["word"] == "fear")
    out.append(
        f'<line x1="{scared["x"]}" y1="{scared["y"]}" x2="{fear["x"]}" y2="{fear["y"]}" '
        f'stroke="#F59E0B" stroke-width="3" stroke-dasharray="8,8" '
        f'class="fade-in" style="animation-delay:2400ms"/>'
    )

    out.append(
        '<text x="750" y="560" text-anchor="middle" font-size="26" fill="#F59E0B" '
        'font-weight="600" class="fade-in" style="animation-delay:2800ms">'
        "Close together = similar meaning</text>"
    )
    out.append(
        '<text x="750" y="610" text-anchor="middle" font-size="22" fill="#64748B" '
        'class="fade-in" style="animation-delay:3200ms">'
        "The geometry of meaning &mdash; in math.</text>"
    )
    return "".join(out)


# ---------- STEP 3: the constellation ----------

def _step_3_constellation() -> str:
    out = []
    out.append(
        '<text x="750" y="55" text-anchor="middle" font-size="32" fill="#F1F5F9" '
        'class="fade-in">Words cluster by meaning.</text>'
    )

    # Faint grid
    for gy in range(140, 441, 50):
        out.append(f'<line x1="150" y1="{gy}" x2="1380" y2="{gy}" stroke="#0B1220" stroke-width="1"/>')
    for gx in range(150, 1381, 90):
        out.append(f'<line x1="{gx}" y1="140" x2="{gx}" y2="440" stroke="#0B1220" stroke-width="1"/>')
    out.append('<line x1="150" y1="440" x2="1380" y2="440" stroke="#334155" stroke-width="2"/>')
    out.append('<line x1="150" y1="140" x2="150" y2="440" stroke="#334155" stroke-width="2"/>')

    # Cluster halos
    for i, (name, c) in enumerate(CLUSTERS.items()):
        delay = 300 + i * 350
        out.append(
            f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" '
            f'stroke="{c["color"]}" stroke-width="2.5" stroke-dasharray="10,10" opacity="0.72" '
            f'class="fade-in" style="animation-delay:{delay}ms"/>'
        )
        out.append(
            f'<text x="{c["cx"]}" y="{c["cy"] - c["r"] - 16}" text-anchor="middle" '
            f'font-size="22" fill="{c["color"]}" font-weight="700" '
            f'class="fade-in" style="animation-delay:{delay + 150}ms">{c["label"]}</text>'
        )

    # Words
    for w in USER_WORDS:
        out.append(f'<circle cx="{w["x"]}" cy="{w["y"]}" r="11" fill="{w["color"]}"/>')
        out.append(
            f'<text x="{w["x"] + 20}" y="{w["y"] + 9}" font-size="26" fill="{w["color"]}" '
            f'font-weight="500">{_html.escape(w["word"])}</text>'
        )

    # Cross-cluster line
    scared = next(w for w in USER_WORDS if w["word"] == "scared")
    er = next(w for w in USER_WORDS if w["word"] == "ER")
    out.append(
        f'<line x1="{scared["x"]}" y1="{scared["y"]}" x2="{er["x"]}" y2="{er["y"]}" '
        f'stroke="#F59E0B" stroke-width="2.5" stroke-dasharray="12,12" '
        f'class="draw-line" style="animation-delay:1800ms"/>'
    )
    out.append(
        '<text x="750" y="125" text-anchor="middle" font-size="20" fill="#F59E0B" '
        'class="fade-in" style="animation-delay:2500ms">'
        "far apart = different meaning</text>"
    )
    out.append(
        '<text x="750" y="560" text-anchor="middle" font-size="26" fill="#F1F5F9" '
        'class="fade-in" style="animation-delay:2800ms">Geometry reveals meaning.</text>'
    )
    return "".join(out)


# ---------- STEP 4: the AI's patterns ----------

def _step_4_patterns() -> str:
    out = []
    out.append(
        '<text x="750" y="55" text-anchor="middle" font-size="30" fill="#F1F5F9" '
        'class="fade-in">What the AI already knows.</text>'
    )

    # Top half: dimmed user words
    out.append(
        '<text x="150" y="105" font-size="18" fill="#64748B" font-weight="700" '
        'letter-spacing="0.1em">YOUR WORDS</text>'
    )
    for name, c in CLUSTERS.items():
        out.append(
            f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" '
            f'stroke="{c["color"]}" stroke-width="1.5" stroke-dasharray="8,8" opacity="0.45"/>'
        )
    for w in USER_WORDS:
        out.append(f'<circle cx="{w["x"]}" cy="{w["y"]}" r="9" fill="{w["color"]}" opacity="0.9"/>')
        out.append(
            f'<text x="{w["x"] + 16}" y="{w["y"] + 8}" font-size="24" fill="{w["color"]}" '
            f'opacity="0.9">{_html.escape(w["word"])}</text>'
        )

    # Divider line
    out.append(
        '<line x1="100" y1="460" x2="1400" y2="460" stroke="#475569" stroke-width="2" '
        'stroke-dasharray="14,14" class="draw-line"/>'
    )

    # AI patterns header
    out.append(
        '<text x="150" y="510" font-size="20" fill="#A78BFA" font-weight="700" '
        'letter-spacing="0.1em" class="fade-in" style="animation-delay:600ms">'
        "WHAT THE AI ALREADY KNOWS</text>"
    )
    out.append(
        '<text x="150" y="538" font-size="16" fill="#64748B" class="fade-in" '
        'style="animation-delay:800ms">Patterns learned from therapy transcripts, '
        "medical texts, and crisis counseling.</text>"
    )

    # AI cluster halos
    for i, (name, c) in enumerate(AI_CLUSTERS.items()):
        delay = 1100 + i * 300
        out.append(
            f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" '
            f'stroke="{c["color"]}" stroke-width="2" stroke-dasharray="10,10" opacity="0.62" '
            f'class="fade-in" style="animation-delay:{delay}ms"/>'
        )
        out.append(
            f'<text x="{c["cx"]}" y="{c["cy"] + c["r"] + 30}" text-anchor="middle" '
            f'font-size="16" fill="{c["color"]}" font-style="italic" '
            f'class="fade-in" style="animation-delay:{delay + 200}ms">{c["label"]}</text>'
        )

    # AI pattern entities
    for i, p in enumerate(AI_PATTERNS):
        delay = 1500 + i * 220
        font_style = "italic" if p["cluster"] == "ai_empathy" else "normal"
        out.append(
            f'<circle cx="{p["x"]}" cy="{p["y"]}" r="9" fill="{p["color"]}" '
            f'class="fade-in" style="animation-delay:{delay}ms"/>'
        )
        out.append(
            f'<text x="{p["x"] + 16}" y="{p["y"] + 8}" font-size="24" fill="{p["color"]}" '
            f'font-style="{font_style}" class="fade-in" style="animation-delay:{delay}ms">'
            f'{_html.escape(p["text"])}</text>'
        )

    return "".join(out)


# ---------- STEP 5: the bridge ----------

def _step_5_bridge() -> str:
    out = []
    out.append(
        '<text x="750" y="55" text-anchor="middle" font-size="30" fill="#F1F5F9" '
        'class="fade-in">Proximity becomes empathy.</text>'
    )

    # Top half
    for name, c in CLUSTERS.items():
        out.append(
            f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" '
            f'stroke="{c["color"]}" stroke-width="1.5" stroke-dasharray="8,8" opacity="0.35"/>'
        )
    for w in USER_WORDS:
        out.append(f'<circle cx="{w["x"]}" cy="{w["y"]}" r="9" fill="{w["color"]}"/>')
        out.append(
            f'<text x="{w["x"] + 16}" y="{w["y"] + 8}" font-size="24" '
            f'fill="{w["color"]}">{_html.escape(w["word"])}</text>'
        )

    # Divider
    out.append(
        '<line x1="100" y1="460" x2="1400" y2="460" stroke="#475569" stroke-width="1.5" '
        'stroke-dasharray="12,12" opacity="0.5"/>'
    )

    # Bottom half
    for name, c in AI_CLUSTERS.items():
        out.append(
            f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" '
            f'stroke="{c["color"]}" stroke-width="1.5" stroke-dasharray="8,8" opacity="0.35"/>'
        )
    for p in AI_PATTERNS:
        font_style = "italic" if p["cluster"] == "ai_empathy" else "normal"
        out.append(f'<circle cx="{p["x"]}" cy="{p["y"]}" r="9" fill="{p["color"]}"/>')
        out.append(
            f'<text x="{p["x"] + 16}" y="{p["y"] + 8}" font-size="24" fill="{p["color"]}" '
            f'font-style="{font_style}">{_html.escape(p["text"])}</text>'
        )

    # Bridge lines
    word_by_name = {w["word"]: w for w in USER_WORDS}
    pat_by_text = {p["text"]: p for p in AI_PATTERNS}
    for i, (word, pat) in enumerate(BRIDGES):
        w = word_by_name.get(word)
        p = pat_by_text.get(pat)
        if w and p:
            delay = 400 + i * 350
            out.append(
                f'<line x1="{w["x"]}" y1="{w["y"]}" x2="{p["x"]}" y2="{p["y"]}" '
                f'stroke="#F59E0B" stroke-width="3.5" stroke-dasharray="10,10" '
                f'opacity="0.88" class="draw-line" style="animation-delay:{delay}ms"/>'
            )

    # Punchline
    out.append(
        '<text x="750" y="835" text-anchor="middle" font-size="38" font-weight="700" '
        'fill="#F59E0B" class="slow-fade" style="animation-delay:3000ms">'
        "The empathy you feel is proximity &mdash; not comprehension.</text>"
    )
    return "".join(out)


# ---------- audience-mode embed viz (LLM-generated data) ----------

def render_audience_embed(prompt: str, embeddings: dict) -> str:
    """Render the audience-mode version using LLM-assigned word positions."""
    from collections import defaultdict

    words = (embeddings or {}).get("words", []) or []
    palette = ["#F97316", "#06B6D4", "#3B82F6", "#A78BFA", "#34D399", "#F59E0B"]

    groups = defaultdict(list)
    for w in words:
        groups[str(w.get("cluster", "default"))].append(w)
    color_map = {}
    for i, name in enumerate(groups.keys()):
        color_map[name] = palette[i % len(palette)]

    def _nx(w):
        return 100 + max(0.05, min(0.95, float(w.get("x", 0.5)))) * 1300

    def _ny(w):
        # Incoming y is 0.25–0.48. Stretch to fill roughly 130–560.
        raw = float(w.get("y", 0.35))
        return 130 + max(0.0, min(1.0, (raw - 0.1) / 0.6)) * 430

    svg_parts = [f"""
<div class="tedx-embed-wrapper" style="background:#06080C; width:100%; min-height:74vh; padding: 0.8em 0 2em;">
  <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase; margin: 0.5em 2.5em 0.3em;">
    Step 2 &middot; Embed
  </div>
  <div style="max-width: 980px; margin: 0.2em auto 1em; padding: 0 2em;">
    <div style="color:#F1F5F9; font-size: 1.5em; font-style: italic; line-height: 1.45;">&ldquo;{_html.escape(prompt)}&rdquo;</div>
    <div style="color:#64748B; margin-top: 0.7em; font-size: 1.05em;">
      Your words became vectors. Each cluster is a region of meaning in the model&rsquo;s space.
    </div>
  </div>
  <svg viewBox="0 0 1500 700" xmlns="http://www.w3.org/2000/svg"
       style="width:100%; height:auto; display:block;"
       font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif">
    {SVG_STYLE}
"""]

    # Grid background
    for gy in range(120, 601, 60):
        svg_parts.append(f'<line x1="100" y1="{gy}" x2="1400" y2="{gy}" stroke="#101827" stroke-width="1"/>')
    for gx in range(100, 1401, 100):
        svg_parts.append(f'<line x1="{gx}" y1="120" x2="{gx}" y2="600" stroke="#101827" stroke-width="1"/>')
    svg_parts.append('<line x1="100" y1="600" x2="1400" y2="600" stroke="#475569" stroke-width="2"/>')
    svg_parts.append('<line x1="100" y1="120" x2="100" y2="600" stroke="#475569" stroke-width="2"/>')
    svg_parts.append('<text x="750" y="640" text-anchor="middle" font-size="18" fill="#64748B">dimension 1 (of thousands)</text>')

    # Cluster halos (first, so words draw on top)
    for name, ws in groups.items():
        if len(ws) < 2:
            continue
        cx = sum(_nx(w) for w in ws) / len(ws)
        cy = sum(_ny(w) for w in ws) / len(ws)
        color = color_map[name]
        svg_parts.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="130" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-dasharray="8,8" opacity="0.5" '
            f'class="fade-in" style="animation-delay:1800ms"/>'
        )
        svg_parts.append(
            f'<text x="{cx:.0f}" y="{cy - 142:.0f}" text-anchor="middle" font-size="20" '
            f'fill="{color}" font-weight="700" class="fade-in" style="animation-delay:2000ms">'
            f'{_html.escape(name)}</text>'
        )

    # Words
    for i, w in enumerate(words):
        nx = _nx(w)
        ny = _ny(w)
        color = color_map.get(str(w.get("cluster", "default")), "#F1F5F9")
        text = _html.escape(str(w.get("word", "")))
        delay = 250 + i * 90
        svg_parts.append(
            f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="9" fill="{color}" '
            f'class="fade-in" style="animation-delay:{delay}ms"/>'
        )
        svg_parts.append(
            f'<text x="{nx + 14:.0f}" y="{ny + 8:.0f}" font-size="22" fill="{color}" '
            f'class="fade-in" style="animation-delay:{delay}ms">{text}</text>'
        )

    svg_parts.append("</svg></div>")
    return "".join(svg_parts)
