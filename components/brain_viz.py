"""Brain visualization stage — interactive 3D cortical activation viewer.

Renders a Three.js scene with the fsaverage5 brain mesh, vertex-colored by
predicted activation values. Styled to match the aurora dark theme.

Uses pre-computed demo data (Phase 1) or live TRIBE v2 predictions (Phase 2).
"""
from __future__ import annotations

import html as _html
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
    },
    "amygdala": {
        "label": "Amygdala",
        "desc": "Emotional arousal and threat detection",
        "color": "#FB7185",
    },
    "temporal": {
        "label": "Temporal Cortex",
        "desc": "Language comprehension and meaning",
        "color": "#F97316",
    },
    "insula": {
        "label": "Insula",
        "desc": "Empathy and emotional awareness",
        "color": "#06B6D4",
    },
    "cingulate": {
        "label": "Cingulate Cortex",
        "desc": "Conflict monitoring and reward processing",
        "color": "#FBBF24",
    },
    "prefrontal": {
        "label": "Prefrontal Cortex",
        "desc": "Reasoning, judgment, and decision-making",
        "color": "#A78BFA",
    },
}


def _render_roi_breakdown(roi_scores: dict) -> str:
    rows = []
    # Sort by score descending
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
              box-shadow: 0 0 10px {meta['color']};"></span>
            <span class="aal-brain-roi-label">{meta['label']}</span>
            <span class="aal-brain-roi-pct">{pct}%</span>
          </div>
          <div class="aal-brain-bar-track">
            <div class="aal-brain-bar-fill" style="width:{pct}%; background:
              linear-gradient(90deg, {meta['color']}88, {meta['color']});"></div>
          </div>
          <div class="aal-brain-roi-desc">{meta['desc']}</div>
        </div>
        """)
    return "".join(rows)


def render_brain_stage(brain_data: dict, response: str = "") -> str:
    """Render the full brain visualization stage as an HTML string.

    Args:
        brain_data: Dict with 'activations' (list of 20484 floats),
                    'roi_scores' (dict), 'status' ('live'|'demo'|'fallback')
        response:   The AI response text (for context display)
    """
    activations = brain_data.get("activations", [])
    roi_scores = brain_data.get("roi_scores", {})
    status = brain_data.get("status", "demo")

    roi_html = _render_roi_breakdown(roi_scores)

    # Serialize activations as compact JSON for embedding
    act_json = json.dumps(activations, separators=(",", ":"))

    # Mesh path for Gradio static serving
    mesh_path = os.path.join(_STATIC, "fsaverage5.json")
    mesh_src = f"/gradio_api/file={mesh_path}"

    # Status banner for demo/fallback
    status_banner = ""
    if status in ("demo", "fallback"):
        status_banner = """
        <div class="aal-brain-demo-banner">
          Reference activation &middot; live TRIBE v2 predictions coming soon
        </div>
        """

    # Step label — this becomes Step 5 in the new 8-stage flow
    step_label = "Step 5 &middot; Brain Response"

    return f"""
<div class="aal-brain-wrap">
  <div class="aal-brain-aurora">
    <div class="aal-think-blob aal-think-blob-a" style="opacity:0.18;"></div>
    <div class="aal-think-blob aal-think-blob-c" style="opacity:0.18;"></div>
    <div class="aal-think-blob aal-think-blob-b" style="opacity:0.10; top:-80px; left:35%;"></div>
  </div>

  <div class="aal-brain-inner">
    <div class="aal-brain-topbar">
      <div class="aal-brain-eyebrow-pill">
        <span class="aal-eyebrow-dot" style="background:#A78BFA; box-shadow: 0 0 12px #A78BFA;"></span>
        {step_label}
      </div>
    </div>

    <h2 class="aal-brain-title">This is your brain on AI.</h2>
    <p class="aal-brain-subtitle">
      TRIBE v2 predicts how <strong style="color:#F1F5F9;">20,484 points</strong>
      on your cortex respond to what you just read.
      The bright spots? That&rsquo;s where language becomes feeling.
    </p>
    {status_banner}

    <div class="aal-brain-grid">
      <div class="aal-brain-canvas-card aal-influence-card-entrance">
        <canvas id="aal-brain-canvas"></canvas>
        <div class="aal-brain-controls-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
        <div class="aal-brain-legend">
          <span class="aal-brain-legend-lo">Low</span>
          <div class="aal-brain-legend-bar"></div>
          <span class="aal-brain-legend-hi">High</span>
        </div>
      </div>

      <div class="aal-brain-regions-card aal-influence-card-entrance" style="animation-delay:200ms;">
        <div class="aal-brain-regions-title">Regional Activation</div>
        <div class="aal-brain-regions-subtitle">
          Predicted cortical response to the AI&rsquo;s answer
        </div>
        {roi_html}
        <div class="aal-brain-narrative">
          The AI&rsquo;s warm approval language activates reward circuits and
          the amygdala &mdash; the same regions triggered by social bonding.
          This isn&rsquo;t understanding. It&rsquo;s persuasion architecture.
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.aal-brain-wrap {{
  position: relative;
  min-height: 82vh;
  background: #06080C;
  overflow: hidden;
  padding: 0.5em 0 2em;
}}
.aal-brain-aurora {{
  position: absolute; inset: 0;
  pointer-events: none; z-index: 0;
}}
.aal-brain-inner {{
  position: relative; z-index: 2;
  max-width: 1200px; margin: 0 auto;
  padding: 1.2em 2em 0;
}}
.aal-brain-topbar {{
  margin-bottom: 0.6em;
}}
.aal-brain-eyebrow-pill {{
  display: inline-flex; align-items: center; gap: 0.5em;
  background: rgba(167,139,250,0.10);
  border: 1px solid rgba(167,139,250,0.25);
  border-radius: 999px; padding: 0.35em 1.1em;
  font-size: 0.82em; letter-spacing: 0.15em;
  text-transform: uppercase; font-weight: 700;
  color: #A78BFA;
}}
.aal-brain-title {{
  font-size: 2em; font-weight: 900;
  color: #F1F5F9; margin: 0.2em 0 0.15em;
  line-height: 1.15;
}}
.aal-brain-subtitle {{
  color: #94A3B8; font-size: 1.05em;
  max-width: 720px; line-height: 1.55;
  margin: 0 0 1em;
}}
.aal-brain-demo-banner {{
  display: inline-block;
  background: rgba(251,191,36,0.08);
  border: 1px dashed rgba(251,191,36,0.3);
  border-radius: 8px; padding: 0.4em 1em;
  font-size: 0.8em; color: #FBBF24;
  margin-bottom: 1em;
}}
.aal-brain-grid {{
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 1.4em;
  align-items: start;
}}
@media (max-width: 900px) {{
  .aal-brain-grid {{ grid-template-columns: 1fr; }}
}}
.aal-brain-canvas-card {{
  background: rgba(15,23,42,0.7);
  border: 1px solid #334155;
  border-radius: 18px;
  padding: 1em;
  position: relative;
  backdrop-filter: blur(12px);
}}
#aal-brain-canvas {{
  width: 100%; height: 420px;
  display: block; border-radius: 12px;
  background: #06080C;
}}
.aal-brain-controls-hint {{
  text-align: center; color: #64748B;
  font-size: 0.78em; margin-top: 0.6em;
  letter-spacing: 0.05em;
}}
.aal-brain-legend {{
  display: flex; align-items: center;
  justify-content: center; gap: 0.6em;
  margin-top: 0.5em;
}}
.aal-brain-legend-lo, .aal-brain-legend-hi {{
  color: #64748B; font-size: 0.75em;
  text-transform: uppercase; letter-spacing: 0.1em;
}}
.aal-brain-legend-bar {{
  width: 120px; height: 8px;
  border-radius: 4px;
  background: linear-gradient(90deg, #1E293B, #06B6D4, #A78BFA, #FB7185);
}}
.aal-brain-regions-card {{
  background: rgba(15,23,42,0.7);
  border: 1px solid #334155;
  border-radius: 18px;
  padding: 1.4em;
  backdrop-filter: blur(12px);
}}
.aal-brain-regions-title {{
  font-size: 1.1em; font-weight: 800;
  color: #F1F5F9; margin-bottom: 0.2em;
}}
.aal-brain-regions-subtitle {{
  color: #64748B; font-size: 0.82em;
  margin-bottom: 1em;
}}
.aal-brain-roi-row {{
  margin-bottom: 0.9em;
}}
.aal-brain-roi-header {{
  display: flex; align-items: center;
  gap: 0.5em; margin-bottom: 0.25em;
}}
.aal-brain-roi-dot {{
  width: 8px; height: 8px;
  border-radius: 50%; flex-shrink: 0;
}}
.aal-brain-roi-label {{
  font-size: 0.92em; font-weight: 600;
  color: #F1F5F9; flex: 1;
}}
.aal-brain-roi-pct {{
  font-size: 0.88em; font-weight: 700;
  color: #94A3B8; font-variant-numeric: tabular-nums;
}}
.aal-brain-bar-track {{
  height: 6px; background: #1E293B;
  border-radius: 3px; overflow: hidden;
}}
.aal-brain-bar-fill {{
  height: 100%; border-radius: 3px;
  transition: width 1.2s cubic-bezier(0.16,1,0.3,1);
}}
.aal-brain-roi-desc {{
  color: #64748B; font-size: 0.78em;
  margin-top: 0.15em;
}}
.aal-brain-narrative {{
  margin-top: 1.2em; padding-top: 1em;
  border-top: 1px solid #334155;
  color: #94A3B8; font-size: 0.88em;
  font-style: italic; line-height: 1.5;
}}
</style>

<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }}
}}
</script>

<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

const ACTIVATIONS = {act_json};
const MESH_URL = "{mesh_src}";

// Color stops: slate -> cyan -> purple -> rose
function activationColor(v) {{
  v = Math.max(0, Math.min(1, v));
  const stops = [
    [0.0, 0.118, 0.161, 0.231],  // #1E293B slate
    [0.33, 0.024, 0.714, 0.831], // #06B6D4 cyan
    [0.66, 0.655, 0.545, 0.984], // #A78BFA purple
    [1.0, 0.984, 0.443, 0.522],  // #FB7185 rose
  ];
  let lo = stops[0], hi = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {{
    if (v >= stops[i][0] && v <= stops[i + 1][0]) {{
      lo = stops[i]; hi = stops[i + 1];
      break;
    }}
  }}
  const t = (hi[0] - lo[0]) > 0 ? (v - lo[0]) / (hi[0] - lo[0]) : 0;
  return [
    lo[1] + t * (hi[1] - lo[1]),
    lo[2] + t * (hi[2] - lo[2]),
    lo[3] + t * (hi[3] - lo[3]),
  ];
}}

async function init() {{
  const canvas = document.getElementById('aal-brain-canvas');
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const width = rect.width || 700;
  const height = rect.height || 420;

  const renderer = new THREE.WebGLRenderer({{
    canvas, antialias: true, alpha: true,
  }});
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x06080C, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x06080C, 0.003);

  const camera = new THREE.PerspectiveCamera(35, width / height, 1, 500);
  camera.position.set(0, 20, 180);

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.6;
  controls.minDistance = 80;
  controls.maxDistance = 300;
  controls.enablePan = false;

  // Lighting — aurora-style
  const ambientLight = new THREE.AmbientLight(0x1E293B, 0.6);
  scene.add(ambientLight);

  const hemiLight = new THREE.HemisphereLight(0x06B6D4, 0xF97316, 0.4);
  scene.add(hemiLight);

  const keyLight = new THREE.DirectionalLight(0xA78BFA, 0.5);
  keyLight.position.set(50, 80, 60);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0xEC4899, 0.3);
  rimLight.position.set(-40, -20, -60);
  scene.add(rimLight);

  // Load mesh
  try {{
    const resp = await fetch(MESH_URL);
    const mesh = await resp.json();

    const geometry = new THREE.BufferGeometry();
    const verts = new Float32Array(mesh.vertices.length * 3);
    for (let i = 0; i < mesh.vertices.length; i++) {{
      verts[i * 3] = mesh.vertices[i][0];
      verts[i * 3 + 1] = mesh.vertices[i][1];
      verts[i * 3 + 2] = mesh.vertices[i][2];
    }}
    geometry.setAttribute('position', new THREE.BufferAttribute(verts, 3));

    const indices = new Uint32Array(mesh.faces.length * 3);
    for (let i = 0; i < mesh.faces.length; i++) {{
      indices[i * 3] = mesh.faces[i][0];
      indices[i * 3 + 1] = mesh.faces[i][1];
      indices[i * 3 + 2] = mesh.faces[i][2];
    }}
    geometry.setIndex(new THREE.BufferAttribute(indices, 1));

    // Vertex colors from activation data
    const colors = new Float32Array(mesh.vertices.length * 3);
    for (let i = 0; i < mesh.vertices.length; i++) {{
      const act = i < ACTIVATIONS.length ? ACTIVATIONS[i] : 0;
      const [r, g, b] = activationColor(act);
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }}
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();

    // Brain material
    const material = new THREE.MeshStandardMaterial({{
      vertexColors: true,
      roughness: 0.55,
      metalness: 0.15,
      side: THREE.DoubleSide,
    }});

    const brainMesh = new THREE.Mesh(geometry, material);
    brainMesh.rotation.x = -Math.PI * 0.1;
    scene.add(brainMesh);

    // Subtle wireframe overlay
    const wireMat = new THREE.MeshBasicMaterial({{
      color: 0x334155,
      wireframe: true,
      transparent: true,
      opacity: 0.04,
    }});
    const wireOverlay = new THREE.Mesh(geometry, wireMat);
    wireOverlay.rotation.x = brainMesh.rotation.x;
    scene.add(wireOverlay);

  }} catch (e) {{
    console.error('Brain mesh load failed:', e);
  }}

  // Animation loop
  function animate() {{
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }}
  animate();

  // Handle resize
  const ro = new ResizeObserver(() => {{
    const r = canvas.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {{
      camera.aspect = r.width / r.height;
      camera.updateProjectionMatrix();
      renderer.setSize(r.width, r.height);
    }}
  }});
  ro.observe(canvas.parentElement);
}}

// Wait for DOM and then init
if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', init);
}} else {{
  // Small delay to ensure Gradio has rendered the HTML
  setTimeout(init, 100);
}}
</script>
"""
