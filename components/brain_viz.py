"""Brain visualization stage — interactive 3D cortical activation viewer.

Renders a Three.js scene with the fsaverage5 brain mesh, vertex-colored by
predicted activation values. Designed for theatrical impact in a large room:
bold typography, glowing accents, generous canvas, aurora lighting.

Uses pre-computed demo data (Phase 1) or live TRIBE v2 predictions (Phase 2).
"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(__file__)
_STATIC = os.path.join(os.path.dirname(_HERE), "static")

# Brain region metadata for the ROI breakdown panel
_ROI_META = {
    "reward": {
        "label": "Reward Circuits",
        "desc": "Dopaminergic response to approval and validation",
        "color": "#EC4899",
        "icon": "reward",
    },
    "amygdala": {
        "label": "Amygdala",
        "desc": "Emotional arousal and threat detection",
        "color": "#FB7185",
        "icon": "amygdala",
    },
    "temporal": {
        "label": "Temporal Cortex",
        "desc": "Language comprehension and meaning",
        "color": "#F97316",
        "icon": "temporal",
    },
    "insula": {
        "label": "Insula",
        "desc": "Empathy and emotional awareness",
        "color": "#06B6D4",
        "icon": "insula",
    },
    "cingulate": {
        "label": "Cingulate Cortex",
        "desc": "Conflict monitoring and reward processing",
        "color": "#FBBF24",
        "icon": "cingulate",
    },
    "prefrontal": {
        "label": "Prefrontal Cortex",
        "desc": "Reasoning, judgment, and decision-making",
        "color": "#A78BFA",
        "icon": "prefrontal",
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
        <div class="aal-brain-roi-row">
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
  <!-- Aurora background blobs -->
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
      <br/>
      <span class="aal-brain-subtitle-em">The bright spots are where language becomes feeling.</span>
    </p>
    {status_banner}

    <div class="aal-brain-grid">
      <!-- 3D brain canvas -->
      <div class="aal-brain-canvas-card aal-influence-card-entrance">
        <canvas id="aal-brain-canvas"></canvas>
        <div class="aal-brain-controls-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
        <div class="aal-brain-legend">
          <span class="aal-brain-legend-label">Low</span>
          <div class="aal-brain-legend-bar"></div>
          <span class="aal-brain-legend-label">High</span>
        </div>
      </div>

      <!-- ROI breakdown -->
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
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.18;
  animation: aal-brain-drift 12s ease-in-out infinite alternate;
}}
.aal-brain-glow-1 {{
  width: 600px; height: 600px;
  background: radial-gradient(circle, #A78BFA 0%, transparent 70%);
  top: -15%; left: 10%;
  animation-delay: 0s;
}}
.aal-brain-glow-2 {{
  width: 500px; height: 500px;
  background: radial-gradient(circle, #06B6D4 0%, transparent 70%);
  top: 30%; right: -5%;
  animation-delay: -4s;
}}
.aal-brain-glow-3 {{
  width: 450px; height: 450px;
  background: radial-gradient(circle, #EC4899 0%, transparent 70%);
  bottom: -10%; left: 35%;
  animation-delay: -8s;
}}
@keyframes aal-brain-drift {{
  0% {{ transform: translate(0, 0) scale(1); }}
  100% {{ transform: translate(30px, -20px) scale(1.08); }}
}}

/* ── LAYOUT ── */
.aal-brain-inner {{
  position: relative; z-index: 2;
  max-width: 1300px; margin: 0 auto;
  padding: 1.5em 2.5em 0;
}}
.aal-brain-topbar {{
  margin-bottom: 0.8em;
}}
.aal-brain-eyebrow-pill {{
  display: inline-flex; align-items: center; gap: 0.55em;
  background: rgba(167,139,250,0.12);
  border: 1px solid rgba(167,139,250,0.30);
  border-radius: 999px; padding: 0.4em 1.3em;
  font-size: 0.95em; letter-spacing: 0.18em;
  text-transform: uppercase; font-weight: 800;
  color: #C4B5FD;
}}

/* ── TYPOGRAPHY — large room readable ── */
.aal-brain-title {{
  font-size: 3em; font-weight: 900;
  color: #FFFFFF; margin: 0.15em 0 0.2em;
  line-height: 1.1; letter-spacing: -0.02em;
}}
.aal-brain-title-accent {{
  background: linear-gradient(135deg, #A78BFA, #EC4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.aal-brain-subtitle {{
  color: #CBD5E1; font-size: 1.25em;
  max-width: 780px; line-height: 1.6;
  margin: 0 0 1em; font-weight: 400;
}}
.aal-brain-subtitle strong {{
  color: #FFFFFF; font-weight: 700;
}}
.aal-brain-subtitle-em {{
  color: #E2E8F0; font-weight: 500;
}}
.aal-brain-demo-banner {{
  display: inline-block;
  background: rgba(251,191,36,0.08);
  border: 1px dashed rgba(251,191,36,0.30);
  border-radius: 8px; padding: 0.45em 1.1em;
  font-size: 0.85em; color: #FCD34D;
  font-weight: 600; margin-bottom: 1.2em;
}}

/* ── GRID ── */
.aal-brain-grid {{
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 1.8em;
  align-items: start;
  margin-top: 0.5em;
}}
@media (max-width: 960px) {{
  .aal-brain-grid {{ grid-template-columns: 1fr; }}
}}

/* ── CANVAS CARD ── */
.aal-brain-canvas-card {{
  background: rgba(15,23,42,0.55);
  border: 1px solid rgba(167,139,250,0.20);
  border-radius: 22px;
  padding: 1em;
  position: relative;
  backdrop-filter: blur(16px);
  box-shadow:
    0 0 40px rgba(167,139,250,0.06),
    0 0 80px rgba(6,182,212,0.04),
    inset 0 1px 0 rgba(255,255,255,0.04);
}}
#aal-brain-canvas {{
  width: 100%; height: 520px;
  display: block; border-radius: 14px;
  background: #030712;
}}
.aal-brain-controls-hint {{
  text-align: center; color: #94A3B8;
  font-size: 0.88em; margin-top: 0.8em;
  letter-spacing: 0.06em; font-weight: 500;
}}
.aal-brain-legend {{
  display: flex; align-items: center;
  justify-content: center; gap: 0.8em;
  margin-top: 0.6em;
}}
.aal-brain-legend-label {{
  color: #94A3B8; font-size: 0.82em;
  text-transform: uppercase; letter-spacing: 0.12em;
  font-weight: 700;
}}
.aal-brain-legend-bar {{
  width: 160px; height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, #1E293B, #06B6D4, #A78BFA, #FB7185);
  box-shadow: 0 0 12px rgba(167,139,250,0.3);
}}

/* ── REGIONS CARD ── */
.aal-brain-regions-card {{
  background: rgba(15,23,42,0.55);
  border: 1px solid rgba(167,139,250,0.15);
  border-radius: 22px;
  padding: 1.8em;
  backdrop-filter: blur(16px);
  box-shadow:
    0 0 30px rgba(167,139,250,0.04),
    inset 0 1px 0 rgba(255,255,255,0.04);
}}
.aal-brain-regions-title {{
  font-size: 1.5em; font-weight: 900;
  color: #FFFFFF; margin-bottom: 0.15em;
  letter-spacing: -0.01em;
}}
.aal-brain-regions-subtitle {{
  color: #94A3B8; font-size: 0.95em;
  margin-bottom: 1.3em; font-weight: 500;
}}

/* ── ROI ROWS ── */
.aal-brain-roi-row {{
  margin-bottom: 1.1em;
}}
.aal-brain-roi-header {{
  display: flex; align-items: center;
  gap: 0.6em; margin-bottom: 0.3em;
}}
.aal-brain-roi-dot {{
  width: 10px; height: 10px;
  border-radius: 50%; flex-shrink: 0;
}}
.aal-brain-roi-label {{
  font-size: 1.05em; font-weight: 700;
  color: #F1F5F9; flex: 1;
}}
.aal-brain-roi-pct {{
  font-size: 1.1em; font-weight: 800;
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
  color: #94A3B8; font-size: 0.88em;
  margin-top: 0.2em; font-weight: 400;
}}

/* ── NARRATIVE ── */
.aal-brain-narrative {{
  margin-top: 1.5em; padding-top: 1.2em;
  border-top: 1px solid rgba(167,139,250,0.15);
  color: #CBD5E1; font-size: 1em;
  line-height: 1.6;
}}
.aal-brain-narrative-headline {{
  display: block; color: #FFFFFF;
  font-size: 1.1em; font-weight: 800;
  margin-bottom: 0.3em;
  font-style: normal;
}}
</style>

<div id="aal-brain-data" style="display:none;">{act_json}</div>
<div id="aal-brain-mesh-url" style="display:none;">{mesh_src}</div>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
     onload="
(function() {{
  if (window._aalBrainInit) return;
  window._aalBrainInit = true;

  var THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
  var ORBIT_URL = 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js';

  var ACTIVATIONS = JSON.parse(document.getElementById('aal-brain-data').textContent);
  var MESH_URL = document.getElementById('aal-brain-mesh-url').textContent.trim();

  function activationColor(v) {{
    v = Math.max(0, Math.min(1, v));
    /* Richer color ramp with more glow at peaks */
    var stops = [
      [0.0,  0.071, 0.098, 0.141],  /* #121926 deep dark */
      [0.15, 0.075, 0.220, 0.310],  /* dark teal hint */
      [0.35, 0.024, 0.714, 0.831],  /* #06B6D4 cyan */
      [0.55, 0.455, 0.380, 0.900],  /* blue-purple transition */
      [0.75, 0.655, 0.545, 0.984],  /* #A78BFA purple */
      [0.90, 0.925, 0.380, 0.520],  /* #EC6185 hot rose */
      [1.0,  1.000, 0.700, 0.780],  /* bright rose-white */
    ];
    var lo = stops[0], hi = stops[stops.length - 1];
    for (var i = 0; i < stops.length - 1; i++) {{
      if (v >= stops[i][0] && v <= stops[i + 1][0]) {{
        lo = stops[i]; hi = stops[i + 1];
        break;
      }}
    }}
    var t = (hi[0] - lo[0]) > 0 ? (v - lo[0]) / (hi[0] - lo[0]) : 0;
    /* Smooth-step for softer transitions */
    t = t * t * (3 - 2 * t);
    return [
      lo[1] + t * (hi[1] - lo[1]),
      lo[2] + t * (hi[2] - lo[2]),
      lo[3] + t * (hi[3] - lo[3]),
    ];
  }}

  Promise.all([
    import(THREE_URL),
    import(ORBIT_URL)
  ]).then(function(mods) {{
    var THREE = mods[0];
    var OrbitControls = mods[1].OrbitControls;

    var canvas = document.getElementById('aal-brain-canvas');
    if (!canvas) return;

    var rect = canvas.getBoundingClientRect();
    var width = rect.width || 700;
    var height = rect.height || 520;

    var renderer = new THREE.WebGLRenderer({{
      canvas: canvas, antialias: true, alpha: true,
    }});
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030712, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    var scene = new THREE.Scene();

    var camera = new THREE.PerspectiveCamera(32, width / height, 1, 500);
    camera.position.set(0, 15, 185);

    var controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.4;
    controls.minDistance = 90;
    controls.maxDistance = 280;
    controls.enablePan = false;

    /* Dramatic aurora lighting */
    scene.add(new THREE.AmbientLight(0x1E293B, 0.8));

    var hemi = new THREE.HemisphereLight(0x06B6D4, 0xF97316, 0.5);
    scene.add(hemi);

    var keyLight = new THREE.DirectionalLight(0xA78BFA, 0.7);
    keyLight.position.set(60, 90, 70);
    scene.add(keyLight);

    var fillLight = new THREE.DirectionalLight(0x06B6D4, 0.35);
    fillLight.position.set(-50, 30, 80);
    scene.add(fillLight);

    var rimLight = new THREE.DirectionalLight(0xEC4899, 0.45);
    rimLight.position.set(-40, -30, -70);
    scene.add(rimLight);

    var underLight = new THREE.PointLight(0xF97316, 0.3, 300);
    underLight.position.set(0, -80, 30);
    scene.add(underLight);

    fetch(MESH_URL).then(function(r) {{ return r.json(); }}).then(function(mesh) {{
      var geometry = new THREE.BufferGeometry();

      var verts = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {{
        verts[i * 3] = mesh.vertices[i][0];
        verts[i * 3 + 1] = mesh.vertices[i][1];
        verts[i * 3 + 2] = mesh.vertices[i][2];
      }}
      geometry.setAttribute('position', new THREE.BufferAttribute(verts, 3));

      var indices = new Uint32Array(mesh.faces.length * 3);
      for (var i = 0; i < mesh.faces.length; i++) {{
        indices[i * 3] = mesh.faces[i][0];
        indices[i * 3 + 1] = mesh.faces[i][1];
        indices[i * 3 + 2] = mesh.faces[i][2];
      }}
      geometry.setIndex(new THREE.BufferAttribute(indices, 1));

      var colors = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {{
        var act = i < ACTIVATIONS.length ? ACTIVATIONS[i] : 0;
        var c = activationColor(act);
        colors[i * 3] = c[0];
        colors[i * 3 + 1] = c[1];
        colors[i * 3 + 2] = c[2];
      }}
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      geometry.computeVertexNormals();

      /* Glossy brain material */
      var material = new THREE.MeshPhysicalMaterial({{
        vertexColors: true,
        roughness: 0.38,
        metalness: 0.12,
        clearcoat: 0.3,
        clearcoatRoughness: 0.4,
        side: THREE.DoubleSide,
        envMapIntensity: 0.5,
      }});

      var brainMesh = new THREE.Mesh(geometry, material);
      brainMesh.rotation.x = -Math.PI * 0.08;
      scene.add(brainMesh);

      /* Subtle glowing wireframe */
      var wireMat = new THREE.MeshBasicMaterial({{
        color: 0x6366F1, wireframe: true, transparent: true, opacity: 0.03,
      }});
      var wireOverlay = new THREE.Mesh(geometry.clone(), wireMat);
      wireOverlay.rotation.x = brainMesh.rotation.x;
      scene.add(wireOverlay);
    }}).catch(function(e) {{ console.error('Brain mesh load failed:', e); }});

    function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();

    var ro = new ResizeObserver(function() {{
      var r = canvas.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {{
        camera.aspect = r.width / r.height;
        camera.updateProjectionMatrix();
        renderer.setSize(r.width, r.height);
      }}
    }});
    ro.observe(canvas.parentElement);
  }}).catch(function(e) {{ console.error('Three.js load failed:', e); }});
}})();
"
/>
"""
