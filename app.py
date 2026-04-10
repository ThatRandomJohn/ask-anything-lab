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
from components.embed_viz import render_embed_step, render_audience_embed
from components.source_list import render_sources
from components.typewriter import typewriter_html
from components.study import SURPRISING_OPTIONS, study_intro_html, thanks_html
from services.claude_api import process_prompt_parallel
from services.supabase_client import save_study


# ============================================================
# Presenter-mode stage rendering
# ============================================================

# Top-level stages: 0=Input, 1=Embed (6 sub-steps), 2=Retrieve, 3=Synthesize, 4=Reflect
EMBED_SUBSTEPS = 6


def render_presenter_stage(stage: int, embed_step: int) -> str:
    if stage == 0:
        return _render_input_stage()
    if stage == 1:
        return render_embed_step(embed_step)
    if stage == 2:
        return render_sources(label="Step 3 \u00b7 Retrieve")
    if stage == 3:
        return typewriter_html(RESPONSE)
    if stage == 4:
        return _render_reflect_stage()
    return _render_input_stage()


def _render_input_stage() -> str:
    escaped = _html.escape(PROMPT)
    return f"""
<div style="background:#06080C; padding: 5em 3em; min-height: 82vh; display:flex; flex-direction:column; justify-content:center;">
  <div style="max-width: 1100px; margin: 0 auto; text-align: center;">
    <div style="color:#64748B; font-size:1em; letter-spacing:0.22em; text-transform:uppercase; margin-bottom:1em;">Step 1 &middot; Input</div>
    <div style="color:#475569; font-size:1.2em; margin-bottom:1.5em;">Imagine you just typed this into ChatGPT.</div>
    <div style="color:#F1F5F9; font-size:2.4em; font-style:italic; line-height:1.4; padding:1em 0;">
      &ldquo;{escaped}&rdquo;
    </div>
    <div style="color:#64748B; margin-top:2em; font-size:1.05em;">Press &rarr; to watch what happens next.</div>
  </div>
</div>
"""


def _render_reflect_stage() -> str:
    return f"""
<div style="background:#06080C; padding: 6em 3em; min-height: 82vh; display:flex; flex-direction:column; justify-content:center; text-align:center;">
  <div style="color:#F59E0B; font-size:1em; letter-spacing:0.22em; text-transform:uppercase; margin-bottom:1.5em;">Step 5 &middot; Reflect</div>
  <div style="color:#F1F5F9; font-size:3em; font-weight:700; max-width:1100px; margin:0 auto; line-height:1.3; font-style:italic;">
    &ldquo;{_html.escape(REFLECT_QUOTE)}&rdquo;
  </div>
  <div style="color:#64748B; margin-top:2.5em; font-size:1.1em;">&mdash; Ask Anything</div>
</div>
"""


# ============================================================
# Presenter state machine
# ============================================================

def advance(stage: int, embed_step: int):
    if stage == 0:
        return 1, 0
    if stage == 1:
        if embed_step < EMBED_SUBSTEPS - 1:
            return 1, embed_step + 1
        return 2, 0
    if stage == 2:
        return 3, 0
    if stage == 3:
        return 4, 0
    return 4, 0


def retreat(stage: int, embed_step: int):
    if stage == 0:
        return 0, 0
    if stage == 1:
        if embed_step > 0:
            return 1, embed_step - 1
        return 0, 0
    if stage == 2:
        # Going back from Retrieve returns to the LAST embed sub-step, not the first.
        return 1, EMBED_SUBSTEPS - 1
    if stage == 3:
        return 2, 0
    if stage == 4:
        return 3, 0
    return 0, 0


def on_forward(stage: int, embed_step: int):
    new_stage, new_step = advance(stage, embed_step)
    return new_stage, new_step, render_presenter_stage(new_stage, new_step)


def on_back(stage: int, embed_step: int):
    new_stage, new_step = retreat(stage, embed_step)
    return new_stage, new_step, render_presenter_stage(new_stage, new_step)


# ============================================================
# Mode switching
# ============================================================

def enter_presenter():
    return (
        gr.update(visible=False),   # landing_view
        gr.update(visible=True),    # presenter_view
        gr.update(visible=False),   # audience_view
        0, 0,                       # stage, embed_step
        render_presenter_stage(0, 0),
    )


def enter_audience():
    return (
        gr.update(visible=False),   # landing_view
        gr.update(visible=False),   # presenter_view
        gr.update(visible=True),    # audience_view
        gr.update(visible=True),    # audience_input_group
        gr.update(visible=False),   # audience_viz_group
        gr.update(visible=False),   # study_group
        gr.update(visible=False),   # thanks_group
        "",                         # prompt_box reset
        0,                          # audience_stage reset
    )


def go_home():
    return (
        gr.update(visible=True),    # landing_view
        gr.update(visible=False),   # presenter_view
        gr.update(visible=False),   # audience_view
        0, 0,                       # stage, embed_step
    )


# ============================================================
# Audience-mode handlers
# ============================================================

def _loading_html(msg: str) -> str:
    return f"""
<div style="background:#06080C; padding: 6em 2em; min-height: 60vh; text-align:center;">
  <div style="color:#F1F5F9; font-size:1.6em; margin-bottom:0.6em;">{_html.escape(msg)}</div>
  <div style="color:#64748B; font-size:1.1em;">Claude is processing your prompt in parallel across three calls&hellip;</div>
  <div class="tedx-spinner" style="margin: 2.5em auto 0; width: 56px; height: 56px; border: 4px solid #1E293B; border-top-color:#F59E0B; border-radius:50%; animation: tedxSpin 900ms linear infinite;"></div>
</div>
<style>
@keyframes tedxSpin {{ to {{ transform: rotate(360deg); }} }}
</style>
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
            "",                    # session_id
            gr.update(value="**Please enter a prompt first.**", visible=True),
        )
        return

    prompt = prompt.strip()
    session_id = str(uuid.uuid4())

    # 1) Loading state
    yield (
        gr.update(visible=False),   # hide input
        gr.update(visible=True),    # show viz
        _loading_html("Embedding your words\u2026"),
        0,
        prompt,
        {}, {}, "",
        session_id,
        gr.update(value="", visible=False),
    )

    # 2) Fire the three calls in parallel
    embeddings, sources, response = process_prompt_parallel(prompt)

    # 3) Render the first audience viz stage (embed)
    yield (
        gr.update(visible=False),
        gr.update(visible=True),
        render_audience_embed(prompt, embeddings),
        1,  # audience_stage = 1 means embed is showing, next is retrieve
        prompt,
        embeddings, sources, response,
        session_id,
        gr.update(value="", visible=False),
    )


def handle_audience_continue(audience_stage, prompt, embeddings, sources, response):
    """Advance through audience stages: 1=embed showing -> 2=retrieve, 2=retrieve -> 3=synthesize, 3=synthesize -> 4=study."""
    if audience_stage == 1:
        srcs = (sources or {}).get("sources") if isinstance(sources, dict) else None
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            render_sources(srcs, label="Step 3 \u00b7 Retrieve"),
            2,
        )
    if audience_stage == 2:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            typewriter_html(response or "(no response)"),
            3,
        )
    if audience_stage == 3:
        return (
            gr.update(visible=False),   # hide viz
            gr.update(visible=True),    # show study
            "",
            4,
        )
    return gr.update(), gr.update(), "", audience_stage


def handle_study_submit(session_id, prompt, q1, q2, q3):
    if not q1:
        return (
            gr.update(),
            gr.update(),
            gr.update(value="**Please answer question 1 before submitting.**", visible=True),
        )
    save_study(session_id, prompt, q1, q2, q3)
    return (
        gr.update(visible=False),   # hide study
        gr.update(visible=True),    # show thanks
        gr.update(value="", visible=False),
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
    const pv = document.querySelector('#presenter_view');
    if (!pv || pv.offsetParent === null) return;  // only active when presenter mode is visible
    const forward = ['ArrowRight', ' ', 'PageDown', 'ArrowDown', 'Enter'];
    const back    = ['ArrowLeft',  'PageUp',  'ArrowUp',  'Backspace'];
    if (forward.includes(e.key)) {
      e.preventDefault();
      const fb = document.querySelector('#forward_btn button') || document.querySelector('#forward_btn');
      if (fb) fb.click();
    } else if (back.includes(e.key)) {
      e.preventDefault();
      const bb = document.querySelector('#back_btn button') || document.querySelector('#back_btn');
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
    session_id_state = gr.State("")

    # ============================================================
    # Landing view
    # ============================================================
    with gr.Column(visible=True, elem_id="landing_view") as landing_view:
        gr.HTML(LANDING_HTML)
        with gr.Row(elem_classes=["tedx-cta"]):
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                go_presenter_btn = gr.Button("Presenter Demo", variant="primary")
            with gr.Column(scale=2):
                go_audience_btn = gr.Button("Try It Yourself", variant="secondary")
            with gr.Column(scale=1): pass
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
    # Audience view
    # ============================================================
    with gr.Column(visible=False, elem_id="audience_view") as audience_view:

        # -- input group --
        with gr.Column(visible=True) as audience_input_group:
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

        # -- viz group (shared HTML slot for embed/retrieve/synthesize) --
        with gr.Column(visible=False) as audience_viz_group:
            audience_display = gr.HTML(value="")
            with gr.Row():
                with gr.Column(scale=1): pass
                with gr.Column(scale=2):
                    continue_btn = gr.Button("Continue \u2192", variant="primary")
                with gr.Column(scale=1): pass

        # -- study questions group --
        with gr.Column(visible=False) as study_group:
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
        with gr.Column(visible=False) as thanks_group:
            gr.HTML(thanks_html())
            with gr.Row():
                with gr.Column(scale=2): pass
                with gr.Column(scale=1):
                    home_btn_a = gr.Button("\u2190 Back to start", size="sm")
                with gr.Column(scale=2): pass

    # ============================================================
    # Event wiring
    # ============================================================

    go_presenter_btn.click(
        enter_presenter,
        outputs=[landing_view, presenter_view, audience_view, stage, embed_step, presenter_display],
    )

    go_audience_btn.click(
        enter_audience,
        outputs=[
            landing_view, presenter_view, audience_view,
            audience_input_group, audience_viz_group, study_group, thanks_group,
            prompt_box, audience_stage,
        ],
    )

    home_btn_p.click(
        go_home,
        outputs=[landing_view, presenter_view, audience_view, stage, embed_step],
    )
    home_btn_a.click(
        go_home,
        outputs=[landing_view, presenter_view, audience_view, stage, embed_step],
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
            session_id_state, prompt_err,
        ],
    )

    continue_btn.click(
        handle_audience_continue,
        inputs=[audience_stage, prompt_state, embeddings_state, sources_state, response_state],
        outputs=[audience_viz_group, study_group, audience_display, audience_stage],
    )

    study_submit_btn.click(
        handle_study_submit,
        inputs=[session_id_state, prompt_state, q1, q2, q3],
        outputs=[study_group, thanks_group, study_err],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"),
        css=_load_css(),
        js=KEYBOARD_JS,
    )
