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

    function activationColor(v) {
      v = Math.max(0, Math.min(1, v));
      var stops = [
        [0.0,  0.120, 0.160, 0.240],
        [0.12, 0.100, 0.300, 0.420],
        [0.30, 0.050, 0.780, 0.900],
        [0.50, 0.500, 0.440, 0.950],
        [0.70, 0.720, 0.600, 1.000],
        [0.85, 0.960, 0.440, 0.560],
        [1.0,  1.000, 0.800, 0.850]
      ];
      var lo = stops[0], hi = stops[stops.length - 1];
      for (var i = 0; i < stops.length - 1; i++)
        if (v >= stops[i][0] && v <= stops[i + 1][0]) { lo = stops[i]; hi = stops[i + 1]; break; }
      var t = (hi[0] - lo[0]) > 0 ? (v - lo[0]) / (hi[0] - lo[0]) : 0;
      t = t * t * (3 - 2 * t);
      return [lo[1]+t*(hi[1]-lo[1]), lo[2]+t*(hi[2]-lo[2]), lo[3]+t*(hi[3]-lo[3])];
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
      renderer.toneMappingExposure = 1.8;
    }

    var scene = new T.Scene();
    var camera = new T.PerspectiveCamera(32, W / H, 1, 500);
    var defaultCamPos = new T.Vector3(0, 15, 185);
    var defaultTarget = new T.Vector3(0, 0, 0);
    camera.position.copy(defaultCamPos);

    var controls = new T.OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.4;
    controls.minDistance = 90;
    controls.maxDistance = 280;
    controls.enablePan = false;

    /* Bright lighting */
    scene.add(new T.AmbientLight(0x6680AA, 1.5));
    scene.add(new T.HemisphereLight(0x06B6D4, 0xF97316, 0.8));
    var kl = new T.DirectionalLight(0xC4B5FD, 1.2); kl.position.set(60,90,70); scene.add(kl);
    var fl = new T.DirectionalLight(0x22D3EE, 0.6); fl.position.set(-50,30,80); scene.add(fl);
    var rl = new T.DirectionalLight(0xF472B6, 0.7); rl.position.set(-40,-30,-70); scene.add(rl);
    var ul = new T.PointLight(0xFBBF24, 0.5, 300); ul.position.set(0,-80,30); scene.add(ul);
    var topL = new T.DirectionalLight(0xFFFFFF, 0.4); topL.position.set(0,100,0); scene.add(topL);

    var raycaster = new T.Raycaster();
    var mouse = new T.Vector2();
    var brainMesh = null;
    var lastROI = -1;
    var roiCenters = [];
    var roiSprites = [];
    var clock = new T.Clock();

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
        var c = activationColor(a);
        cols[i*3] = c[0]; cols[i*3+1] = c[1]; cols[i*3+2] = c[2];
      }
      geo.setAttribute("color", new T.BufferAttribute(cols, 3));
      geo.computeVertexNormals();

      var mat = new T.MeshStandardMaterial({
        vertexColors: true, roughness: 0.3, metalness: 0.1,
        side: T.DoubleSide, emissiveIntensity: 0.15, emissive: new T.Color(0x1a1a2e)
      });
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
            if (ROIS[ri].key === key) { focusOnROI(ri); break; }
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
        if (roiIdx >= 0) focusOnROI(roiIdx);
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

    /* ── Animation loop ── */
    (function animate() {
      requestAnimationFrame(animate);
      var elapsed = clock.getElapsedTime();

      /* Pulse ROI sprites */
      for (var si = 0; si < roiSprites.length; si++) {
        if (focusedROI >= 0 && si !== focusedROI) continue;
        var baseScale = focusedROI === si ? 14 : 8;
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
        controls.update();
      } else {
        controls.update();
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
