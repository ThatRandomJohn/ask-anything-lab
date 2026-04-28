"""Brain visualization stage — interactive 3D cortical activation viewer.

Renders a Three.js scene with the fsaverage5 brain mesh, vertex-colored by
predicted activation values. Designed for theatrical impact in a large room.

Features:
- Hover raycasting: shows region name + score tooltip on mouse over
- Floating callout labels pointing to key brain regions
- Bold, high-contrast text optimized for projection in large rooms
"""
from __future__ import annotations

import json
import os

from data.brain_data import map_response_words

_HERE = os.path.dirname(__file__)
_STATIC = os.path.join(os.path.dirname(_HERE), "static")

_ROI_META = {
    "reward": {
        "label": "Reward Circuits",
        "desc": "Dopaminergic response to approval and validation",
        "color": "#EC4899",
        "vertices": [(1100, 1400), (11342, 11642)],
    },
    "amygdala": {
        "label": "Amygdala",
        "desc": "Emotional arousal and threat detection",
        "color": "#FB7185",
        "vertices": [(1390, 1490), (11632, 11732)],
    },
    "temporal": {
        "label": "Temporal Cortex",
        "desc": "Language comprehension and meaning",
        "color": "#F97316",
        "vertices": [(5600, 6200), (15842, 16442)],
    },
    "insula": {
        "label": "Insula",
        "desc": "Empathy and emotional awareness",
        "color": "#06B6D4",
        "vertices": [(4710, 4950), (14952, 15192)],
    },
    "cingulate": {
        "label": "Cingulate Cortex",
        "desc": "Conflict monitoring and reward processing",
        "color": "#FBBF24",
        "vertices": [(2100, 2500), (12342, 12742)],
    },
    "prefrontal": {
        "label": "Prefrontal Cortex",
        "desc": "Reasoning, judgment, and decision-making",
        "color": "#A78BFA",
        "vertices": [(800, 1200), (11042, 11442)],
    },
}


def _render_roi_breakdown(roi_scores: dict) -> str:
    rows = []
    sorted_rois = sorted(
        _ROI_META.items(),
        key=lambda kv: roi_scores.get(kv[0], 0),
        reverse=True,
    )
    for roi_key, meta in sorted_rois:
        score = roi_scores.get(roi_key, 0)
        pct = int(round(score * 100))
        rows.append(f"""
        <div class="aal-brain-roi-row" data-roi="{roi_key}">
          <div class="aal-brain-roi-header">
            <span class="aal-brain-roi-dot" style="background:{meta['color']};
              box-shadow: 0 0 14px {meta['color']}, 0 0 28px {meta['color']}44;"></span>
            <span class="aal-brain-roi-label" style="color:#FFFFFF;font-weight:800;font-size:1.15em;">{meta['label']}</span>
            <span class="aal-brain-roi-pct" style="color:{meta['color']};font-size:1.3em;font-weight:900;">{pct}%</span>
          </div>
          <div class="aal-brain-bar-track">
            <div class="aal-brain-bar-fill" style="width:{pct}%; background:
              linear-gradient(90deg, {meta['color']}44, {meta['color']});
              box-shadow: 0 0 12px {meta['color']}66;"></div>
          </div>
          <div style="color:#FFFFFF;font-size:0.95em;margin-top:0.2em;font-weight:500;">{meta['desc']}</div>
        </div>
        """)
    return "".join(rows)


def render_brain_stage(brain_data: dict, response: str = "") -> str:
    activations = brain_data.get("activations", [])
    roi_scores = brain_data.get("roi_scores", {})
    status = brain_data.get("status", "demo")

    roi_html = _render_roi_breakdown(roi_scores)
    act_json = json.dumps(activations, separators=(",", ":"))

    mesh_path = os.path.join(_STATIC, "fsaverage5.json")
    mesh_src = f"/gradio_api/file={mesh_path}"
    js_path = os.path.join(_STATIC, "brain3d.js")

    # Build ROI data as proper JSON for the JS file to parse
    roi_list = []
    for key, meta in _ROI_META.items():
        score = roi_scores.get(key, 0)
        roi_list.append({
            "key": key, "label": meta["label"], "color": meta["color"],
            "desc": meta["desc"], "score": round(score, 3),
            "ranges": meta["vertices"],
        })
    roi_json = json.dumps(roi_list, separators=(",", ":"))

    # Per-word ROI mapping for the response text
    word_map = map_response_words(response) if response else []
    word_map_json = json.dumps(word_map, separators=(",", ":"))

    status_banner = ""
    if status in ("demo", "fallback"):
        status_banner = """
        <div class="aal-brain-demo-banner">
          Reference activation &middot; live TRIBE v2 predictions coming soon
        </div>
        """

    step_label = "Step 5 &middot; Brain Response"

    return f"""
<div class="aal-brain-wrap">
  <div class="aal-brain-aurora">
    <div class="aal-brain-glow aal-brain-glow-1"></div>
    <div class="aal-brain-glow aal-brain-glow-2"></div>
    <div class="aal-brain-glow aal-brain-glow-3"></div>
  </div>

  <div class="aal-brain-inner">
    <div class="aal-brain-topbar">
      <div class="aal-brain-eyebrow-pill">
        <span class="aal-eyebrow-dot" style="background:#A78BFA; box-shadow: 0 0 12px #A78BFA;"></span>
        {step_label}
      </div>
    </div>

    <h2 style="font-size:3.2em;font-weight:900;color:#FFFFFF;margin:0.15em 0 0.2em;line-height:1.1;">
      This is your brain <span class="aal-brain-title-accent">on AI.</span>
    </h2>
    <p style="color:#FFFFFF;font-size:1.3em;max-width:780px;line-height:1.55;margin:0 0 0.8em;">
      TRIBE v2 maps <strong style="color:#FFFFFF;font-weight:800;">20,484 cortical points</strong> to predict how
      your brain responds to what you just read.
      <span style="color:#FFFFFF;font-weight:500;">The bright spots are where language becomes feeling.</span>
    </p>
    {status_banner}

    <div class="aal-brain-grid">
      <div class="aal-brain-canvas-card aal-influence-card-entrance">
        <div class="aal-brain-canvas-wrap">
          <canvas id="aal-brain-canvas"></canvas>
          <div id="aal-brain-tooltip" class="aal-brain-tooltip"></div>
          <div id="aal-brain-focus-panel" class="aal-brain-focus-panel"></div>
        </div>
        <div style="text-align:center;color:#FFFFFF;font-size:1em;margin-top:0.8em;font-weight:600;">
          Click a region to focus &middot; Drag to rotate &middot; Views snap at key angles
        </div>
        <div style="display:flex;align-items:center;justify-content:center;gap:1em;margin-top:0.6em;">
          <div style="display:flex;align-items:center;gap:0.5em;">
            <span style="color:#FFFFFF;font-size:0.82em;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;">Low</span>
            <div style="width:120px;height:8px;border-radius:4px;background:linear-gradient(90deg,#1E293B,#06B6D4,#A78BFA,#FB7185);"></div>
            <span style="color:#FFFFFF;font-size:0.82em;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;">High</span>
          </div>
          <div style="width:1px;height:16px;background:rgba(255,255,255,0.2);"></div>
          <div style="display:flex;align-items:center;gap:0.5em;">
            <span style="color:#FFFFFF;font-size:0.82em;font-weight:700;">Zoom</span>
            <input type="range" id="aal-brain-zoom" min="120" max="280" value="185"
                   style="width:100px;accent-color:#A78BFA;cursor:pointer;" />
          </div>
        </div>
      </div>

      <div class="aal-brain-regions-card aal-influence-card-entrance" style="animation-delay:200ms;">
        <div style="font-size:1.7em;font-weight:900;color:#FFFFFF;margin-bottom:0.1em;">Regional Activation</div>
        <div style="color:#FFFFFF;font-size:1.05em;margin-bottom:1.3em;font-weight:500;">
          Predicted cortical response to the AI&rsquo;s answer
        </div>
        {roi_html}
        <div style="margin-top:1em;padding-top:1em;border-top:1px solid rgba(167,139,250,0.20);
             color:#FFFFFF;font-size:0.95em;">
          <strong style="color:#FFFFFF;font-weight:700;">Click a region above</strong>
          to see which words from the AI&rsquo;s response activate it.
        </div>
      </div>
    </div>

    <!-- Word activation panel — shows when a ROI row is clicked -->
    <div id="aal-brain-words-panel" style="display:none;margin-top:1.4em;
         background:rgba(15,23,42,0.92);border:1px solid rgba(167,139,250,0.25);
         border-radius:18px;padding:1.4em 1.8em;">
      <div style="display:flex;align-items:center;gap:0.8em;margin-bottom:0.8em;">
        <span id="aal-words-roi-dot" style="width:12px;height:12px;border-radius:50%;flex-shrink:0;"></span>
        <span id="aal-words-roi-name" style="color:#FFFFFF;font-size:1.3em;font-weight:900;"></span>
        <span id="aal-words-roi-desc" style="color:#FFFFFF;font-size:0.95em;font-weight:400;margin-left:auto;"></span>
      </div>
      <div id="aal-words-stream" style="color:#FFFFFF;font-size:1.15em;line-height:1.8;min-height:3em;"></div>
    </div>
  </div>
</div>

<style>
/* ── WRAP & AURORA ── */
.aal-brain-wrap {{
  position: relative;
  min-height: 90vh;
  background: #06080C;
  overflow: hidden;
  padding: 1em 0 2.5em;
}}
.aal-brain-aurora {{
  position: absolute; inset: 0;
  pointer-events: none; z-index: 0;
  overflow: hidden;
}}
.aal-brain-glow {{
  position: absolute; border-radius: 50%;
  filter: blur(100px); opacity: 0.18;
  animation: aal-brain-drift 12s ease-in-out infinite alternate;
}}
.aal-brain-glow-1 {{
  width: 600px; height: 600px;
  background: radial-gradient(circle, #A78BFA 0%, transparent 70%);
  top: -15%; left: 10%;
}}
.aal-brain-glow-2 {{
  width: 500px; height: 500px;
  background: radial-gradient(circle, #06B6D4 0%, transparent 70%);
  top: 30%; right: -5%; animation-delay: -4s;
}}
.aal-brain-glow-3 {{
  width: 450px; height: 450px;
  background: radial-gradient(circle, #EC4899 0%, transparent 70%);
  bottom: -10%; left: 35%; animation-delay: -8s;
}}
@keyframes aal-brain-drift {{
  0% {{ transform: translate(0,0) scale(1); }}
  100% {{ transform: translate(30px,-20px) scale(1.08); }}
}}

/* ── LAYOUT ── */
.aal-brain-inner {{
  position: relative; z-index: 2;
  max-width: 1300px; margin: 0 auto;
  padding: 1.5em 2.5em 0;
}}
.aal-brain-topbar {{ margin-bottom: 0.8em; }}
.aal-brain-eyebrow-pill {{
  display: inline-flex; align-items: center; gap: 0.55em;
  background: rgba(167,139,250,0.14);
  border: 1px solid rgba(167,139,250,0.35);
  border-radius: 999px; padding: 0.45em 1.4em;
  font-size: 1em; letter-spacing: 0.18em;
  text-transform: uppercase; font-weight: 800;
  color: #DDD6FE;
}}

/* ── TYPOGRAPHY ── */
.aal-brain-title {{
  font-size: 3.2em; font-weight: 900;
  color: #FFFFFF; margin: 0.15em 0 0.2em;
  line-height: 1.1; letter-spacing: -0.02em;
  text-shadow: 0 0 40px rgba(167,139,250,0.15);
}}
.aal-brain-title-accent {{
  background: linear-gradient(135deg, #A78BFA, #EC4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.aal-brain-subtitle {{
  color: #F1F5F9; font-size: 1.3em;
  max-width: 780px; line-height: 1.55;
  margin: 0 0 0.8em; font-weight: 400;
}}
.aal-brain-subtitle strong {{
  color: #FFFFFF; font-weight: 800;
}}
.aal-brain-subtitle-em {{
  color: #F1F5F9; font-weight: 500;
}}
.aal-brain-demo-banner {{
  display: inline-block;
  background: rgba(251,191,36,0.10);
  border: 1px dashed rgba(251,191,36,0.35);
  border-radius: 8px; padding: 0.5em 1.2em;
  font-size: 0.9em; color: #FDE68A;
  font-weight: 600; margin-bottom: 1.2em;
}}

/* ── GRID ── */
.aal-brain-grid {{
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 1.8em; align-items: start;
  margin-top: 0.5em;
}}
@media (max-width: 960px) {{
  .aal-brain-grid {{ grid-template-columns: 1fr; }}
}}

/* ── CANVAS CARD ── */
.aal-brain-canvas-card {{
  background: rgba(15,23,42,0.92);
  border: 1px solid rgba(167,139,250,0.30);
  border-radius: 22px; padding: 1em;
  position: relative;
  box-shadow:
    0 0 40px rgba(167,139,250,0.08),
    0 0 80px rgba(6,182,212,0.05);
}}
.aal-brain-canvas-wrap {{
  position: relative; overflow: hidden;
  border-radius: 14px;
}}
#aal-brain-canvas {{
  width: 100%; height: 520px;
  display: block; background: #030712;
  cursor: grab;
  animation: aal-brain-fadein 0.5s ease-out;
}}
#aal-brain-canvas:active {{ cursor: grabbing; }}
@keyframes aal-brain-fadein {{
  0% {{ opacity: 0; }}
  100% {{ opacity: 1; }}
}}

/* ── HOVER TOOLTIP ── */
.aal-brain-tooltip {{
  position: absolute; pointer-events: none;
  display: none; z-index: 20;
  background: rgba(15,23,42,0.92);
  border: 1px solid rgba(167,139,250,0.4);
  border-radius: 12px; padding: 0.7em 1em;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 24px rgba(0,0,0,0.5);
  min-width: 180px;
  transform: translate(-50%, -110%);
}}
.aal-brain-tooltip-name {{
  font-size: 1em; font-weight: 800;
  color: #FFFFFF; margin-bottom: 0.15em;
}}
.aal-brain-tooltip-desc {{
  font-size: 0.82em; color: #94A3B8;
  margin-bottom: 0.35em;
}}
.aal-brain-tooltip-score {{
  font-size: 1.1em; font-weight: 900;
  font-variant-numeric: tabular-nums;
}}

/* ── FOCUS PANEL ── */
.aal-brain-focus-panel {{
  display: none;
  position: absolute; bottom: 16px; left: 16px; right: 16px;
  z-index: 20;
  background: rgba(15,23,42,0.92);
  border: 1px solid rgba(167,139,250,0.30);
  border-radius: 14px; padding: 1.1em 1.4em;
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  animation: aal-brain-fadein 0.3s ease-out;
}}
.aal-focus-name {{
  font-size: 1.3em; font-weight: 900;
  margin-bottom: 0.15em;
}}
.aal-focus-score {{
  font-size: 1.1em; font-weight: 800;
  margin-bottom: 0.3em;
}}
.aal-focus-desc {{
  color: #F1F5F9; font-size: 1.05em;
  margin-bottom: 0.4em; font-weight: 500;
}}
.aal-focus-detail {{
  color: #E2E8F0; font-size: 0.95em;
  line-height: 1.5; margin-bottom: 0.8em;
}}
.aal-focus-back {{
  background: rgba(167,139,250,0.15);
  border: 1px solid rgba(167,139,250,0.3);
  border-radius: 8px; padding: 0.4em 1em;
  color: #C4B5FD; font-size: 0.9em;
  font-weight: 700; cursor: pointer;
  transition: background 0.2s;
}}
.aal-focus-back:hover {{
  background: rgba(167,139,250,0.25);
}}

/* ── CONTROLS & LEGEND ── */
.aal-brain-controls-hint {{
  text-align: center; color: #F1F5F9;
  font-size: 1em; margin-top: 0.8em;
  letter-spacing: 0.04em; font-weight: 600;
}}
.aal-brain-legend {{
  display: flex; align-items: center;
  justify-content: center; gap: 0.8em;
  margin-top: 0.6em;
}}
.aal-brain-legend-label {{
  color: #F1F5F9; font-size: 0.95em;
  text-transform: uppercase; letter-spacing: 0.12em;
  font-weight: 800;
}}
.aal-brain-legend-bar {{
  width: 180px; height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, #1E293B, #06B6D4, #A78BFA, #FB7185);
  box-shadow: 0 0 12px rgba(167,139,250,0.3);
}}

/* ── REGIONS CARD ── */
.aal-brain-regions-card {{
  background: rgba(15,23,42,0.92);
  border: 1px solid rgba(167,139,250,0.25);
  border-radius: 22px; padding: 1.8em;
  box-shadow: 0 0 30px rgba(167,139,250,0.06);
}}
.aal-brain-regions-title {{
  font-size: 1.7em; font-weight: 900;
  color: #FFFFFF; margin-bottom: 0.1em;
}}
.aal-brain-regions-subtitle {{
  color: #F1F5F9; font-size: 1.05em;
  margin-bottom: 1.3em; font-weight: 500;
}}

/* ── ROI ROWS ── */
.aal-brain-roi-row {{
  margin-bottom: 1.15em;
  padding: 0.5em 0.6em; border-radius: 10px;
  transition: background 0.25s;
  cursor: default;
}}
.aal-brain-roi-row:hover,
.aal-brain-roi-row.aal-roi-active {{
  background: rgba(167,139,250,0.08);
}}
.aal-brain-roi-header {{
  display: flex; align-items: center;
  gap: 0.6em; margin-bottom: 0.3em;
}}
.aal-brain-roi-dot {{
  width: 12px; height: 12px;
  border-radius: 50%; flex-shrink: 0;
}}
.aal-brain-roi-label {{
  font-size: 1.15em; font-weight: 800;
  color: #FFFFFF; flex: 1;
}}
.aal-brain-roi-pct {{
  font-size: 1.3em; font-weight: 900;
  font-variant-numeric: tabular-nums;
}}
.aal-brain-bar-track {{
  height: 8px; background: #1E293B;
  border-radius: 4px; overflow: hidden;
}}
.aal-brain-bar-fill {{
  height: 100%; border-radius: 4px;
  transition: width 1.4s cubic-bezier(0.16,1,0.3,1);
}}
.aal-brain-roi-desc {{
  color: #F1F5F9; font-size: 0.95em;
  margin-top: 0.2em; font-weight: 500;
}}

/* ── NARRATIVE ── */
.aal-brain-narrative {{
  margin-top: 1.5em; padding-top: 1.2em;
  border-top: 1px solid rgba(167,139,250,0.20);
  color: #FFFFFF; font-size: 1.1em;
  line-height: 1.6;
}}
.aal-brain-narrative-headline {{
  display: block; color: #FFFFFF;
  font-size: 1.2em; font-weight: 900;
  margin-bottom: 0.3em;
  font-style: normal;
}}
</style>

<div id="aal-brain-data" style="display:none;">{act_json}</div>
<div id="aal-brain-mesh-url" style="display:none;">{mesh_src}</div>
<div id="aal-brain-roi-data" style="display:none;">{roi_json}</div>
<div id="aal-brain-word-map" style="display:none;">{word_map_json}</div>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
     onload="var s=document.createElement('script');s.src='/gradio_api/file={js_path}';document.head.appendChild(s);"
/>
"""
