/* Brain 3D visualization — Three.js renderer with interactive ROI exploration.
 *
 * Features:
 * - Pulsing glow sprites at ROI centers (always face camera)
 * - Click brain region or sidebar row → camera focuses on that region
 * - Hover → tooltip anchored to 3D surface point
 * - Sidebar ↔ brain bidirectional highlighting
 */
(function() {
  function loadScript(src) {
    return new Promise(function(ok, fail) {
      if (document.querySelector('script[src="' + src + '"]')) { ok(); return; }
      var s = document.createElement("script");
      s.src = src; s.crossOrigin = "anonymous";
      s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    });
  }

  var base = "https://unpkg.com/three@0.137.0";
  var p = window.THREE ? Promise.resolve() : loadScript(base + "/build/three.min.js");
  p.then(function() {
    return window.THREE.OrbitControls ? Promise.resolve()
      : loadScript(base + "/examples/js/controls/OrbitControls.js");
  }).then(initBrain).catch(function(e) { console.error("Three.js load failed:", e); });

  function makeGlowTexture(color, size) {
    var c = document.createElement("canvas");
    c.width = c.height = size || 64;
    var ctx = c.getContext("2d");
    var g = ctx.createRadialGradient(c.width/2, c.height/2, 0, c.width/2, c.height/2, c.width/2);
    g.addColorStop(0, color);
    g.addColorStop(0.3, color + "CC");
    g.addColorStop(0.6, color + "44");
    g.addColorStop(1, "transparent");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, c.width, c.height);
    return c;
  }

  function initBrain() {
    var dataEl = document.getElementById("aal-brain-data");
    var urlEl = document.getElementById("aal-brain-mesh-url");
    var roiEl = document.getElementById("aal-brain-roi-data");
    if (!dataEl || !urlEl || !roiEl) return;

    var ACT = JSON.parse(dataEl.textContent);
    var MESH_URL = urlEl.textContent.trim();
    var ROIS = JSON.parse(roiEl.textContent);

    /* vertex → ROI lookup */
    var vertexROI = new Int8Array(20484);
    for (var i = 0; i < vertexROI.length; i++) vertexROI[i] = -1;
    for (var ri = 0; ri < ROIS.length; ri++) {
      var ranges = ROIS[ri].ranges;
      for (var rr = 0; rr < ranges.length; rr++)
        for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < 20484; vi++)
          vertexROI[vi] = ri;
    }

    /* Parse hex color to [r,g,b] 0-1 */
    function hexToRGB(hex) {
      var r = parseInt(hex.slice(1,3), 16) / 255;
      var g = parseInt(hex.slice(3,5), 16) / 255;
      var b = parseInt(hex.slice(5,7), 16) / 255;
      return [r, g, b];
    }

    /* Build per-vertex color: ROI vertices get their signature color
       scaled by activation, non-ROI vertices stay dark */
    var roiVertexColor = {}; /* vertex index → {r,g,b} of the ROI color */
    for (var ri = 0; ri < ROIS.length; ri++) {
      var rgb = hexToRGB(ROIS[ri].color);
      var ranges = ROIS[ri].ranges;
      for (var rr = 0; rr < ranges.length; rr++)
        for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < 20484; vi++)
          roiVertexColor[vi] = rgb;
    }

    function vertexColor(idx, activation) {
      var a = Math.max(0, Math.min(1, activation));
      var roi = roiVertexColor[idx];
      if (roi) {
        /* ROI vertex: cubic ramp for dramatic dark→bright contrast */
        var t = a * a * a; /* cubic — stays very dark until high activation */
        var intensity = 0.02 + t * 1.2; /* near-black at low, oversaturated at high */
        return [
          Math.min(1, roi[0] * intensity),
          Math.min(1, roi[1] * intensity),
          Math.min(1, roi[2] * intensity)
        ];
      } else {
        /* Non-ROI: near-black */
        return [0.015, 0.018, 0.025];
      }
    }

    var T = window.THREE;
    var canvas = document.getElementById("aal-brain-canvas");
    var tooltip = document.getElementById("aal-brain-tooltip");
    var focusPanel = document.getElementById("aal-brain-focus-panel");
    if (!canvas) return;

    var rect = canvas.getBoundingClientRect();
    var W = rect.width || 700, H = rect.height || 520;

    var renderer = new T.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030712, 1);
    if (T.ACESFilmicToneMapping) {
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.0;
    }

    var scene = new T.Scene();
    var camera = new T.PerspectiveCamera(32, W / H, 1, 500);
    var defaultCamPos = new T.Vector3(0, 15, 185);
    var defaultTarget = new T.Vector3(0, 0, 0);
    camera.position.copy(defaultCamPos);

    var controls = new T.OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.3;
    controls.enableZoom = false; /* zoom via slider only */
    controls.enablePan = false;
    controls.rotateSpeed = 1.0;
    controls.minPolarAngle = 0.05;          /* near-top */
    controls.maxPolarAngle = Math.PI - 0.05; /* near-bottom */
    /* No azimuthal limits — full 360 horizontal rotation */

    /* Stop auto-rotate on first user interaction */
    canvas.addEventListener("pointerdown", function() {
      controls.autoRotate = false;
    });

    /* ── Snap angles: front, left, right, top, bottom ── */
    var SNAP_ANGLES = [
      { azimuth: 0,              polar: Math.PI/2 },  /* front */
      { azimuth: Math.PI/2,      polar: Math.PI/2 },  /* left */
      { azimuth: -Math.PI/2,     polar: Math.PI/2 },  /* right */
      { azimuth: Math.PI,        polar: Math.PI/2 },  /* back */
      { azimuth: 0,              polar: 0.15 },        /* top */
      { azimuth: 0,              polar: Math.PI-0.15 } /* bottom */
    ];
    var SNAP_THRESHOLD = 0.12;

    /* Zoom slider — value 0-100, maps to distance 280 (far) → 120 (close) */
    var zoomSlider = document.getElementById("aal-brain-zoom");
    function zoomValToDist(v) { return 280 - (v / 100) * 160; } /* 0=280, 100=120 */
    function distToZoomVal(d) { return Math.round((280 - d) / 160 * 100); }
    if (zoomSlider) {
      zoomSlider.min = 0;
      zoomSlider.max = 100;
      zoomSlider.value = distToZoomVal(185); /* default distance */
      zoomSlider.addEventListener("input", function() {
        var dist = zoomValToDist(parseFloat(zoomSlider.value));
        var dir = camera.position.clone().sub(controls.target).normalize();
        camera.position.copy(controls.target).addScaledVector(dir, dist);
        controls.autoRotate = false;
      });
    }

    /* Dark moody lighting — lets ROI colors glow against dark mesh */
    scene.add(new T.AmbientLight(0x223344, 1.0));
    scene.add(new T.HemisphereLight(0x112233, 0x111122, 0.4));
    var kl = new T.DirectionalLight(0x8888AA, 0.6); kl.position.set(60,90,70); scene.add(kl);
    var fl = new T.DirectionalLight(0x445566, 0.3); fl.position.set(-50,30,80); scene.add(fl);
    var rl = new T.DirectionalLight(0x554466, 0.3); rl.position.set(-40,-30,-70); scene.add(rl);

    var raycaster = new T.Raycaster();
    var mouse = new T.Vector2();
    var brainMesh = null;
    var lastROI = -1;
    var roiCenters = [];
    var roiSprites = [];
    var clock = new T.Clock();

    /* Word map for streaming */
    var wordMapEl = document.getElementById("aal-brain-word-map");
    var WORD_MAP = wordMapEl ? JSON.parse(wordMapEl.textContent) : [];
    var wordsPanel = document.getElementById("aal-brain-words-panel");
    var wordsStream = document.getElementById("aal-words-stream");
    var wordsRoiDot = document.getElementById("aal-words-roi-dot");
    var wordsRoiName = document.getElementById("aal-words-roi-name");
    var wordsRoiDesc = document.getElementById("aal-words-roi-desc");
    var activeWordStream = null; /* timer handle */
    var activeStreamROI = -1;
    var brainPulseROI = -1;
    var brainPulseTime = 0;

    /* Focus state */
    var focusedROI = -1;
    var focusTarget = null;
    var focusCamTarget = null;
    var isAnimatingFocus = false;
    var mouseDownPos = { x: 0, y: 0 };

    fetch(MESH_URL).then(function(r) { return r.json(); }).then(function(mesh) {
      var geo = new T.BufferGeometry();
      var verts = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {
        verts[i*3] = mesh.vertices[i][0];
        verts[i*3+1] = mesh.vertices[i][1];
        verts[i*3+2] = mesh.vertices[i][2];
      }
      geo.setAttribute("position", new T.BufferAttribute(verts, 3));

      var idx = new Uint32Array(mesh.faces.length * 3);
      for (var i = 0; i < mesh.faces.length; i++) {
        idx[i*3] = mesh.faces[i][0]; idx[i*3+1] = mesh.faces[i][1]; idx[i*3+2] = mesh.faces[i][2];
      }
      geo.setIndex(new T.BufferAttribute(idx, 1));

      var cols = new Float32Array(mesh.vertices.length * 3);
      for (var i = 0; i < mesh.vertices.length; i++) {
        var a = i < ACT.length ? ACT[i] : 0;
        var c = vertexColor(i, a);
        cols[i*3] = c[0]; cols[i*3+1] = c[1]; cols[i*3+2] = c[2];
      }
      geo.setAttribute("color", new T.BufferAttribute(cols, 3));
      geo.computeVertexNormals();

      var mat = new T.MeshStandardMaterial({
        vertexColors: true, roughness: 0.5, metalness: 0.05,
        side: T.DoubleSide, emissiveIntensity: 0.6, emissive: new T.Color(0x000000)
      });
      /* Use vertex colors as emissive so ROI regions glow */
      mat.onBeforeCompile = function(shader) {
        shader.fragmentShader = shader.fragmentShader.replace(
          'vec3 totalEmissiveRadiance = emissive;',
          'vec3 totalEmissiveRadiance = vColor * 0.5;'
        );
      };
      brainMesh = new T.Mesh(geo, mat);
      brainMesh.rotation.x = -Math.PI * 0.08;
      scene.add(brainMesh);

      var wm = new T.MeshBasicMaterial({
        color: 0x6366F1, wireframe: true, transparent: true, opacity: 0.03
      });
      scene.add(new T.Mesh(geo.clone(), wm).rotation.set(brainMesh.rotation.x, 0, 0) || scene.children[scene.children.length-1]);

      /* Create ROI center positions + glow sprites */
      for (var ri = 0; ri < ROIS.length; ri++) {
        var cx=0, cy=0, cz=0, cnt=0;
        var ranges = ROIS[ri].ranges;
        for (var rr = 0; rr < ranges.length; rr++)
          for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < mesh.vertices.length; vi++) {
            cx += mesh.vertices[vi][0]; cy += mesh.vertices[vi][1]; cz += mesh.vertices[vi][2]; cnt++;
          }
        var center = cnt > 0 ? new T.Vector3(cx/cnt, cy/cnt, cz/cnt) : new T.Vector3();
        /* Apply the same rotation as the brain mesh */
        center.applyAxisAngle(new T.Vector3(1,0,0), brainMesh.rotation.x);
        roiCenters.push(center);

        /* Glow sprite */
        var tex = new T.CanvasTexture(makeGlowTexture(ROIS[ri].color, 64));
        var spriteMat = new T.SpriteMaterial({ map: tex, transparent: true, opacity: 0.9, depthWrite: false });
        var sprite = new T.Sprite(spriteMat);
        sprite.position.copy(center);
        sprite.scale.set(8, 8, 1);
        sprite.userData = { roiIndex: ri };
        scene.add(sprite);
        roiSprites.push(sprite);
      }

      /* Wire sidebar row clicks */
      var rows = document.querySelectorAll(".aal-brain-roi-row[data-roi]");
      rows.forEach(function(row) {
        row.addEventListener("click", function() {
          var key = row.getAttribute("data-roi");
          for (var ri = 0; ri < ROIS.length; ri++) {
            if (ROIS[ri].key === key) {
              focusOnROI(ri);
              streamWordsForROI(ri);
              break;
            }
          }
        });
        row.addEventListener("mouseenter", function() {
          var key = row.getAttribute("data-roi");
          for (var ri = 0; ri < ROIS.length; ri++) {
            if (ROIS[ri].key === key && roiSprites[ri]) {
              roiSprites[ri].scale.set(14, 14, 1);
              break;
            }
          }
        });
        row.addEventListener("mouseleave", function() {
          for (var ri = 0; ri < roiSprites.length; ri++)
            roiSprites[ri].scale.set(8, 8, 1);
        });
      });
    }).catch(function(e) { console.error("Brain mesh load failed:", e); });

    /* ── Focus camera on an ROI ── */
    function focusOnROI(ri) {
      if (ri < 0 || ri >= roiCenters.length) return;
      focusedROI = ri;
      controls.autoRotate = false;

      /* Camera target: ROI center. Camera position: offset along the direction from origin to ROI center */
      var dir = roiCenters[ri].clone().normalize();
      focusTarget = dir.clone().multiplyScalar(140).add(new T.Vector3(0, 10, 0));
      focusCamTarget = roiCenters[ri].clone();
      isAnimatingFocus = true;

      /* Dim other sprites */
      for (var si = 0; si < roiSprites.length; si++) {
        roiSprites[si].material.opacity = si === ri ? 1.0 : 0.15;
        roiSprites[si].scale.set(si === ri ? 14 : 6, si === ri ? 14 : 6, 1);
      }

      /* Highlight sidebar row */
      document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
      var match = document.querySelector(".aal-brain-roi-row[data-roi='" + ROIS[ri].key + "']");
      if (match) match.classList.add("aal-roi-active");

      /* Show focus panel */
      if (focusPanel) {
        var roi = ROIS[ri];
        var pct = Math.round(roi.score * 100);
        focusPanel.innerHTML =
          "<div class='aal-focus-name' style='color:" + roi.color + "'>" + roi.label + "</div>" +
          "<div class='aal-focus-score' style='color:" + roi.color + "'>" + pct + "% activation</div>" +
          "<div class='aal-focus-desc'>" + roi.desc + "</div>" +
          "<div class='aal-focus-detail'>This region activates when the AI uses " +
          (roi.key === "reward" ? "approval and validation language — making you feel good about following its advice." :
           roi.key === "amygdala" ? "urgency and threat signals — triggering your fight-or-flight response." :
           roi.key === "insula" ? "empathetic mirroring — making you feel heard and understood." :
           roi.key === "prefrontal" ? "logical framing and evidence — engaging your reasoning circuits." :
           roi.key === "temporal" ? "storytelling and metaphor — helping you find meaning in the response." :
           roi.key === "cingulate" ? "nuanced language — creating a sense of balanced, trustworthy advice." :
           "language patterns from its training data.") + "</div>" +
          "<button class='aal-focus-back' onclick='window._aalBrainUnfocus()'>Back to overview</button>";
        focusPanel.style.display = "block";
      }
    }

    /* ── Return to overview ── */
    window._aalBrainUnfocus = function() {
      focusedROI = -1;
      focusTarget = defaultCamPos.clone();
      focusCamTarget = defaultTarget.clone();
      isAnimatingFocus = true;
      controls.autoRotate = true;

      /* Restore sprites */
      for (var si = 0; si < roiSprites.length; si++) {
        roiSprites[si].material.opacity = 0.9;
        roiSprites[si].scale.set(8, 8, 1);
      }
      document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
      if (focusPanel) focusPanel.style.display = "none";

      /* Stop word stream and hide panel */
      if (activeWordStream) { clearInterval(activeWordStream); activeWordStream = null; }
      if (wordsPanel) wordsPanel.style.display = "none";
      brainPulseROI = -1;
      activeStreamROI = -1;
    };

    /* ── Click to focus ── */
    canvas.addEventListener("mousedown", function(e) {
      mouseDownPos = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener("mouseup", function(e) {
      var dx = e.clientX - mouseDownPos.x, dy = e.clientY - mouseDownPos.y;
      if (Math.sqrt(dx*dx + dy*dy) > 5) return; /* was a drag, not a click */

      var cr = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - cr.left) / cr.width) * 2 - 1;
      mouse.y = -((e.clientY - cr.top) / cr.height) * 2 + 1;

      if (!brainMesh) return;
      raycaster.setFromCamera(mouse, camera);
      var hits = raycaster.intersectObject(brainMesh);
      if (hits.length > 0) {
        var fi = hits[0].faceIndex;
        var face = brainMesh.geometry.index;
        var a = face.getX(fi*3), b = face.getX(fi*3+1), c = face.getX(fi*3+2);
        var roiIdx = -1;
        if (vertexROI[a] >= 0) roiIdx = vertexROI[a];
        else if (vertexROI[b] >= 0) roiIdx = vertexROI[b];
        else if (vertexROI[c] >= 0) roiIdx = vertexROI[c];
        if (roiIdx >= 0) { focusOnROI(roiIdx); streamWordsForROI(roiIdx); }
        else window._aalBrainUnfocus();
      } else {
        window._aalBrainUnfocus();
      }
    });

    /* ── Hover tooltip ── */
    canvas.addEventListener("mousemove", function(e) {
      var cr = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - cr.left) / cr.width) * 2 - 1;
      mouse.y = -((e.clientY - cr.top) / cr.height) * 2 + 1;
      if (!brainMesh || !tooltip) return;
      raycaster.setFromCamera(mouse, camera);
      var hits = raycaster.intersectObject(brainMesh);
      if (hits.length > 0) {
        var fi = hits[0].faceIndex;
        var face = brainMesh.geometry.index;
        var a = face.getX(fi*3), b = face.getX(fi*3+1), c = face.getX(fi*3+2);
        var roiIdx = -1;
        if (vertexROI[a] >= 0) roiIdx = vertexROI[a];
        else if (vertexROI[b] >= 0) roiIdx = vertexROI[b];
        else if (vertexROI[c] >= 0) roiIdx = vertexROI[c];
        if (roiIdx >= 0 && roiIdx < ROIS.length) {
          var roi = ROIS[roiIdx];
          var pct = Math.round(roi.score * 100);
          /* Project hit point to screen */
          var pt = hits[0].point.clone().project(camera);
          var sx = (pt.x * 0.5 + 0.5) * cr.width;
          var sy = (-pt.y * 0.5 + 0.5) * cr.height;
          tooltip.innerHTML = "<div class='aal-brain-tooltip-name' style='color:" + roi.color + "'>" + roi.label + "</div>"
            + "<div class='aal-brain-tooltip-desc'>" + roi.desc + "</div>"
            + "<div class='aal-brain-tooltip-score' style='color:" + roi.color + "'>" + pct + "% activation</div>";
          tooltip.style.display = "block";
          tooltip.style.left = sx + "px";
          tooltip.style.top = sy + "px";
          tooltip.style.borderColor = roi.color + "88";
          canvas.style.cursor = "pointer";
          if (roiIdx !== lastROI) {
            document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
            var match = document.querySelector(".aal-brain-roi-row[data-roi='" + roi.key + "']");
            if (match) match.classList.add("aal-roi-active");
            lastROI = roiIdx;
          }
        } else { hideTooltip(); }
      } else { hideTooltip(); }
    });
    function hideTooltip() {
      if (tooltip) tooltip.style.display = "none";
      canvas.style.cursor = focusedROI >= 0 ? "default" : "grab";
      if (lastROI >= 0) {
        document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
        lastROI = -1;
      }
    }
    canvas.addEventListener("mouseleave", hideTooltip);

    /* ── Word streaming for ROI exploration ── */
    function streamWordsForROI(ri) {
      if (!wordsPanel || !wordsStream || WORD_MAP.length === 0) return;
      var roi = ROIS[ri];

      /* Stop any existing stream */
      if (activeWordStream) { clearInterval(activeWordStream); activeWordStream = null; }

      /* Set up panel header */
      if (wordsRoiDot) {
        wordsRoiDot.style.background = roi.color;
        wordsRoiDot.style.boxShadow = "0 0 12px " + roi.color;
      }
      if (wordsRoiName) wordsRoiName.textContent = roi.label;
      if (wordsRoiDesc) wordsRoiDesc.textContent = roi.desc;
      wordsPanel.style.display = "block";
      wordsStream.innerHTML = "";
      activeStreamROI = ri;

      /* Stream words one by one */
      var wordIdx = 0;
      var roiKey = roi.key;

      activeWordStream = setInterval(function() {
        if (wordIdx >= WORD_MAP.length) {
          clearInterval(activeWordStream);
          activeWordStream = null;
          brainPulseROI = -1;
          return;
        }

        var w = WORD_MAP[wordIdx];
        var isMatch = w.rois && w.rois.indexOf(roiKey) >= 0;
        var span = document.createElement("span");
        span.textContent = w.word + " ";

        if (isMatch) {
          span.style.cssText = "color:" + roi.color + ";font-weight:800;text-shadow:0 0 8px " + roi.color + "66;font-size:1.2em;";
          /* Pulse the brain region */
          brainPulseROI = ri;
          brainPulseTime = clock.getElapsedTime();
        } else {
          span.style.cssText = "color:rgba(255,255,255,0.5);";
        }

        wordsStream.appendChild(span);
        /* Auto-scroll */
        wordsStream.scrollTop = wordsStream.scrollHeight;

        wordIdx++;
      }, 60); /* 60ms per word — fast enough to feel like streaming */
    }

    /* Hide word panel on unfocus */
    var origUnfocus = window._aalBrainUnfocus;

    /* ── Animation loop ── */
    (function animate() {
      requestAnimationFrame(animate);
      var elapsed = clock.getElapsedTime();

      /* Pulse ROI sprites */
      for (var si = 0; si < roiSprites.length; si++) {
        if (focusedROI >= 0 && si !== focusedROI) continue;
        var baseScale = focusedROI === si ? 14 : 8;
        /* Extra flash when a trigger word streams in */
        if (brainPulseROI === si && (elapsed - brainPulseTime) < 0.4) {
          var flash = 1.0 + 0.6 * Math.max(0, 1.0 - (elapsed - brainPulseTime) / 0.4);
          baseScale *= flash;
        }
        var pulse = baseScale * (1.0 + 0.15 * Math.sin(elapsed * 2.0 + si * 1.2));
        roiSprites[si].scale.set(pulse, pulse, 1);
      }

      /* Focus camera animation */
      if (isAnimatingFocus && focusTarget) {
        camera.position.lerp(focusTarget, 0.06);
        controls.target.lerp(focusCamTarget, 0.06);
        if (camera.position.distanceTo(focusTarget) < 0.5) {
          isAnimatingFocus = false;
          if (focusedROI < 0) controls.autoRotate = true;
        }
      }

      controls.update();

      /* Snap to canonical views when close */
      if (!controls.autoRotate && !isAnimatingFocus && focusedROI < 0) {
        var offset = camera.position.clone().sub(controls.target);
        var dist = offset.length();
        var azimuth = Math.atan2(offset.x, offset.z);
        var polar = Math.acos(Math.max(-1, Math.min(1, offset.y / dist)));

        for (var si = 0; si < SNAP_ANGLES.length; si++) {
          var sa = SNAP_ANGLES[si];
          var dA = Math.abs(azimuth - sa.azimuth);
          if (dA > Math.PI) dA = 2 * Math.PI - dA;
          var dP = Math.abs(polar - sa.polar);
          if (dA < SNAP_THRESHOLD && dP < SNAP_THRESHOLD) {
            /* Gently pull toward snap angle */
            var tgtAz = azimuth + (sa.azimuth - azimuth) * 0.08;
            var tgtPo = polar + (sa.polar - polar) * 0.08;
            var nx = dist * Math.sin(tgtPo) * Math.sin(tgtAz);
            var ny = dist * Math.cos(tgtPo);
            var nz = dist * Math.sin(tgtPo) * Math.cos(tgtAz);
            camera.position.set(
              controls.target.x + nx,
              controls.target.y + ny,
              controls.target.z + nz
            );
            break;
          }
        }
      }

      /* Keep zoom slider in sync with camera distance */
      if (zoomSlider) {
        var curDist = camera.position.clone().sub(controls.target).length();
        var expectedVal = distToZoomVal(curDist);
        if (Math.abs(parseInt(zoomSlider.value) - expectedVal) > 2) {
          zoomSlider.value = expectedVal;
        }
      }

      renderer.render(scene, camera);
    })();

    new ResizeObserver(function() {
      var r = canvas.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        W = r.width; H = r.height;
        camera.aspect = W / H;
        camera.updateProjectionMatrix();
        renderer.setSize(W, H);
      }
    }).observe(canvas.parentElement);
  }
})();
