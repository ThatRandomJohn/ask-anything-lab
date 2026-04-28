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
            <span class="aal-brain-roi-label">{meta['label']}</span>
            <span class="aal-brain-roi-pct" style="color:{meta['color']};">{pct}%</span>
          </div>
          <div class="aal-brain-bar-track">
            <div class="aal-brain-bar-fill" style="width:{pct}%; background:
              linear-gradient(90deg, {meta['color']}44, {meta['color']});
              box-shadow: 0 0 12px {meta['color']}66;"></div>
          </div>
          <div class="aal-brain-roi-desc">{meta['desc']}</div>
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

    # Build ROI data for JavaScript (vertex ranges, labels, colors, scores)
    roi_js_entries = []
    for key, meta in _ROI_META.items():
        score = roi_scores.get(key, 0)
        roi_js_entries.append(
            f'{{key:"{key}",label:"{meta["label"]}",color:"{meta["color"]}",'
            f'desc:"{meta["desc"]}",score:{score:.3f},'
            f'ranges:{json.dumps(meta["vertices"])}}}'
        )
    roi_js = "[" + ",".join(roi_js_entries) + "]"

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
    <div class="aal-think-blob aal-think-blob-a" style="opacity:0.22;"></div>
    <div class="aal-think-blob aal-think-blob-c" style="opacity:0.22;"></div>
  </div>

  <div class="aal-brain-inner">
    <div class="aal-brain-topbar">
      <div class="aal-brain-eyebrow-pill">
        <span class="aal-eyebrow-dot" style="background:#A78BFA; box-shadow: 0 0 12px #A78BFA;"></span>
        {step_label}
      </div>
    </div>

    <h2 class="aal-brain-title">
      This is your brain <span class="aal-brain-title-accent">on AI.</span>
    </h2>
    <p class="aal-brain-subtitle">
      TRIBE v2 maps <strong>20,484 cortical points</strong> to predict how
      your brain responds to what you just read.
      <span class="aal-brain-subtitle-em">The bright spots are where language becomes feeling.</span>
    </p>
    {status_banner}

    <div class="aal-brain-grid">
      <div class="aal-brain-canvas-card aal-influence-card-entrance">
        <div class="aal-brain-canvas-wrap">
          <canvas id="aal-brain-canvas"></canvas>
          <!-- Hover tooltip -->
          <div id="aal-brain-tooltip" class="aal-brain-tooltip"></div>
          <!-- Callout labels (positioned by JS) -->
          <div id="aal-brain-callouts" class="aal-brain-callouts"></div>
        </div>
        <div class="aal-brain-controls-hint">
          Drag to rotate &middot; Scroll to zoom &middot; Hover to explore regions
        </div>
        <div class="aal-brain-legend">
          <span class="aal-brain-legend-label">Low</span>
          <div class="aal-brain-legend-bar"></div>
          <span class="aal-brain-legend-label">High</span>
        </div>
      </div>

      <div class="aal-brain-regions-card aal-influence-card-entrance" style="animation-delay:200ms;">
        <div class="aal-brain-regions-title">Regional Activation</div>
        <div class="aal-brain-regions-subtitle">
          Predicted cortical response to the AI&rsquo;s answer
        </div>
        {roi_html}
        <div class="aal-brain-narrative">
          <strong class="aal-brain-narrative-headline">
            The AI&rsquo;s approval language lights up your reward circuits.
          </strong>
          The same regions triggered by social bonding, trust,
          and belonging. This isn&rsquo;t understanding &mdash;
          it&rsquo;s persuasion architecture.
        </div>
      </div>
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
  color: #E2E8F0; font-size: 1.3em;
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
  background: rgba(15,23,42,0.55);
  border: 1px solid rgba(167,139,250,0.22);
  border-radius: 22px; padding: 1em;
  position: relative;
  backdrop-filter: blur(16px);
  box-shadow:
    0 0 40px rgba(167,139,250,0.06),
    0 0 80px rgba(6,182,212,0.04),
    inset 0 1px 0 rgba(255,255,255,0.04);
}}
.aal-brain-canvas-wrap {{
  position: relative; overflow: hidden;
  border-radius: 14px;
}}
#aal-brain-canvas {{
  width: 100%; height: 520px;
  display: block; background: #030712;
  cursor: grab;
}}
#aal-brain-canvas:active {{ cursor: grabbing; }}

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

/* ── FLOATING CALLOUT LABELS ── */
.aal-brain-callouts {{
  position: absolute; inset: 0;
  pointer-events: none; z-index: 10;
}}
.aal-brain-callout {{
  position: absolute;
  display: flex; align-items: center; gap: 0.4em;
  font-size: 0.82em; font-weight: 700;
  color: #F1F5F9;
  text-shadow: 0 1px 6px rgba(0,0,0,0.8);
  opacity: 0;
  animation: aal-callout-in 0.6s ease-out forwards;
  transition: opacity 0.3s;
  white-space: nowrap;
}}
.aal-brain-callout-dot {{
  width: 8px; height: 8px;
  border-radius: 50%; flex-shrink: 0;
}}
.aal-brain-callout-line {{
  width: 24px; height: 1px;
  flex-shrink: 0;
}}
@keyframes aal-callout-in {{
  0% {{ opacity: 0; transform: translateY(6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

/* ── CONTROLS & LEGEND ── */
.aal-brain-controls-hint {{
  text-align: center; color: #CBD5E1;
  font-size: 0.95em; margin-top: 0.8em;
  letter-spacing: 0.04em; font-weight: 600;
}}
.aal-brain-legend {{
  display: flex; align-items: center;
  justify-content: center; gap: 0.8em;
  margin-top: 0.6em;
}}
.aal-brain-legend-label {{
  color: #CBD5E1; font-size: 0.88em;
  text-transform: uppercase; letter-spacing: 0.12em;
  font-weight: 700;
}}
.aal-brain-legend-bar {{
  width: 180px; height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, #1E293B, #06B6D4, #A78BFA, #FB7185);
  box-shadow: 0 0 12px rgba(167,139,250,0.3);
}}

/* ── REGIONS CARD ── */
.aal-brain-regions-card {{
  background: rgba(15,23,42,0.55);
  border: 1px solid rgba(167,139,250,0.15);
  border-radius: 22px; padding: 1.8em;
  backdrop-filter: blur(16px);
  box-shadow:
    0 0 30px rgba(167,139,250,0.04),
    inset 0 1px 0 rgba(255,255,255,0.04);
}}
.aal-brain-regions-title {{
  font-size: 1.6em; font-weight: 900;
  color: #FFFFFF; margin-bottom: 0.1em;
}}
.aal-brain-regions-subtitle {{
  color: #CBD5E1; font-size: 1em;
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
  font-size: 1.1em; font-weight: 700;
  color: #F8FAFC; flex: 1;
}}
.aal-brain-roi-pct {{
  font-size: 1.2em; font-weight: 900;
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
  color: #CBD5E1; font-size: 0.92em;
  margin-top: 0.2em; font-weight: 400;
}}

/* ── NARRATIVE ── */
.aal-brain-narrative {{
  margin-top: 1.5em; padding-top: 1.2em;
  border-top: 1px solid rgba(167,139,250,0.15);
  color: #E2E8F0; font-size: 1.05em;
  line-height: 1.6;
}}
.aal-brain-narrative-headline {{
  display: block; color: #FFFFFF;
  font-size: 1.15em; font-weight: 800;
  margin-bottom: 0.3em;
  font-style: normal;
}}
</style>

<div id="aal-brain-data" style="display:none;">{act_json}</div>
<div id="aal-brain-mesh-url" style="display:none;">{mesh_src}</div>
<div id="aal-brain-roi-data" style="display:none;">{roi_js}</div>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
     onload="
(function() {{
  if (document.getElementById('aal-brain-canvas') && window._aalBrainDone) return;
  window._aalBrainDone = true;

  function loadScript(src) {{
    return new Promise(function(ok, fail) {{
      var s = document.createElement('script');
      s.src = src; s.crossOrigin = 'anonymous';
      s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    }});
  }}

  var base = 'https://unpkg.com/three@0.137.0';
  var p = window.THREE ? Promise.resolve() : loadScript(base + '/build/three.min.js');
  p.then(function() {{
    return window.THREE.OrbitControls ? Promise.resolve()
      : loadScript(base + '/examples/js/controls/OrbitControls.js');
  }}).then(initBrain).catch(function(e) {{ console.error('Three.js load failed:', e); }});

  function initBrain() {{
    var ACT = JSON.parse(document.getElementById('aal-brain-data').textContent);
    var MESH_URL = document.getElementById('aal-brain-mesh-url').textContent.trim();
    var ROIS = eval('(' + document.getElementById('aal-brain-roi-data').textContent + ')');

    /* Build vertex → ROI lookup */
    var vertexROI = new Int8Array(20484);
    vertexROI.fill(-1);
    for (var ri = 0; ri < ROIS.length; ri++) {{
      var ranges = ROIS[ri].ranges;
      for (var rr = 0; rr < ranges.length; rr++) {{
        for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < 20484; vi++) {{
          vertexROI[vi] = ri;
        }}
      }}
    }}

    function activationColor(v) {{
      v = Math.max(0, Math.min(1, v));
      var stops = [
        [0.0,  0.071, 0.098, 0.141],
        [0.15, 0.075, 0.220, 0.310],
        [0.35, 0.024, 0.714, 0.831],
        [0.55, 0.455, 0.380, 0.900],
        [0.75, 0.655, 0.545, 0.984],
        [0.90, 0.925, 0.380, 0.520],
        [1.0,  1.000, 0.700, 0.780],
      ];
      var lo = stops[0], hi = stops[stops.length - 1];
      for (var i = 0; i < stops.length - 1; i++) {{
        if (v >= stops[i][0] && v <= stops[i + 1][0]) {{ lo = stops[i]; hi = stops[i + 1]; break; }}
      }}
      var t = (hi[0] - lo[0]) > 0 ? (v - lo[0]) / (hi[0] - lo[0]) : 0;
      t = t * t * (3 - 2 * t);
      return [lo[1]+t*(hi[1]-lo[1]), lo[2]+t*(hi[2]-lo[2]), lo[3]+t*(hi[3]-lo[3])];
    }}

    var T = window.THREE;
    var canvas = document.getElementById('aal-brain-canvas');
    var tooltip = document.getElementById('aal-brain-tooltip');
    var calloutsEl = document.getElementById('aal-brain-callouts');
    if (!canvas) return;

    var rect = canvas.getBoundingClientRect();
    var W = rect.width || 700, H = rect.height || 520;

    var renderer = new T.WebGLRenderer({{ canvas: canvas, antialias: true, alpha: true }});
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030712, 1);
    if (T.ACESFilmicToneMapping) {{
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
    }}

    var scene = new T.Scene();
    var camera = new T.PerspectiveCamera(32, W / H, 1, 500);
    camera.position.set(0, 15, 185);

    var controls = new T.OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.4;
    controls.minDistance = 90;
    controls.maxDistance = 280;
    controls.enablePan = false;

    scene.add(new T.AmbientLight(0x1E293B, 0.8));
    scene.add(new T.HemisphereLight(0x06B6D4, 0xF97316, 0.5));
    var kl = new T.DirectionalLight(0xA78BFA, 0.7); kl.position.set(60,90,70); scene.add(kl);
    var fl = new T.DirectionalLight(0x06B6D4, 0.35); fl.position.set(-50,30,80); scene.add(fl);
    var rl = new T.DirectionalLight(0xEC4899, 0.45); rl.position.set(-40,-30,-70); scene.add(rl);
    var ul = new T.PointLight(0xF97316, 0.3, 300); ul.position.set(0,-80,30); scene.add(ul);

    /* Raycaster for hover */
    var raycaster = new T.Raycaster();
    var mouse = new T.Vector2();
    var brainMesh = null;
    var lastROI = -1;

    /* ROI center positions (computed after mesh loads) */
    var roiCenters = [];

    fetch(MESH_URL).then(function(r) {{ return r.json(); }}).then(function(mesh) {{
      var geo = new T.BufferGeometry();
      var verts = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {{
        verts[i*3] = mesh.vertices[i][0];
        verts[i*3+1] = mesh.vertices[i][1];
        verts[i*3+2] = mesh.vertices[i][2];
      }}
      geo.setAttribute('position', new T.BufferAttribute(verts, 3));

      var idx = new Uint32Array(mesh.faces.length * 3);
      for (var i = 0; i < mesh.faces.length; i++) {{
        idx[i*3] = mesh.faces[i][0]; idx[i*3+1] = mesh.faces[i][1]; idx[i*3+2] = mesh.faces[i][2];
      }}
      geo.setIndex(new T.BufferAttribute(idx, 1));

      var cols = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {{
        var a = i < ACT.length ? ACT[i] : 0;
        var c = activationColor(a);
        cols[i*3] = c[0]; cols[i*3+1] = c[1]; cols[i*3+2] = c[2];
      }}
      geo.setAttribute('color', new T.BufferAttribute(cols, 3));
      geo.computeVertexNormals();

      var mat = new T.MeshStandardMaterial({{
        vertexColors: true, roughness: 0.4, metalness: 0.15, side: T.DoubleSide,
      }});
      brainMesh = new T.Mesh(geo, mat);
      brainMesh.rotation.x = -Math.PI * 0.08;
      scene.add(brainMesh);

      var wm = new T.MeshBasicMaterial({{
        color: 0x6366F1, wireframe: true, transparent: true, opacity: 0.03,
      }});
      var wire = new T.Mesh(geo.clone(), wm);
      wire.rotation.x = brainMesh.rotation.x;
      scene.add(wire);

      /* Compute ROI 3D centers for callout labels */
      for (var ri = 0; ri < ROIS.length; ri++) {{
        var cx=0, cy=0, cz=0, cnt=0;
        var ranges = ROIS[ri].ranges;
        for (var rr = 0; rr < ranges.length; rr++) {{
          for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < mesh.vertices.length; vi++) {{
            cx += mesh.vertices[vi][0]; cy += mesh.vertices[vi][1]; cz += mesh.vertices[vi][2];
            cnt++;
          }}
        }}
        if (cnt > 0) roiCenters.push(new T.Vector3(cx/cnt, cy/cnt, cz/cnt));
        else roiCenters.push(new T.Vector3(0,0,0));
      }}
    }}).catch(function(e) {{ console.error('Brain mesh load failed:', e); }});

    /* Hover handler */
    canvas.addEventListener('mousemove', function(e) {{
      var cr = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - cr.left) / cr.width) * 2 - 1;
      mouse.y = -((e.clientY - cr.top) / cr.height) * 2 + 1;

      if (!brainMesh) return;
      raycaster.setFromCamera(mouse, camera);
      var hits = raycaster.intersectObject(brainMesh);

      if (hits.length > 0) {{
        var faceIdx = hits[0].faceIndex;
        var face = brainMesh.geometry.index;
        var a = face.getX(faceIdx * 3), b = face.getX(faceIdx * 3 + 1), c = face.getX(faceIdx * 3 + 2);
        /* Check which ROI this vertex belongs to */
        var roiIdx = -1;
        if (vertexROI[a] >= 0) roiIdx = vertexROI[a];
        else if (vertexROI[b] >= 0) roiIdx = vertexROI[b];
        else if (vertexROI[c] >= 0) roiIdx = vertexROI[c];

        if (roiIdx >= 0 && roiIdx < ROIS.length) {{
          var roi = ROIS[roiIdx];
          var pct = Math.round(roi.score * 100);
          tooltip.innerHTML = '<div class=\"aal-brain-tooltip-name\" style=\"color:' + roi.color + '\">' + roi.label + '</div>'
            + '<div class=\"aal-brain-tooltip-desc\">' + roi.desc + '</div>'
            + '<div class=\"aal-brain-tooltip-score\" style=\"color:' + roi.color + '\">' + pct + '% activation</div>';
          tooltip.style.display = 'block';
          tooltip.style.left = (e.clientX - cr.left) + 'px';
          tooltip.style.top = (e.clientY - cr.top) + 'px';
          tooltip.style.borderColor = roi.color + '88';
          canvas.style.cursor = 'pointer';

          /* Highlight matching ROI row */
          if (roiIdx !== lastROI) {{
            var rows = document.querySelectorAll('.aal-brain-roi-row');
            rows.forEach(function(r) {{ r.classList.remove('aal-roi-active'); }});
            var match = document.querySelector('.aal-brain-roi-row[data-roi=\"' + roi.key + '\"]');
            if (match) match.classList.add('aal-roi-active');
            lastROI = roiIdx;
          }}
        }} else {{
          tooltip.style.display = 'none';
          canvas.style.cursor = 'grab';
          if (lastROI >= 0) {{
            document.querySelectorAll('.aal-brain-roi-row').forEach(function(r) {{ r.classList.remove('aal-roi-active'); }});
            lastROI = -1;
          }}
        }}
      }} else {{
        tooltip.style.display = 'none';
        canvas.style.cursor = 'grab';
        if (lastROI >= 0) {{
          document.querySelectorAll('.aal-brain-roi-row').forEach(function(r) {{ r.classList.remove('aal-roi-active'); }});
          lastROI = -1;
        }}
      }}
    }});
    canvas.addEventListener('mouseleave', function() {{
      tooltip.style.display = 'none';
      document.querySelectorAll('.aal-brain-roi-row').forEach(function(r) {{ r.classList.remove('aal-roi-active'); }});
      lastROI = -1;
    }});

    /* Floating callout labels — project ROI centers to 2D each frame */
    var calloutEls = [];
    function updateCallouts() {{
      if (!brainMesh || roiCenters.length === 0) return;
      if (calloutEls.length === 0 && calloutsEl) {{
        /* Create callout DOM elements once */
        for (var ri = 0; ri < ROIS.length; ri++) {{
          var el = document.createElement('div');
          el.className = 'aal-brain-callout';
          el.style.animationDelay = (ri * 120) + 'ms';
          el.innerHTML = '<span class=\"aal-brain-callout-dot\" style=\"background:' + ROIS[ri].color
            + ';box-shadow:0 0 8px ' + ROIS[ri].color + '\"></span>'
            + '<span class=\"aal-brain-callout-line\" style=\"background:' + ROIS[ri].color + '55\"></span>'
            + '<span>' + ROIS[ri].label + '</span>';
          calloutsEl.appendChild(el);
          calloutEls.push(el);
        }}
      }}
      var cr = canvas.getBoundingClientRect();
      for (var ri = 0; ri < roiCenters.length && ri < calloutEls.length; ri++) {{
        var pos = roiCenters[ri].clone();
        pos.applyAxisAngle(new T.Vector3(1,0,0), brainMesh.rotation.x);
        pos.project(camera);
        var x = (pos.x * 0.5 + 0.5) * cr.width;
        var y = (-pos.y * 0.5 + 0.5) * cr.height;
        /* Only show if in front of camera */
        if (pos.z < 1 && x > 20 && x < cr.width - 20 && y > 20 && y < cr.height - 40) {{
          calloutEls[ri].style.left = x + 'px';
          calloutEls[ri].style.top = y + 'px';
          calloutEls[ri].style.opacity = '1';
        }} else {{
          calloutEls[ri].style.opacity = '0';
        }}
      }}
    }}

    (function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
      updateCallouts();
    }})();

    new ResizeObserver(function() {{
      var r = canvas.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {{
        W = r.width; H = r.height;
        camera.aspect = W / H;
        camera.updateProjectionMatrix();
        renderer.setSize(W, H);
      }}
    }}).observe(canvas.parentElement);
  }}
}})();
"
/>
"""
