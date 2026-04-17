"""The 5-step embedding visualization.

This is the centerpiece of the TEDx talk. Every element must be readable from the
back row of a 300-seat venue. Dark background, big bold text, slow deliberate
animations, SVG so it scales to any projector.

Steps:
    0. The Sentence        (sets up: the prompt is just text)
    1. The Embedding Matrix (words become math)
    2. The Vector Space     (math becomes geometry, clusters emerge)
    3. The AI's Patterns    (the AI was trained on human suffering)
    4. The Bridge           (empathy is proximity)
"""
import html as _html
import math

from data.demo import (
    PROMPT,
    USER_WORDS,
    EXTRA_WORDS,
    AI_PATTERNS,
    BRIDGES,
    CLUSTERS,
    AI_CLUSTERS,
    EMBEDDING_VECTORS,
)

# ---------- 3D oblique-cabinet projection helpers ----------

_3D_ANGLE = math.radians(30)
_3D_DEPTH = 0.5


def _project(x3d, y3d, z3d):
    """Oblique cabinet projection: 3D → 2D screen coords."""
    sx = x3d + z3d * _3D_DEPTH * math.cos(_3D_ANGLE)
    sy = y3d - z3d * _3D_DEPTH * math.sin(_3D_ANGLE)
    return sx, sy


def _depth_scale(z3d, z_max=350):
    """Returns (scale, opacity) based on depth."""
    t = z3d / z_max
    scale = 1.0 - 0.30 * t
    opacity = 1.0 - 0.45 * t
    return scale, opacity


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
  .llm-stream {
    clip-path: inset(0 100% 0 0);
    animation: llmReveal 500ms cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
  }
  @keyframes llmReveal { to { clip-path: inset(0 0 0 0); } }
  .aal-gather {
    opacity: 0;
    transform: translate(var(--aal-dx, 0px), var(--aal-dy, 0px));
    transform-box: view-box;
    animation: aalGather 2800ms cubic-bezier(0.22, 0.75, 0.2, 1) forwards;
  }
  @keyframes aalGather {
    0%   { opacity: 0; transform: translate(var(--aal-dx, 0px), var(--aal-dy, 0px)); }
    8%   { opacity: 1; transform: translate(var(--aal-dx, 0px), var(--aal-dy, 0px)); }
    38%  { opacity: 1; transform: translate(var(--aal-dx, 0px), var(--aal-dy, 0px)); }
    100% { opacity: 1; transform: translate(0px, 0px); }
  }
  text { fill: #F1F5F9; }
]]></style>
<linearGradient id="bridgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%"   stop-color="#F97316"/>
  <stop offset="50%"  stop-color="#F59E0B"/>
  <stop offset="100%" stop-color="#3B82F6"/>
</linearGradient>
<linearGradient id="bodyBridgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%"   stop-color="#F97316" stop-opacity="0.06"/>
  <stop offset="30%"  stop-color="#06B6D4" stop-opacity="0.04"/>
  <stop offset="70%"  stop-color="#06B6D4" stop-opacity="0.04"/>
  <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.06"/>
</linearGradient>
<radialGradient id="spotFadeEmotion" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<radialGradient id="spotFadeBody" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<radialGradient id="spotFadeMedical" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<mask id="aalSpotlight" maskUnits="userSpaceOnUse" x="0" y="0" width="1500" height="880">
  <rect x="0" y="0" width="1500" height="880" fill="white"/>
  <circle cx="240"  cy="350" r="340" fill="url(#spotFadeEmotion)"/>
  <circle cx="700"  cy="300" r="360" fill="url(#spotFadeBody)"/>
  <circle cx="1210" cy="340" r="340" fill="url(#spotFadeMedical)"/>
</mask>
<mask id="aalSpotlight6" maskUnits="userSpaceOnUse" x="0" y="0" width="1500" height="880">
  <rect x="0" y="0" width="1500" height="880" fill="white"/>
  <circle cx="240"  cy="320" r="290" fill="url(#spotFadeEmotion)"/>
  <circle cx="700"  cy="290" r="310" fill="url(#spotFadeBody)"/>
  <circle cx="1210" cy="320" r="290" fill="url(#spotFadeMedical)"/>
  <circle cx="350"  cy="670" r="290" fill="url(#spotFadeAiEmp)"/>
  <circle cx="760"  cy="670" r="290" fill="url(#spotFadeAiClin)"/>
  <circle cx="1170" cy="670" r="290" fill="url(#spotFadeAiHedge)"/>
</mask>
<radialGradient id="spotFadeAiEmp" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<radialGradient id="spotFadeAiClin" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<radialGradient id="spotFadeAiHedge" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="black"/>
  <stop offset="100%" stop-color="white"/>
</radialGradient>
<radialGradient id="glowAiEmp" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#A78BFA" stop-opacity="0.18"/>
  <stop offset="60%"  stop-color="#A78BFA" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#A78BFA" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowAiClin" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#34D399" stop-opacity="0.16"/>
  <stop offset="60%"  stop-color="#34D399" stop-opacity="0.04"/>
  <stop offset="100%" stop-color="#34D399" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowAiHedge" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#64748B" stop-opacity="0.18"/>
  <stop offset="60%"  stop-color="#64748B" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#64748B" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowEmotion" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#F97316" stop-opacity="0.18"/>
  <stop offset="60%"  stop-color="#F97316" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#F97316" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowBody" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#06B6D4" stop-opacity="0.16"/>
  <stop offset="60%"  stop-color="#06B6D4" stop-opacity="0.04"/>
  <stop offset="100%" stop-color="#06B6D4" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glowMedical" cx="50%" cy="50%" r="50%">
  <stop offset="0%"   stop-color="#3B82F6" stop-opacity="0.18"/>
  <stop offset="60%"  stop-color="#3B82F6" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#3B82F6" stop-opacity="0"/>
</radialGradient>
</defs>"""


EMBED_STEP_LABELS = [
    "sentence",
    "matrix",
    "vector space",
    "AI patterns",
    "bridge",
]

# Stage-level progress (top-level deck, 7 stages).
# Colors double as a mini legend tying each stage to its cluster hue.
_STAGE_COLORS = ["#94A3B8", "#06B6D4", "#06B6D4", "#06B6D4", "#F59E0B", "#A78BFA", "#F59E0B"]
_STAGE_LABELS = ["Input", "Sentence", "Matrix", "Vectors", "Bridge", "Compare", "Reflect"]


def stage_progress(current: int) -> str:
    """Segmented 7-stage progress bar shown in every presenter header."""
    out = ['<span class="aal-progress">']
    for i in range(7):
        if i < current:
            out.append(
                f'<span class="aal-progress-seg aal-seg-done" '
                f'style="background:{_STAGE_COLORS[i]}; opacity:0.55;"></span>'
            )
        elif i == current:
            out.append(
                f'<span class="aal-progress-seg aal-seg-active" '
                f'style="background:{_STAGE_COLORS[i]}; color:{_STAGE_COLORS[i]};"></span>'
            )
        else:
            out.append('<span class="aal-progress-seg"></span>')
    out.append('</span>')
    return "".join(out)


def _wrap_svg_stage(eyebrow: str, svg_inner: str, current_stage: int) -> str:
    """Wrap SVG content in the standard presenter-stage chrome."""
    return f"""
<div class="tedx-embed-wrapper" style="background:#06080C; width:100%; min-height: 88vh;">
  <div style="display:flex; justify-content:space-between; padding: 1.2em 2.5em 0.3em;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase;">
      {eyebrow}
    </div>
    <div>{stage_progress(current_stage)}</div>
  </div>
  <svg viewBox="0 0 1500 880" xmlns="http://www.w3.org/2000/svg"
       style="width:100%; height:auto; display:block;"
       font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif">
    {SVG_STYLE}
    {svg_inner}
  </svg>
</div>
"""


# ---------- main entry ----------

def render_embed_step(step: int) -> str:
    """Legacy 5-sub-step renderer. Still used by audience mode / tests.

    Presenter mode no longer calls this — it uses render_embed_vector_stage
    and render_bridge_stage directly.
    """
    step = max(0, min(4, int(step)))
    inner = [
        _step_0_sentence,
        _step_1_matrix,
        _step_2_grid,
        _step_3_patterns,
        _step_4_bridge,
    ][step]()
    label = EMBED_STEP_LABELS[step]
    return _wrap_svg_stage(
        eyebrow=f"Step 2 &middot; Embed &middot; {step + 1} / 5 &middot; {label}",
        svg_inner=inner,
        current_stage=1,
    )


def render_embed_sentence_stage() -> str:
    """Presenter stage 1 — the prompt broken into pieces."""
    return _wrap_svg_stage(
        eyebrow="Step 2 &middot; Embed &middot; sentence",
        svg_inner=_step_0_sentence(),
        current_stage=1,
    )


def render_embed_matrix_stage() -> str:
    """Presenter stage 2 — every word becomes numbers."""
    return _wrap_svg_stage(
        eyebrow="Step 3 &middot; Embed &middot; matrix",
        svg_inner=_step_1_matrix(),
        current_stage=2,
    )


def render_embed_vector_stage() -> str:
    """Presenter stage 3 — the vector space with clusters forming."""
    return _wrap_svg_stage(
        eyebrow="Step 4 &middot; Embed &middot; vector space",
        svg_inner=_step_2_grid(),
        current_stage=3,
    )


def render_bridge_stage() -> str:
    """Presenter stage 4 — AI patterns + bridge lines drawing."""
    return _wrap_svg_stage(
        eyebrow="Step 5 &middot; Bridge &middot; proximity becomes empathy",
        svg_inner=_step_4_bridge(),
        current_stage=4,
    )


# Per-step colors that double as a mini legend:
# 0 sentence=slate, 1 matrix=amber, 2 vector=body cyan, 3 patterns=ai purple, 4 bridge=amber
_STEP_COLORS = ["#94A3B8", "#F59E0B", "#06B6D4", "#A78BFA", "#F59E0B"]


def _dots(step: int) -> str:
    out = ['<span class="aal-progress">']
    for i in range(5):
        if i < step:
            out.append(
                f'<span class="aal-progress-seg aal-seg-done" '
                f'style="background:{_STEP_COLORS[i]}; opacity:0.55;"></span>'
            )
        elif i == step:
            out.append(
                f'<span class="aal-progress-seg aal-seg-active" '
                f'style="background:{_STEP_COLORS[i]}; color:{_STEP_COLORS[i]};"></span>'
            )
        else:
            out.append('<span class="aal-progress-seg"></span>')
    out.append('</span>')
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


# ---------- STEP 2: the 3D vector space ----------

# --- Narrative word positions for step 2 (module-level so helpers can derive exclusion zones) ---
_NARR_POS = {
    "scared":   (180,  220),
    "fear":     (280,  340),
    "panic":    (170,  440),
    "spiking":  (320,  500),
    "racing":   (500,  280),   # body, near emotion side
    "chest":    (620,  200),
    "heart":    (680,  380),
    "tight":    (760,  280),
    "blood":    (900,  380),   # body, near medical side
    "ER":       (1180, 220),
    "hospital": (1300, 340),
    "pressure": (1150, 470),
}

_LABEL_OFFSETS = {
    "scared":   (24, 7, "start"),     # right
    "fear":     (24, 7, "start"),     # right
    "panic":    (24, 7, "start"),     # right
    "spiking":  (24, 7, "start"),     # right
    "racing":   (24, 7, "start"),     # right
    "chest":    (18, 30, "start"),    # below-right
    "heart":    (24, 7, "start"),     # right
    "tight":    (-24, 7, "end"),      # left
    "blood":    (24, 7, "start"),     # right
    "ER":       (-24, 7, "end"),      # left (away from right edge)
    "hospital": (-24, 7, "end"),      # left
    "pressure": (-24, 7, "end"),      # left
}

_CLUSTER_ZONES = {
    "emotion": {"cx": 240, "cy": 350, "r": 220, "color": "#F97316"},
    "body":    {"cx": 700, "cy": 300, "r": 260, "color": "#06B6D4"},
    "medical": {"cx": 1210, "cy": 340, "r": 220, "color": "#3B82F6"},
}


def _compute_tint(sx, sy):
    """Return (color, intensity) for proximity to a cluster zone."""
    best_color = "#94A3B8"
    best_intensity = 0.0
    for zone in _CLUSTER_ZONES.values():
        dist = math.sqrt((sx - zone["cx"]) ** 2 + (sy - zone["cy"]) ** 2)
        if dist < zone["r"]:
            intensity = 1.0 - (dist / zone["r"])
            if intensity > best_intensity:
                best_intensity = intensity
                best_color = zone["color"]
    return best_color, best_intensity


# Background vocabulary — a representative slice of the words an LLM knows.
# Seeded positions so the layout is stable across reloads.
_BG_WORDS = [
    "the", "of", "and", "to", "in", "is", "you", "that", "it", "was",
    "for", "on", "are", "with", "as", "at", "be", "this", "have", "from",
    "or", "one", "had", "by", "but", "not", "what", "all", "were", "we",
    "when", "your", "can", "said", "there", "each", "which", "do", "how", "if",
    "water", "oil", "call", "first", "who", "may", "down", "side", "been", "now",
    "find", "long", "day", "did", "get", "come", "made", "after", "back", "only",
    "think", "also", "just", "know", "take", "people", "into", "year", "them", "some",
    "time", "very", "thing", "her", "two", "way", "about", "many", "then", "would",
    "write", "like", "so", "these", "could", "other", "look", "has", "more", "go",
    "see", "number", "no", "make", "than", "my", "over", "such", "new", "sound",
    "dog", "cat", "tree", "sun", "moon", "star", "rain", "snow", "wind", "fire",
    "book", "read", "song", "play", "run", "walk", "talk", "sing", "jump", "eat",
    "happy", "sad", "love", "hate", "hope", "wish", "dream", "sleep", "wake", "live",
    "color", "shape", "size", "light", "dark", "fast", "slow", "loud", "soft", "warm",
    "cold", "north", "south", "east", "west", "sky", "sea", "rock", "sand", "wave",
    "car", "road", "house", "door", "wall", "floor", "roof", "glass", "stone", "wood",
    "mother", "father", "child", "friend", "teacher", "doctor", "nurse", "king", "queen", "hero",
    "city", "town", "farm", "field", "river", "lake", "hill", "mountain", "forest", "garden",
    "food", "bread", "milk", "rice", "meat", "fish", "fruit", "salt", "sugar", "spice",
    "music", "dance", "paint", "draw", "build", "break", "grow", "cut", "push", "pull",
    "red", "blue", "green", "yellow", "white", "black", "brown", "pink", "gray", "gold",
    "hand", "foot", "head", "eye", "ear", "nose", "mouth", "arm", "leg", "bone",
    "earth", "air", "land", "cloud", "storm", "ice", "dust", "mud", "grass", "leaf",
    "money", "work", "game", "test", "plan", "idea", "name", "word", "page", "line",
    "past", "future", "begin", "end", "open", "close", "true", "false", "right", "wrong",
    "anger", "joy", "trust", "doubt", "peace", "fight", "laugh", "cry", "smile", "frown",
    "power", "force", "energy", "speed", "weight", "space", "point", "edge", "center", "path",
    "system", "group", "world", "state", "school", "order", "part", "place", "case", "week",
    "company", "problem", "program", "question", "change", "move", "act", "try", "ask", "need",
    "home", "night", "story", "study", "still", "learn", "plant", "cover", "food", "turn",
]

import random as _random


def _decompose_ai_patterns():
    """Break each AI phrase into individual tokens scattered in the lower vector space.

    Tokens are spread inside their cluster spotlight zone with rejection-sampling
    collision avoidance so bold labels never overlap each other. Each token
    stores assembled_x/y — where it will slide to in Step 4.
    """
    rng = _random.Random(123)
    char_w = 8.5   # approx px per char at font-size 16
    word_gap = 10
    row_gap = 28   # min vertical center-to-center between tokens
    pad_x = 14     # min horizontal gap between token edges

    # Per-cluster placement zones — centered on the spotlight halos
    zones = {
        "ai_empathy":  (350,  700, 220, 80),
        "ai_clinical": (760,  700, 220, 80),
        "ai_hedge":    (1170, 700, 220, 80),
    }
    y_min, y_max = 630, 790

    by_cluster = {}
    for p in AI_PATTERNS:
        by_cluster.setdefault(p["cluster"], []).append(p)

    tokens = []
    for cluster, phrases in by_cluster.items():
        zcx, zcy, zx_half, zy_half = zones.get(cluster, (760, 700, 220, 80))

        for p in phrases:
            raw = p["text"].replace("\u201c", "").replace("\u201d", "").replace("\u2019", "\u2019")
            words = raw.split()
            widths = [len(w) * char_w for w in words]
            total = sum(widths) + (len(words) - 1) * word_gap
            cursor = p["x"] - total / 2

            for j, word in enumerate(words):
                assembled_x = cursor
                cursor += widths[j] + word_gap
                w = len(word) * char_w

                best = None
                for _ in range(150):
                    tx = zcx + rng.uniform(-zx_half, zx_half)
                    ty = zcy + rng.uniform(-zy_half, zy_half)
                    ty = max(y_min, min(y_max, ty))

                    collides = False
                    for t in tokens:
                        tw = len(t["word"]) * char_w
                        if (abs(tx - t["x"]) < (w + tw) / 2 + pad_x
                                and abs(ty - t["y"]) < row_gap):
                            collides = True
                            break
                    if not collides:
                        best = (tx, ty)
                        break
                if best is None:
                    best = (tx, ty)

                tokens.append({
                    "word": word,
                    "x": best[0],
                    "y": best[1],
                    "assembled_x": assembled_x,
                    "assembled_y": p["y"],
                    "color": p["color"],
                    "cluster": p["cluster"],
                    "phrase_text": p["text"],
                })
    return tokens


_AI_TOKENS = _decompose_ai_patterns()

# All exclusion zones: narrative words + decomposed AI tokens
_ALL_EXCL = list(_NARR_POS.values()) + [(t["x"], t["y"]) for t in _AI_TOKENS]


def _make_bg_field():
    """Generate 300 background word positions in 2D screen-space.

    These are spread across the full SVG viewbox so the visualization
    fills the entire viewport.  Positions near narrative words and AI
    tokens are rejected to prevent label overlap.
    """
    rng = _random.Random(42)
    excl_r = 55

    field = []
    for word in _BG_WORDS[:300]:
        for _ in range(12):
            sx = rng.randint(30, 1470)
            sy = rng.randint(150, 780)
            ok = all(
                math.sqrt((sx - ex) ** 2 + (sy - ey) ** 2) > excl_r
                for ex, ey in _ALL_EXCL
            )
            if ok:
                break
        tint_color, tint_intensity = _compute_tint(sx, sy)
        field.append({
            "word": word,
            "sx": sx,
            "sy": sy,
            "depth": rng.uniform(0.0, 1.0),
            "tint_color": tint_color,
            "tint_intensity": tint_intensity,
        })
    return field


_BG_FIELD = _make_bg_field()


def _make_particle_cloud():
    """Generate 1200 unnamed dots across the full 2D viewbox.

    These are the 'stars' that convey the vastness of the embedding space.
    A real model has 150k+ tokens — these dots hint at that scale.
    Particles near narrative words are dimmed so labels stay readable.
    """
    rng = _random.Random(99)
    _excl = list(_NARR_POS.values())
    excl_r = 45

    particles = []
    for _ in range(1200):
        sx = rng.randint(10, 1490)
        sy = rng.randint(10, 870)
        near_narr = any(
            math.sqrt((sx - ex) ** 2 + (sy - ey) ** 2) < excl_r
            for ex, ey in _excl
        )
        tint_color, tint_intensity = _compute_tint(sx, sy)
        particles.append({
            "sx": sx,
            "sy": sy,
            "size": rng.uniform(0.8, 4.0),
            "depth": rng.uniform(0.0, 1.0),
            "dimmed": near_narr,
            "tint_color": tint_color,
            "tint_intensity": tint_intensity,
        })
    return particles


_PARTICLE_CLOUD = _make_particle_cloud()


def _make_connection_web():
    """Pre-compute ~120 faint lines between nearby points.

    Creates a constellation / neural-web texture.  Only connects points
    that are 25–100 px apart in screen space.
    """
    rng = _random.Random(77)
    # Combine a sample of particles + background words
    all_pts = []
    for bg in _BG_FIELD:
        all_pts.append((bg["sx"], bg["sy"], bg["depth"]))
    for p in _PARTICLE_CLOUD[:400]:  # sample for perf
        all_pts.append((p["sx"], p["sy"], p["depth"]))

    lines = []
    for _ in range(4000):
        if len(lines) >= 120:
            break
        i = rng.randint(0, len(all_pts) - 1)
        j = rng.randint(0, len(all_pts) - 1)
        if i == j:
            continue
        ax, ay, ad = all_pts[i]
        bx, by, bd = all_pts[j]
        dist = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
        if 25 < dist < 100:
            avg_d = (ad + bd) / 2
            op = 0.06 + (1.0 - avg_d) * 0.12  # closer = brighter
            mid_x = (ax + bx) / 2
            mid_y = (ay + by) / 2
            tint_color, _ = _compute_tint(mid_x, mid_y)
            lines.append((ax, ay, bx, by, op, tint_color))
    return lines


_CONNECTION_WEB = _make_connection_web()


_WORD_SIZE = 16  # uniform font size for ALL words in the vector space

# --- Connection network ---
# Nearest-neighbor lines within each cluster
_NEIGHBOR_LINES = [
    # emotion
    ("scared", "fear"),
    ("fear", "panic"),
    ("panic", "spiking"),
    ("scared", "panic"),
    # body
    ("chest", "tight"),
    ("chest", "heart"),
    ("heart", "racing"),
    ("tight", "blood"),
    ("racing", "blood"),
    # medical
    ("ER", "hospital"),
    ("hospital", "pressure"),
    ("ER", "pressure"),
]

# Cross-cluster bridges (body is the semantic bridge between emotion and medical)
_BRIDGE_LINES = [
    ("spiking", "racing"),   # emotion → body (arousal crosses into physiology)
    ("scared", "chest"),     # emotion → body (fear manifests as chest tightness)
    ("blood", "pressure"),   # body → medical (symptom becomes a measurement)
    ("heart", "ER"),         # body → medical (racing heart brings you to the ER)
]


def _line_color(w1_cluster, w2_cluster):
    """Pick line color: cluster color for intra, amber for cross-cluster."""
    if w1_cluster == w2_cluster:
        return CLUSTERS.get(w1_cluster, {}).get("color", "#64748B")
    return "#F59E0B"


def _step_2_grid() -> str:
    out = []
    _halo = 'paint-order="stroke" stroke="#06080C" stroke-width="5"'

    # --- build word lookup ---
    all_words = list(USER_WORDS) + list(EXTRA_WORDS)
    word_map = {w["word"]: w for w in all_words}

    # --- Tagline ---
    out.append(
        '<text x="750" y="38" text-anchor="middle" font-size="32" fill="#F1F5F9" '
        'class="fade-in">Those numbers become coordinates.</text>'
    )
    out.append(
        '<text x="750" y="66" text-anchor="middle" font-size="20" fill="#64748B" '
        'font-style="italic" class="fade-in" style="animation-delay:400ms">'
        "Each word lands somewhere in a space of thousands of dimensions.</text>"
    )

    # === Layer 1: Particle cloud ===
    for p in _PARTICLE_CLOUD:
        brightness = 1.0 - p["depth"]
        r = p["size"] * (0.6 + brightness * 0.4)
        op = 0.04 + brightness * 0.18
        if p.get("dimmed"):
            op *= 0.3
        out.append(
            f'<circle cx="{p["sx"]}" cy="{p["sy"]}" r="{r:.1f}" '
            f'fill="#64748B" opacity="{op:.2f}"/>'
        )

    # === Layer 2: Background connection web ===
    for ax, ay, bx, by, op, _ in _CONNECTION_WEB:
        out.append(
            f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" '
            f'stroke="#334155" stroke-width="0.7" opacity="{op:.2f}"/>'
        )

    # === Layer 3: Intra-cluster neighbor lines (cluster-colored) ===
    for i, (a, b) in enumerate(_NEIGHBOR_LINES):
        pa, pb = _NARR_POS.get(a), _NARR_POS.get(b)
        wa, wb = word_map.get(a), word_map.get(b)
        if not (pa and pb and wa and wb):
            continue
        color = _line_color(wa["cluster"], wb["cluster"])
        delay = 1800 + i * 80
        out.append(
            f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" '
            f'stroke="{color}" stroke-width="1.5" opacity="0.45" '
            f'class="draw-line" style="animation-delay:{delay}ms"/>'
        )

    # === Layer 4: Cross-cluster bridge lines (amber, dashed) ===
    for i, (a, b) in enumerate(_BRIDGE_LINES):
        pa, pb = _NARR_POS.get(a), _NARR_POS.get(b)
        wa, wb = word_map.get(a), word_map.get(b)
        if not (pa and pb and wa and wb):
            continue
        delay = 2600 + i * 200
        out.append(
            f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" '
            f'stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6" '
            f'opacity="0.6" class="draw-line" style="animation-delay:{delay}ms"/>'
        )

    # === Layer 5: Background words — uniform gray ===
    for bg in _BG_FIELD:
        brightness = 1.0 - bg["depth"]
        op = 0.10 + brightness * 0.14
        out.append(
            f'<text x="{bg["sx"]}" y="{bg["sy"]}" font-size="{_WORD_SIZE}" '
            f'fill="#94A3B8" opacity="{op:.2f}" {_halo}>'
            f'{_html.escape(bg["word"])}</text>'
        )

    # === Layer 5b: Radial spotlight — dim the field everywhere except cluster zones ===
    out.append(
        '<rect x="0" y="0" width="1500" height="880" fill="#06080C" '
        'opacity="0.68" mask="url(#aalSpotlight)" class="fade-in" '
        'style="animation-delay:500ms"/>'
    )
    # Cluster color halos — re-light the zones with their own hues
    out.append(
        '<ellipse cx="240"  cy="350" rx="300" ry="220" fill="url(#glowEmotion)" '
        'class="fade-in" style="animation-delay:700ms"/>'
    )
    out.append(
        '<ellipse cx="700"  cy="300" rx="320" ry="230" fill="url(#glowBody)" '
        'class="fade-in" style="animation-delay:850ms"/>'
    )
    out.append(
        '<ellipse cx="1210" cy="340" rx="300" ry="220" fill="url(#glowMedical)" '
        'class="fade-in" style="animation-delay:1000ms"/>'
    )

    # === Layer 6: Narrative words in gray first (part of the field) ===
    for w in all_words:
        pos = _NARR_POS.get(w["word"])
        if not pos:
            continue
        out.append(
            f'<text x="{pos[0]}" y="{pos[1]}" font-size="{_WORD_SIZE}" '
            f'fill="#94A3B8" opacity="0.22" {_halo}>'
            f'{_html.escape(w["word"])}</text>'
        )

    # === Layer 7: Narrative words light up — bold + cluster color (fade in) ===
    for i, w in enumerate(all_words):
        pos = _NARR_POS.get(w["word"])
        if not pos:
            continue
        delay = 800 + i * 100
        out.append(
            f'<text x="{pos[0]}" y="{pos[1]}" font-size="{_WORD_SIZE}" '
            f'fill="{w["color"]}" font-weight="700" {_halo} '
            f'class="fade-in" style="animation-delay:{delay}ms">'
            f'{_html.escape(w["word"])}</text>'
        )

    # === Layer 8: Cluster labels ===
    from collections import defaultdict
    cluster_words = defaultdict(list)
    for w in all_words:
        cluster_words[w["cluster"]].append(w)

    for cname, c in CLUSTERS.items():
        ws = cluster_words.get(cname, [])
        positions = [_NARR_POS[w["word"]] for w in ws if w["word"] in _NARR_POS]
        if not positions:
            continue
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        max_dist = max(math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2) for p in positions)
        label_y = max(140, cy - max_dist - 18)
        out.append(
            f'<text x="{cx:.0f}" y="{label_y:.0f}" text-anchor="middle" '
            f'font-size="20" fill="{c["color"]}" font-style="italic" '
            f'opacity="0.6" {_halo} class="fade-in" style="animation-delay:2000ms">'
            f'{c["label"]}</text>'
        )

    # === Layer 9: Bridge annotation ===
    out.append(
        '<text x="750" y="700" text-anchor="middle" font-size="26" '
        f'fill="#F59E0B" font-weight="700" {_halo} '
        'class="fade-in" style="animation-delay:3400ms">'
        'Your body is the semantic bridge between fear and medicine.</text>'
    )
    out.append(
        '<text x="750" y="740" text-anchor="middle" font-size="22" fill="#64748B" '
        f'{_halo} class="fade-in" style="animation-delay:3800ms">'
        "12 words. 3 clusters. The AI sees connections, not feelings.</text>"
    )

    # === Axis labels ===
    out.append(
        '<text x="1460" y="870" text-anchor="end" font-size="16" fill="#475569" '
        'class="fade-in">dimension 1 of thousands</text>'
    )
    out.append(
        '<text x="30" y="870" font-size="16" fill="#475569" '
        'class="fade-in">dimension 2</text>'
    )
    return "".join(out)


# ---------- shared base layer for steps 2-4 ----------

def _render_base_field(out, user_word_opacity=1.0, show_connections=True,
                       connection_opacity=1.0):
    """Render the shared vector space: particles, web, bg words, user words.

    Reused by steps 2, 3, and 4 so the vector space is visually continuous.
    """
    _halo = 'paint-order="stroke" stroke="#06080C" stroke-width="5"'
    all_words = list(USER_WORDS) + list(EXTRA_WORDS)
    word_map = {w["word"]: w for w in all_words}

    # Particle cloud
    for p in _PARTICLE_CLOUD:
        brightness = 1.0 - p["depth"]
        r = p["size"] * (0.6 + brightness * 0.4)
        op = 0.04 + brightness * 0.18
        if p.get("dimmed"):
            op *= 0.3
        out.append(
            f'<circle cx="{p["sx"]}" cy="{p["sy"]}" r="{r:.1f}" '
            f'fill="#64748B" opacity="{op:.2f}"/>'
        )

    # Background connection web
    for ax, ay, bx, by, op, _ in _CONNECTION_WEB:
        out.append(
            f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" '
            f'stroke="#334155" stroke-width="0.7" opacity="{op:.2f}"/>'
        )

    # Intra-cluster + cross-cluster connection lines
    if show_connections:
        for i, (a, b) in enumerate(_NEIGHBOR_LINES):
            pa, pb = _NARR_POS.get(a), _NARR_POS.get(b)
            wa, wb = word_map.get(a), word_map.get(b)
            if not (pa and pb and wa and wb):
                continue
            color = _line_color(wa["cluster"], wb["cluster"])
            op = 0.45 * connection_opacity
            out.append(
                f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" '
                f'stroke="{color}" stroke-width="1.5" opacity="{op:.2f}"/>'
            )
        for i, (a, b) in enumerate(_BRIDGE_LINES):
            pa, pb = _NARR_POS.get(a), _NARR_POS.get(b)
            if not (pa and pb):
                continue
            op = 0.6 * connection_opacity
            out.append(
                f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" '
                f'stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6" '
                f'opacity="{op:.2f}"/>'
            )

    # Background words
    for bg in _BG_FIELD:
        brightness = 1.0 - bg["depth"]
        op = 0.10 + brightness * 0.14
        out.append(
            f'<text x="{bg["sx"]}" y="{bg["sy"]}" font-size="{_WORD_SIZE}" '
            f'fill="#94A3B8" opacity="{op:.2f}" {_halo}>'
            f'{_html.escape(bg["word"])}</text>'
        )

    # Narrative words — bold + cluster color
    for w in all_words:
        pos = _NARR_POS.get(w["word"])
        if not pos:
            continue
        op = user_word_opacity
        out.append(
            f'<text x="{pos[0]}" y="{pos[1]}" font-size="{_WORD_SIZE}" '
            f'fill="{w["color"]}" font-weight="700" opacity="{op}" {_halo}>'
            f'{_html.escape(w["word"])}</text>'
        )

    # Cluster labels
    from collections import defaultdict
    cluster_words = defaultdict(list)
    for w in all_words:
        cluster_words[w["cluster"]].append(w)
    for cname, c in CLUSTERS.items():
        ws = cluster_words.get(cname, [])
        positions = [_NARR_POS[w["word"]] for w in ws if w["word"] in _NARR_POS]
        if not positions:
            continue
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        max_dist = max(math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2) for p in positions)
        label_y = max(140, cy - max_dist - 18)
        out.append(
            f'<text x="{cx:.0f}" y="{label_y:.0f}" text-anchor="middle" '
            f'font-size="20" fill="{c["color"]}" font-style="italic" '
            f'opacity="0.45" {_halo}>{c["label"]}</text>'
        )


# ---------- STEP 3: the AI's patterns ----------

def _step_3_patterns() -> str:
    _halo = 'paint-order="stroke" stroke="#06080C" stroke-width="5"'
    out = []

    # Header
    out.append(
        '<text x="750" y="38" text-anchor="middle" font-size="32" fill="#F1F5F9" '
        'class="fade-in">What the AI already knows.</text>'
    )
    out.append(
        '<text x="750" y="66" text-anchor="middle" font-size="20" fill="#64748B" '
        'font-style="italic" class="fade-in" style="animation-delay:400ms">'
        "Patterns learned from therapy transcripts, medical texts, and crisis counseling.</text>"
    )

    # Same vector space as step 2, user words slightly dimmed
    _render_base_field(out, user_word_opacity=0.55, show_connections=True,
                       connection_opacity=0.4)

    # Spotlight — dim field everywhere except the 6 cluster zones.
    out.append(
        '<rect x="0" y="0" width="1500" height="880" fill="#06080C" '
        'opacity="0.74" mask="url(#aalSpotlight6)" class="fade-in" '
        'style="animation-delay:500ms"/>'
    )
    # User-cluster halos (top)
    out.append(
        '<ellipse cx="240"  cy="320" rx="280" ry="200" fill="url(#glowEmotion)" '
        'class="fade-in" style="animation-delay:700ms"/>'
    )
    out.append(
        '<ellipse cx="700"  cy="290" rx="300" ry="210" fill="url(#glowBody)" '
        'class="fade-in" style="animation-delay:800ms"/>'
    )
    out.append(
        '<ellipse cx="1210" cy="320" rx="280" ry="200" fill="url(#glowMedical)" '
        'class="fade-in" style="animation-delay:900ms"/>'
    )
    # AI-cluster halos (bottom)
    out.append(
        '<ellipse cx="350"  cy="670" rx="280" ry="200" fill="url(#glowAiEmp)" '
        'class="fade-in" style="animation-delay:1000ms"/>'
    )
    out.append(
        '<ellipse cx="760"  cy="670" rx="280" ry="200" fill="url(#glowAiClin)" '
        'class="fade-in" style="animation-delay:1100ms"/>'
    )
    out.append(
        '<ellipse cx="1170" cy="670" rx="280" ry="200" fill="url(#glowAiHedge)" '
        'class="fade-in" style="animation-delay:1200ms"/>'
    )

    # Divider — subtle line + centered frosted pill overlay
    out.append(
        '<line x1="60" y1="580" x2="1440" y2="580" stroke="#475569" stroke-width="1" '
        'stroke-dasharray="14,14" opacity="0.35" class="draw-line" '
        'style="animation-delay:600ms"/>'
    )
    # Frosted pill — opaque so it reads cleanly above any residual bg text
    out.append(
        '<rect x="520" y="558" width="460" height="44" rx="22" '
        'fill="#0C1018" opacity="0.98" stroke="#334155" stroke-width="1" '
        'class="fade-in" style="animation-delay:700ms"/>'
    )
    out.append(
        '<text x="660" y="585" text-anchor="end" font-size="14" fill="#64748B" '
        'font-weight="500" letter-spacing="0.08em" '
        'class="fade-in" style="animation-delay:900ms">'
        '&#8593; your words</text>'
    )
    out.append(
        '<circle cx="690" cy="580" r="2" fill="#475569" '
        'class="fade-in" style="animation-delay:900ms"/>'
    )
    out.append(
        '<text x="720" y="585" font-size="14" fill="#A78BFA" '
        'font-weight="500" letter-spacing="0.08em" '
        'class="fade-in" style="animation-delay:900ms">'
        "AI training data &#8595;</text>"
    )

    # Decomposed AI tokens — individual words scattered in the lower vector space.
    # They look like any other vocabulary entries, just highlighted in cluster color.
    for i, t in enumerate(_AI_TOKENS):
        delay = 1000 + i * 80
        out.append(
            f'<text x="{t["x"]:.0f}" y="{t["y"]:.0f}" font-size="{_WORD_SIZE}" '
            f'fill="{t["color"]}" font-weight="700" {_halo} '
            f'class="fade-in" style="animation-delay:{delay}ms">'
            f'{_html.escape(t["word"])}</text>'
        )

    # AI cluster labels
    for i, (name, c) in enumerate(AI_CLUSTERS.items()):
        delay = 2800 + i * 200
        out.append(
            f'<text x="{c["cx"]}" y="{c["cy"] + c["r"] + 24}" text-anchor="middle" '
            f'font-size="18" fill="{c["color"]}" font-style="italic" opacity="0.5" '
            f'{_halo} class="fade-in" style="animation-delay:{delay}ms">'
            f'{c["label"]}</text>'
        )

    # Axis labels
    out.append(
        '<text x="1460" y="870" text-anchor="end" font-size="16" fill="#475569">'
        'dimension 1 of thousands</text>'
    )
    out.append(
        '<text x="30" y="870" font-size="16" fill="#475569">'
        'dimension 2</text>'
    )
    return "".join(out)


# ---------- STEP 4: the bridge ----------

def _step_4_bridge() -> str:
    _halo = 'paint-order="stroke" stroke="#06080C" stroke-width="5"'
    out = []

    # Header
    out.append(
        '<text x="750" y="38" text-anchor="middle" font-size="32" fill="#F1F5F9" '
        'class="fade-in">Proximity becomes empathy.</text>'
    )

    # Full vector space — user words at full brightness
    _render_base_field(out, user_word_opacity=0.85, show_connections=True,
                       connection_opacity=0.25)

    # Spotlight — same 6-zone dim as step 3 so the layout stays continuous.
    out.append(
        '<rect x="0" y="0" width="1500" height="880" fill="#06080C" '
        'opacity="0.74" mask="url(#aalSpotlight6)"/>'
    )
    for cx, cy, grad in (
        (240, 320, "glowEmotion"), (700, 290, "glowBody"), (1210, 320, "glowMedical"),
        (350, 670, "glowAiEmp"), (760, 670, "glowAiClin"), (1170, 670, "glowAiHedge"),
    ):
        out.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="280" ry="200" fill="url(#{grad})"/>'
        )

    # Divider (persistent from step 3, dimmed)
    out.append(
        '<line x1="60" y1="580" x2="1440" y2="580" stroke="#475569" stroke-width="1" '
        'stroke-dasharray="14,14" opacity="0.2"/>'
    )

    # Decomposed tokens slide from scattered → assembled via CSS transform.
    # Rendered at the assembled coordinates with a starting --aal-dx/dy offset
    # that the keyframe animates back to (0,0). Fires reliably on every SVG
    # re-mount, unlike SMIL.
    for i, t in enumerate(_AI_TOKENS):
        delay_ms = 450 + i * 45
        dx = t["x"] - t["assembled_x"]
        dy = t["y"] - t["assembled_y"]
        out.append(
            f'<text class="aal-gather" x="{t["assembled_x"]:.0f}" y="{t["assembled_y"]}" '
            f'font-size="{_WORD_SIZE}" fill="{t["color"]}" font-weight="700" {_halo} '
            f'style="--aal-dx:{dx:.0f}px; --aal-dy:{dy:.0f}px; animation-delay:{delay_ms}ms;">'
            f'{_html.escape(t["word"])}</text>'
        )

    # Bridge lines — draw after tokens finish gathering.
    # Gather keyframe runs 2800ms; last token starts at ~1170ms
    # (450 + 16*45), so last gather completes ~3970ms. Start the
    # bridge reveal at 4100ms so the audience sees the phrases
    # settle first.
    pat_by_text = {p["text"]: p for p in AI_PATTERNS}
    for i, (word, pat_text) in enumerate(BRIDGES):
        pos = _NARR_POS.get(word)
        p = pat_by_text.get(pat_text)
        if pos and p:
            delay = 4100 + i * 280
            out.append(
                f'<line x1="{pos[0]}" y1="{pos[1]}" x2="{p["x"]}" y2="{p["y"]}" '
                f'stroke="#F59E0B" stroke-width="2.5" stroke-dasharray="10,8" '
                f'opacity="0.75" class="draw-line" style="animation-delay:{delay}ms"/>'
            )

    # Punchline
    out.append(
        f'<text x="750" y="835" text-anchor="middle" font-size="36" font-weight="700" '
        f'fill="#F59E0B" {_halo} class="slow-fade" style="animation-delay:6200ms">'
        "The empathy you feel is proximity &mdash; not comprehension.</text>"
    )

    # Axis labels
    out.append(
        '<text x="1460" y="870" text-anchor="end" font-size="16" fill="#475569">'
        'dimension 1 of thousands</text>'
    )
    out.append(
        '<text x="30" y="870" font-size="16" fill="#475569">'
        'dimension 2</text>'
    )
    return "".join(out)


# ---------- audience-mode embed viz (LLM-generated data) ----------

def render_audience_embed(prompt: str, embeddings: dict) -> str:
    """Render the audience-mode embed with a 3-phase animated progression.

    Phase A (0-2s): Sentence breaks into individual words
    Phase B (2-4s): Vector numbers flash next to each word
    Phase C (4-7s): Words fly to cluster positions on the scatter plot
    """
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
        raw = float(w.get("y", 0.35))
        return 130 + max(0.0, min(1.0, (raw - 0.1) / 0.6)) * 430

    # Phase A: words laid out in a sentence-like grid, then scatter
    word_start_positions = []
    cols = min(6, max(3, len(words)))
    for i, w in enumerate(words):
        sx = 200 + (i % cols) * 200
        sy = 200 + (i // cols) * 70
        word_start_positions.append((sx, sy))

    # Build per-word CSS keyframes
    word_keyframes = []
    for i, w in enumerate(words):
        sx, sy = word_start_positions[i]
        ex, ey = _nx(w), _ny(w)
        word_keyframes.append(f"""
        @keyframes aalWordFly{i} {{
          0%   {{ transform: translate({sx}px, {sy}px); opacity: 0; }}
          15%  {{ transform: translate({sx}px, {sy}px); opacity: 1; }}
          55%  {{ transform: translate({sx}px, {sy}px); opacity: 1; }}
          100% {{ transform: translate({ex:.0f}px, {ey:.0f}px); opacity: 1; }}
        }}
        @keyframes aalVecFlash{i} {{
          0%, 35%  {{ opacity: 0; }}
          40%      {{ opacity: 0.9; }}
          55%      {{ opacity: 0.9; }}
          60%, 100% {{ opacity: 0; }}
        }}
        """)

    parts = [f"""
<div class="aal-audience-embed-wrap">
  <div class="aal-audience-embed-header">
    <div class="aal-audience-embed-eyebrow">Step 2 &middot; Embed</div>
    <div class="aal-audience-embed-prompt">&ldquo;{_html.escape(prompt)}&rdquo;</div>
  </div>

  <div class="aal-audience-embed-phases">
    <div class="aal-phase-label aal-phase-a">The AI breaks your sentence into pieces&hellip;</div>
    <div class="aal-phase-label aal-phase-b">Each word becomes a vector of numbers&hellip;</div>
    <div class="aal-phase-label aal-phase-c">Similar meanings land near each other in space.</div>
  </div>

  <svg viewBox="0 0 1500 700" xmlns="http://www.w3.org/2000/svg"
       class="aal-audience-embed-svg"
       font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif">
    {SVG_STYLE}
"""]

    # Grid background (appears in phase C)
    grid_parts = []
    for gy in range(120, 601, 60):
        grid_parts.append(f'<line x1="100" y1="{gy}" x2="1400" y2="{gy}" stroke="#101827" stroke-width="1"/>')
    for gx in range(100, 1401, 100):
        grid_parts.append(f'<line x1="{gx}" y1="120" x2="{gx}" y2="600" stroke="#101827" stroke-width="1"/>')
    grid_parts.append('<line x1="100" y1="600" x2="1400" y2="600" stroke="#475569" stroke-width="2"/>')
    grid_parts.append('<line x1="100" y1="120" x2="100" y2="600" stroke="#475569" stroke-width="2"/>')
    grid_parts.append('<text x="750" y="640" text-anchor="middle" font-size="18" fill="#64748B">dimension 1 (of thousands)</text>')
    parts.append(f'<g class="aal-embed-grid">{"".join(grid_parts)}</g>')

    # Cluster halos (appear in phase C)
    for name, ws in groups.items():
        if len(ws) < 2:
            continue
        cx = sum(_nx(w) for w in ws) / len(ws)
        cy = sum(_ny(w) for w in ws) / len(ws)
        color = color_map[name]
        parts.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="130" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-dasharray="8,8" opacity="0" '
            f'class="aal-embed-halo"/>'
        )
        parts.append(
            f'<text x="{cx:.0f}" y="{cy - 142:.0f}" text-anchor="middle" font-size="20" '
            f'fill="{color}" font-weight="700" opacity="0" class="aal-embed-halo-label">'
            f'{_html.escape(name)}</text>'
        )

    # Words — positioned at origin, animated via CSS keyframes
    for i, w in enumerate(words):
        color = color_map.get(str(w.get("cluster", "default")), "#F1F5F9")
        text = _html.escape(str(w.get("word", "")))
        ex, ey = _nx(w), _ny(w)
        # Vector snippet (shown during phase B)
        vec_x = round(float(w.get("x", 0.5)), 2)
        vec_y = round(float(w.get("y", 0.3)), 2)
        anim_delay = i * 120
        parts.append(f"""
        <g style="animation: aalWordFly{i} 6s ease-in-out {anim_delay}ms forwards;
                  transform: translate(0, 0); opacity: 0;">
          <circle r="9" fill="{color}"/>
          <text x="14" y="8" font-size="22" fill="{color}">{text}</text>
          <text x="14" y="26" font-size="13" fill="#475569" font-family="SF Mono, Menlo, monospace"
                style="animation: aalVecFlash{i} 6s ease-in-out {anim_delay}ms forwards; opacity:0;">
            [{vec_x:+.2f}, {vec_y:+.2f}, &hellip;]</text>
        </g>
        """)

    parts.append("</svg>")

    # Inject the per-word keyframes
    parts.append(f"<style>{''.join(word_keyframes)}")
    parts.append("""
    .aal-audience-embed-wrap {
        background: #06080C; width: 100%; min-height: 78vh; padding: 0.8em 0 2em;
        position: relative; overflow: hidden;
    }
    .aal-audience-embed-header {
        max-width: 980px; margin: 0.5em auto 0; padding: 0 2em;
    }
    .aal-audience-embed-eyebrow {
        color: #64748B; font-size: 0.95em; letter-spacing: 0.2em;
        text-transform: uppercase; margin-bottom: 0.5em;
    }
    .aal-audience-embed-prompt {
        color: #F1F5F9; font-size: 1.5em; font-style: italic; line-height: 1.45;
    }
    .aal-audience-embed-phases {
        max-width: 980px; margin: 0.7em auto 0; padding: 0 2em;
        height: 2em; position: relative;
    }
    .aal-phase-label {
        position: absolute; top: 0; left: 2em;
        color: #94A3B8; font-size: 1.05em; opacity: 0;
    }
    .aal-phase-a { animation: aalPhaseShow 6s ease-in-out forwards; }
    .aal-phase-b { animation: aalPhaseShow 6s ease-in-out 2s forwards; }
    .aal-phase-c { animation: aalPhaseShowStay 6s ease-in-out 3.5s forwards; }
    @keyframes aalPhaseShow {
        0%   { opacity: 0; transform: translateY(6px); }
        10%  { opacity: 1; transform: translateY(0); }
        40%  { opacity: 1; }
        55%  { opacity: 0; }
        100% { opacity: 0; }
    }
    @keyframes aalPhaseShowStay {
        0%   { opacity: 0; transform: translateY(6px); }
        15%  { opacity: 1; transform: translateY(0); }
        100% { opacity: 1; }
    }
    .aal-audience-embed-svg {
        width: 100%; height: auto; display: block;
    }
    .aal-embed-grid { opacity: 0; animation: aalFadeIn 1s ease-out 3.5s forwards; }
    .aal-embed-halo { animation: aalFadeIn 800ms ease-out 5s forwards; }
    .aal-embed-halo-label { animation: aalFadeIn 800ms ease-out 5.2s forwards; }
    @keyframes aalFadeIn { to { opacity: 1; } }
    </style>""")

    parts.append("</div>")
    return "".join(parts)
