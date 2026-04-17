"""Ask Anything Lab — TEDx presentation Gradio app.

Two modes from one URL:
    - Presenter: clicker-controlled stage demo with hardcoded data, zero API calls.
    - Audience:  prompt input, three parallel Claude calls, study data to Supabase.

Run locally: `python app.py`
"""
import html as _html
import os
import uuid

# Load .env before any service module reads os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gradio as gr

from data.demo import PROMPT, REFLECT_QUOTE, RESPONSE
from components.landing import LANDING_HTML
from components.embed_viz import (
    render_audience_embed,
    render_bridge_stage,
    render_embed_matrix_stage,
    render_embed_sentence_stage,
    render_embed_step,
    render_embed_vector_stage,
    stage_progress,
)
from components.source_list import render_sources
from components.typewriter import typewriter_html
from components.compare import render_compare_stage
from components.audience_compare import render_audience_compare
from components.influence import render_influence_analysis
from components.speaker import SPEAKER_HTML
from components.study import SURPRISING_OPTIONS, study_intro_html, thanks_html
from components import corpus_slideshow
from services.claude_api import get_influence_analysis, process_prompt_parallel
from services.supabase_client import fetch_aggregate_stats, save_influence, save_study


# ============================================================
# Presenter-mode stage rendering
# ============================================================

# Tight 5-stage presenter deck (TEDx format). Every click earns its moment:
#   0 Input     — chat-input typing of the prompt
#   1 Embed     — vector space with clusters forming
#   2 Bridge    — AI patterns gather + bridge lines draw
#   3 Compare   — cold vs warm empirical proof
#   4 Reflect   — closing quote
#
# Audience mode still uses the original 5-sub-step embed + retrieve +
# synthesize flow (self-paced, full experience). embed_step remains in
# state for audience-mode compatibility but presenter mode ignores it.
LAST_STAGE = 6
EMBED_SUBSTEPS = 5


def render_presenter_stage(stage: int, embed_step: int) -> str:
    if stage == 0:
        return _render_input_stage()
    if stage == 1:
        return render_embed_sentence_stage()
    if stage == 2:
        return render_embed_matrix_stage()
    if stage == 3:
        return render_embed_vector_stage()
    if stage == 4:
        return render_bridge_stage()
    if stage == 5:
        return render_compare_stage()
    if stage == 6:
        return _render_reflect_stage()
    return _render_input_stage()


def _render_input_stage() -> str:
    # Character-by-character reveal. Each char gets a staggered fade
    # so the sentence appears to be typed, ending with a blinking caret.
    per_char_ms = 32
    chars = []
    for i, ch in enumerate(PROMPT):
        delay = 700 + i * per_char_ms
        if ch == " ":
            chars.append(f'<span class="aal-typed" style="animation-delay:{delay}ms">&nbsp;</span>')
        else:
            chars.append(
                f'<span class="aal-typed" style="animation-delay:{delay}ms">{_html.escape(ch)}</span>'
            )
    typed_html = "".join(chars)
    caret_delay = 700 + len(PROMPT) * per_char_ms + 100
    footer_delay = caret_delay + 400
    return f"""
<div class="aal-input-stage">
  <div class="aal-input-topbar">
    <div class="aal-input-eyebrow">Step 1 &middot; Input</div>
    <div>{stage_progress(0)}</div>
  </div>
  <div class="aal-input-subtitle">Imagine you just typed this into ChatGPT.</div>
  <div class="aal-chat-input">
    <div class="aal-chat-label">
      <span class="aal-chat-label-dot"></span>
      Your prompt
    </div>
    <div class="aal-chat-text">&ldquo;{typed_html}&rdquo;<span class="aal-caret" style="animation-delay:{caret_delay}ms"></span></div>
  </div>
  <div class="aal-input-footer" style="--aal-footer-delay: {footer_delay}ms;">
    Press &rarr; to watch what happens next.
  </div>
</div>
"""


def _render_reflect_stage() -> str:
    return f"""
<div class="aal-reflect-wrap">
  <div class="aal-reflect-topbar">
    <div class="aal-reflect-eyebrow">Step 7 &middot; Reflect</div>
    <div>{stage_progress(6)}</div>
  </div>
  <div class="aal-reflect-body">
    <div class="aal-reflect-quote">
      &ldquo;{_html.escape(REFLECT_QUOTE)}&rdquo;
    </div>
    <div class="aal-reflect-attribution">&mdash; Ask Anything</div>
  </div>
</div>
"""


# ============================================================
# Presenter state machine
# ============================================================

def advance(stage: int, embed_step: int):
    if stage >= LAST_STAGE:
        return LAST_STAGE, 0
    return stage + 1, 0


def retreat(stage: int, embed_step: int):
    if stage <= 0:
        return 0, 0
    return stage - 1, 0


def on_forward(stage: int, embed_step: int):
    new_stage, new_step = advance(stage, embed_step)
    return new_stage, new_step, render_presenter_stage(new_stage, new_step)


def on_back(stage: int, embed_step: int):
    new_stage, new_step = retreat(stage, embed_step)
    return new_stage, new_step, render_presenter_stage(new_stage, new_step)


# ============================================================
# Mode switching
# ============================================================

# Shorthand for Gradio 6 visibility-cascade workaround. Every navigation
# function must set these classes explicitly or stale state from earlier
# screens (e.g. aal-force-show left on audience_viz_group after a submit)
# will keep that column displayed on top of whatever you navigate to next.
_SHOW = ["aal-force-show"]
_HIDE = ["aal-force-hide"]


def enter_presenter():
    return (
        gr.update(visible=False, elem_classes=_HIDE),   # landing_view
        gr.update(visible=True,  elem_classes=_SHOW),   # presenter_view
        gr.update(visible=False, elem_classes=_HIDE),   # audience_input_group
        gr.update(visible=False, elem_classes=_HIDE),   # audience_viz_group
        gr.update(visible=False, elem_classes=_HIDE),   # study_group
        gr.update(visible=False, elem_classes=_HIDE),   # thanks_group
        gr.update(visible=False, elem_classes=_HIDE),   # corpus_view
        gr.update(visible=False, elem_classes=_HIDE),   # speaker_view
        0, 0,                                            # stage, embed_step
        render_presenter_stage(0, 0),
    )


def enter_audience():
    return (
        gr.update(visible=False, elem_classes=_HIDE),   # landing_view
        gr.update(visible=False, elem_classes=_HIDE),   # presenter_view
        gr.update(visible=True,  elem_classes=_SHOW),   # audience_input_group
        gr.update(visible=False, elem_classes=_HIDE),   # audience_viz_group
        gr.update(visible=False, elem_classes=_HIDE),   # study_group
        gr.update(visible=False, elem_classes=_HIDE),   # thanks_group
        gr.update(visible=False, elem_classes=_HIDE),   # corpus_view
        gr.update(visible=False, elem_classes=_HIDE),   # speaker_view
        "",                                              # prompt_box reset
        0,                                               # audience_stage reset
    )


def enter_corpus():
    return (
        gr.update(visible=False, elem_classes=_HIDE),   # landing_view
        gr.update(visible=False, elem_classes=_HIDE),   # presenter_view
        gr.update(visible=False, elem_classes=_HIDE),   # audience_input_group
        gr.update(visible=False, elem_classes=_HIDE),   # audience_viz_group
        gr.update(visible=False, elem_classes=_HIDE),   # study_group
        gr.update(visible=False, elem_classes=_HIDE),   # thanks_group
        gr.update(visible=True,  elem_classes=_SHOW),   # corpus_view
        gr.update(visible=False, elem_classes=_HIDE),   # speaker_view
        0,                                               # corpus_idx reset
        corpus_slideshow.slide_html(0),                  # corpus_slide
    )


def enter_speaker():
    return (
        gr.update(visible=False, elem_classes=_HIDE),   # landing_view
        gr.update(visible=False, elem_classes=_HIDE),   # presenter_view
        gr.update(visible=False, elem_classes=_HIDE),   # audience_input_group
        gr.update(visible=False, elem_classes=_HIDE),   # audience_viz_group
        gr.update(visible=False, elem_classes=_HIDE),   # study_group
        gr.update(visible=False, elem_classes=_HIDE),   # thanks_group
        gr.update(visible=False, elem_classes=_HIDE),   # corpus_view
        gr.update(visible=True,  elem_classes=_SHOW),   # speaker_view
    )


def go_home():
    return (
        gr.update(visible=True,  elem_classes=_SHOW),   # landing_view
        gr.update(visible=False, elem_classes=_HIDE),   # presenter_view
        gr.update(visible=False, elem_classes=_HIDE),   # audience_input_group
        gr.update(visible=False, elem_classes=_HIDE),   # audience_viz_group
        gr.update(visible=False, elem_classes=_HIDE),   # study_group
        gr.update(visible=False, elem_classes=_HIDE),   # thanks_group
        gr.update(visible=False, elem_classes=_HIDE),   # corpus_view
        gr.update(visible=False, elem_classes=_HIDE),   # speaker_view
        0, 0,                                            # stage, embed_step
    )


# ============================================================
# Corpus slideshow handlers
# ============================================================

def on_corpus_forward(idx: int):
    new_idx = corpus_slideshow.advance(idx)
    return new_idx, corpus_slideshow.slide_html(new_idx)


def on_corpus_back(idx: int):
    new_idx = corpus_slideshow.retreat(idx)
    return new_idx, corpus_slideshow.slide_html(new_idx)


# ============================================================
# Audience-mode handlers
# ============================================================

def _loading_html(prompt: str = "") -> str:
    # Float up to 10 real tokens from the user's prompt so the thinking
    # screen feels grounded in what they typed.
    words = [w.strip(".,!?\u2019\u201c\u201d\"'") for w in (prompt or "").split() if len(w) > 2][:10]
    floaters = ""
    for i, w in enumerate(words):
        delay = i * 280
        left = 6 + (i * 9) % 86  # spread horizontally across the container
        floaters += (
            f'<span class="aal-think-token" '
            f'style="left:{left}%; animation-delay:{delay}ms;">'
            f'{_html.escape(w)}</span>'
        )
    return f"""
<div class="aal-think-wrap">
  <div class="aal-think-aurora">
    <div class="aal-think-blob aal-think-blob-a"></div>
    <div class="aal-think-blob aal-think-blob-b"></div>
    <div class="aal-think-blob aal-think-blob-c"></div>
  </div>

  <div class="aal-think-floaters">{floaters}</div>

  <div class="aal-think-center">
    <div class="aal-think-eyebrow">
      <span class="aal-think-eyebrow-dot"></span>
      Processing
    </div>
    <h2 class="aal-think-title">
      <span class="aal-think-cycle">
        <span>Embedding your words</span>
        <span>Retrieving nearby knowledge</span>
        <span>Synthesizing a response</span>
      </span>
    </h2>
    <div class="aal-think-sub">Three parallel API calls \u2014 hang on a few seconds.</div>

    <div class="aal-think-tasks">
      <div class="aal-think-task aal-task-embed">
        <div class="aal-think-task-dot"></div>
        <div class="aal-think-task-body">
          <div class="aal-think-task-title">Embed</div>
          <div class="aal-think-task-sub">words \u2192 vectors</div>
        </div>
        <div class="aal-think-shimmer"></div>
      </div>
      <div class="aal-think-task aal-task-retrieve">
        <div class="aal-think-task-dot"></div>
        <div class="aal-think-task-body">
          <div class="aal-think-task-title">Retrieve</div>
          <div class="aal-think-task-sub">nearby sources</div>
        </div>
        <div class="aal-think-shimmer"></div>
      </div>
      <div class="aal-think-task aal-task-synthesize">
        <div class="aal-think-task-dot"></div>
        <div class="aal-think-task-body">
          <div class="aal-think-task-title">Synthesize</div>
          <div class="aal-think-task-sub">stitch the answer</div>
        </div>
        <div class="aal-think-shimmer"></div>
      </div>
    </div>
  </div>
</div>
"""


def handle_audience_submit(prompt):
    """Generator: shows loading state, fires 3 parallel API calls, then renders embed viz."""
    if not prompt or not prompt.strip():
        yield (
            gr.update(),           # audience_input_group (no change)
            gr.update(),           # audience_viz_group   (no change)
            "",                    # audience_display
            0,                     # audience_stage
            "",                    # prompt_state
            {}, {}, "",            # embeddings/sources/response
            {},                    # influence_state
            "",                    # session_id
            gr.update(value="**Please enter a prompt first.**", visible=True),
        )
        return

    prompt = prompt.strip()
    session_id = str(uuid.uuid4())

    yield (
        gr.update(visible=False, elem_classes=["aal-force-hide"]),   # hide input
        gr.update(visible=True,  elem_classes=["aal-force-show"]),   # show viz
        _loading_html(prompt),
        0,
        prompt,
        {}, {}, "",
        {},
        session_id,
        gr.update(value="", visible=False),
    )

    embeddings, sources, response = process_prompt_parallel(prompt)

    yield (
        gr.update(visible=False, elem_classes=["aal-force-hide"]),
        gr.update(visible=True,  elem_classes=["aal-force-show"]),
        render_audience_embed(prompt, embeddings),
        1,
        prompt,
        embeddings, sources, response,
        {},
        session_id,
        gr.update(value="", visible=False),
    )


def handle_audience_continue(audience_stage, prompt, embeddings, sources, response,
                             influence_data, session_id):
    """Advance through audience stages:
    1=embed → 2=retrieve → 3=synthesize → 4=influence → 5=study → 6=compare → 7=thanks
    """
    # Returns: (audience_viz_group, study_group, thanks_group,
    #           audience_display, audience_stage, influence_state)
    print(f"[audience] continue: stage={audience_stage!r}", flush=True)
    _no = gr.update()

    if audience_stage == 1:
        srcs = (sources or {}).get("sources") if isinstance(sources, dict) else None
        return (
            gr.update(visible=True), _no, _no,
            render_sources(srcs, embeddings=embeddings, label="Step 3 \u00b7 Retrieve"),
            2, influence_data,
        )

    if audience_stage == 2:
        return (
            gr.update(visible=True), _no, _no,
            typewriter_html(response or "(no response)"),
            3, influence_data,
        )

    if audience_stage == 3:
        inf = get_influence_analysis(prompt, response or "")
        return (
            gr.update(visible=True), _no, _no,
            render_influence_analysis(response or "", inf),
            4, inf,
        )

    if audience_stage == 4:
        # Influence done → transition to study questions
        save_influence(session_id, influence_data)
        return (
            gr.update(visible=False, elem_classes=["aal-force-hide"]),
            gr.update(visible=True, elem_classes=["aal-force-show"]),
            _no,
            _no, 5, influence_data,
        )

    if audience_stage == 6:
        # Compare done → transition to thanks
        return (
            gr.update(visible=False, elem_classes=["aal-force-hide"]),
            _no,
            gr.update(visible=True, elem_classes=["aal-force-show"]),
            _no, 7, influence_data,
        )

    return _no, _no, _no, _no, audience_stage, influence_data


def handle_study_submit(session_id, prompt, q1, q2, q3):
    if not q1:
        return (
            gr.update(),                 # study_group
            gr.update(),                 # audience_viz_group
            gr.update(),                 # audience_display
            6,                           # audience_stage
            gr.update(value="**Please answer question 1 before submitting.**", visible=True),
        )
    save_study(session_id, prompt, q1, q2, q3)
    stats = fetch_aggregate_stats()
    return (
        gr.update(visible=False, elem_classes=["aal-force-hide"]),   # hide study
        gr.update(visible=True, elem_classes=["aal-force-show"]),    # show viz with compare
        render_audience_compare(stats),                               # audience_display
        6,                                                            # audience_stage
        gr.update(value="", visible=False),                          # study_err
    )


# ============================================================
# Gradio UI
# ============================================================

KEYBOARD_JS = """
() => {
  if (window._tedxKbSetup) return;
  window._tedxKbSetup = true;
  document.addEventListener('keydown', (e) => {
    const ae = document.activeElement;
    const tag = ae ? ae.tagName : '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'BUTTON' || tag === 'SELECT') return;
    const forward = ['ArrowRight', ' ', 'PageDown', 'ArrowDown', 'Enter'];
    const back    = ['ArrowLeft',  'PageUp',  'ArrowUp',  'Backspace'];
    const pv = document.querySelector('#presenter_view');
    const cv = document.querySelector('#corpus_view');
    const presenterVisible = pv && pv.offsetParent !== null;
    const corpusVisible    = cv && cv.offsetParent !== null;
    if (!presenterVisible && !corpusVisible) return;
    const fwdSel = presenterVisible ? '#forward_btn' : '#corpus_forward_btn';
    const backSel = presenterVisible ? '#back_btn'    : '#corpus_back_btn';
    if (forward.includes(e.key)) {
      e.preventDefault();
      const fb = document.querySelector(fwdSel + ' button') || document.querySelector(fwdSel);
      if (fb) fb.click();
    } else if (back.includes(e.key)) {
      e.preventDefault();
      const bb = document.querySelector(backSel + ' button') || document.querySelector(backSel);
      if (bb) bb.click();
    }
  });
}
"""


def _load_css():
    path = os.path.join(os.path.dirname(__file__), "static", "style.css")
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


with gr.Blocks(title="Ask Anything Lab") as demo:
    # -- State --
    stage = gr.State(0)
    embed_step = gr.State(0)
    audience_stage = gr.State(0)
    prompt_state = gr.State("")
    embeddings_state = gr.State({})
    sources_state = gr.State({})
    response_state = gr.State("")
    influence_state = gr.State({})
    session_id_state = gr.State("")
    corpus_idx = gr.State(0)

    # ============================================================
    # Landing view
    # ============================================================
    with gr.Column(visible=True, elem_id="landing_view") as landing_view:
        gr.HTML(LANDING_HTML)
        with gr.Row(elem_classes=["tedx-cta"]):
            with gr.Column(scale=2, min_width=0): pass
            with gr.Column(scale=2, elem_classes=["aal-cta-ghost"], min_width=160):
                go_presenter_btn = gr.Button("Presenter Demo", variant="secondary")
            with gr.Column(scale=3, elem_classes=["aal-cta-primary"], min_width=200):
                go_audience_btn = gr.Button("Try It Yourself  \u2192", variant="primary")
            with gr.Column(scale=2, elem_classes=["aal-cta-ghost"], min_width=160):
                go_corpus_btn = gr.Button("The Corpus Deck", variant="secondary")
            with gr.Column(scale=2, elem_classes=["aal-cta-ghost"], min_width=140):
                go_speaker_btn = gr.Button("Book John", variant="secondary")
            with gr.Column(scale=2, min_width=0): pass
        gr.HTML("""
        <div style="text-align:center; color:#475569; margin: 2em 0 3em; font-size:0.95em;">
          TEDx &middot; May 1, 2026 &middot;
          <a href="https://thatrandomagency.com" style="color:#64748B; text-decoration:none;">thatrandomagency.com</a>
        </div>
        """)

    # ============================================================
    # Presenter view
    # ============================================================
    with gr.Column(visible=False, elem_id="presenter_view") as presenter_view:
        presenter_display = gr.HTML(value=render_presenter_stage(0, 0))
        with gr.Row():
            with gr.Column(scale=1):
                home_btn_p = gr.Button("\u2190 Home", size="sm")
            with gr.Column(scale=4): pass
        # Hidden keyboard-proxy buttons (styled off-screen by CSS)
        forward_btn = gr.Button("forward", elem_id="forward_btn")
        back_btn = gr.Button("back", elem_id="back_btn")

    # ============================================================
    # Audience view — top-level sibling groups to avoid Gradio 6 nested
    # visibility cascading issues. Each view is an independent top-level
    # Column that can be toggled cleanly.
    # ============================================================

    # -- audience input group (first screen of audience mode) --
    with gr.Column(visible=False, elem_id="audience_input_view") as audience_input_group:
        gr.HTML("""
        <div style="max-width: 860px; margin: 3em auto 1em; padding: 0 2em;">
          <div style="color:#64748B; font-size:0.95em; letter-spacing:0.2em; text-transform:uppercase;">Ask anything</div>
          <h2 style="color:#F1F5F9; font-size:2.2em; margin-top:0.35em; font-weight:700;">
            Type a prompt. We&rsquo;ll show you what the AI does next.
          </h2>
          <p style="color:#64748B; font-size:1.1em; line-height:1.55;">
            Your words will travel through embedding &rarr; retrieval &rarr; synthesis &mdash;
            the same pipeline ChatGPT runs on every request.
          </p>
        </div>
        """)
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=3):
                prompt_box = gr.Textbox(
                    label="Your prompt",
                    placeholder="Ask me anything\u2026",
                    lines=3,
                    autofocus=True,
                )
                prompt_err = gr.Markdown(value="", visible=False)
                submit_btn = gr.Button("Process my prompt \u2192", variant="primary")
            with gr.Column(scale=1): pass

    # -- audience viz group (embed/retrieve/synthesize display) --
    with gr.Column(visible=False, elem_id="audience_viz_view") as audience_viz_group:
        audience_display = gr.HTML(value="")
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                continue_btn = gr.Button("Continue \u2192", variant="primary")
            with gr.Column(scale=1): pass

    # -- study questions group --
    with gr.Column(visible=False, elem_id="study_view") as study_group:
        gr.HTML(study_intro_html())
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=3):
                q1 = gr.Radio(
                    choices=[(label, value) for value, label in SURPRISING_OPTIONS],
                    label="1. Which stage surprised you most?",
                )
                q2 = gr.Slider(
                    minimum=1, maximum=5, step=1, value=3,
                    label="2. Before seeing this, how much did you trust AI answers? (1 = not at all, 5 = completely)",
                )
                q3 = gr.Slider(
                    minimum=1, maximum=5, step=1, value=3,
                    label="3. After seeing how it works, how much do you trust AI answers? (1 = not at all, 5 = completely)",
                )
                study_err = gr.Markdown(value="", visible=False)
                study_submit_btn = gr.Button("Submit", variant="primary")
            with gr.Column(scale=1): pass

    # -- thanks group --
    with gr.Column(visible=False, elem_id="thanks_view") as thanks_group:
        gr.HTML(thanks_html())
        with gr.Row():
            with gr.Column(scale=2): pass
            with gr.Column(scale=1):
                home_btn_a = gr.Button("\u2190 Back to start", size="sm")
            with gr.Column(scale=2): pass

    # ============================================================
    # Corpus slideshow view
    # ============================================================
    with gr.Column(visible=False, elem_id="corpus_view") as corpus_view:
        corpus_slide = gr.HTML(value=corpus_slideshow.slide_html(0))
        with gr.Row():
            with gr.Column(scale=1):
                home_btn_c = gr.Button("\u2190 Home", size="sm")
            with gr.Column(scale=4): pass
        # Hidden keyboard-proxy buttons (styled off-screen by CSS)
        corpus_forward_btn = gr.Button("corpus forward", elem_id="corpus_forward_btn")
        corpus_back_btn = gr.Button("corpus back", elem_id="corpus_back_btn")

    # ============================================================
    # Speaker / Book John view
    # ============================================================
    with gr.Column(visible=False, elem_id="speaker_view") as speaker_view:
        gr.HTML(SPEAKER_HTML)
        with gr.Row():
            with gr.Column(scale=1):
                home_btn_s = gr.Button("\u2190 Home", size="sm")
            with gr.Column(scale=4): pass

    # ============================================================
    # Event wiring
    # ============================================================

    go_presenter_btn.click(
        enter_presenter,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            stage, embed_step, presenter_display,
        ],
    )

    go_audience_btn.click(
        enter_audience,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            prompt_box, audience_stage,
        ],
    )

    go_corpus_btn.click(
        enter_corpus,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            corpus_idx, corpus_slide,
        ],
    )

    go_speaker_btn.click(
        enter_speaker,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
        ],
    )

    home_btn_p.click(
        go_home,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            stage, embed_step,
        ],
    )
    home_btn_a.click(
        go_home,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            stage, embed_step,
        ],
    )
    home_btn_c.click(
        go_home,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            stage, embed_step,
        ],
    )
    home_btn_s.click(
        go_home,
        outputs=[
            landing_view, presenter_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            corpus_view, speaker_view,
            stage, embed_step,
        ],
    )

    corpus_forward_btn.click(
        on_corpus_forward,
        inputs=[corpus_idx],
        outputs=[corpus_idx, corpus_slide],
    )
    corpus_back_btn.click(
        on_corpus_back,
        inputs=[corpus_idx],
        outputs=[corpus_idx, corpus_slide],
    )

    forward_btn.click(
        on_forward,
        inputs=[stage, embed_step],
        outputs=[stage, embed_step, presenter_display],
    )
    back_btn.click(
        on_back,
        inputs=[stage, embed_step],
        outputs=[stage, embed_step, presenter_display],
    )

    submit_btn.click(
        handle_audience_submit,
        inputs=[prompt_box],
        outputs=[
            audience_input_group, audience_viz_group, audience_display,
            audience_stage, prompt_state,
            embeddings_state, sources_state, response_state,
            influence_state,
            session_id_state, prompt_err,
        ],
        show_progress="hidden",
    )

    continue_btn.click(
        handle_audience_continue,
        inputs=[audience_stage, prompt_state, embeddings_state, sources_state,
                response_state, influence_state, session_id_state],
        outputs=[audience_viz_group, study_group, thanks_group,
                 audience_display, audience_stage, influence_state],
    )

    study_submit_btn.click(
        handle_study_submit,
        inputs=[session_id_state, prompt_state, q1, q2, q3],
        outputs=[study_group, audience_viz_group, audience_display,
                 audience_stage, study_err],
    )

    # Install keyboard listener on page load (Gradio 6: js= must go on .load())
    demo.load(fn=None, inputs=None, outputs=None, js=KEYBOARD_JS)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", os.environ.get("AAL_PORT", "7860"))),
        show_error=True,
        theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"),
        css=_load_css(),
        allowed_paths=[corpus_slideshow.slides_dir()],
    )
