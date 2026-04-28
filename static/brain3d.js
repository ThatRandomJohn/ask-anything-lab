/* Brain 3D visualization — loaded dynamically by brain_viz.py */
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

  function initBrain() {
    var dataEl = document.getElementById("aal-brain-data");
    var urlEl = document.getElementById("aal-brain-mesh-url");
    var roiEl = document.getElementById("aal-brain-roi-data");
    if (!dataEl || !urlEl || !roiEl) return;

    var ACT = JSON.parse(dataEl.textContent);
    var MESH_URL = urlEl.textContent.trim();
    var ROIS = JSON.parse(roiEl.textContent);

    /* Build vertex → ROI lookup */
    var vertexROI = new Int8Array(20484);
    for (var i = 0; i < vertexROI.length; i++) vertexROI[i] = -1;
    for (var ri = 0; ri < ROIS.length; ri++) {
      var ranges = ROIS[ri].ranges;
      for (var rr = 0; rr < ranges.length; rr++) {
        for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < 20484; vi++) {
          vertexROI[vi] = ri;
        }
      }
    }

    function activationColor(v) {
      v = Math.max(0, Math.min(1, v));
      var stops = [
        [0.0,  0.071, 0.098, 0.141],
        [0.15, 0.075, 0.220, 0.310],
        [0.35, 0.024, 0.714, 0.831],
        [0.55, 0.455, 0.380, 0.900],
        [0.75, 0.655, 0.545, 0.984],
        [0.90, 0.925, 0.380, 0.520],
        [1.0,  1.000, 0.700, 0.780]
      ];
      var lo = stops[0], hi = stops[stops.length - 1];
      for (var i = 0; i < stops.length - 1; i++) {
        if (v >= stops[i][0] && v <= stops[i + 1][0]) { lo = stops[i]; hi = stops[i + 1]; break; }
      }
      var t = (hi[0] - lo[0]) > 0 ? (v - lo[0]) / (hi[0] - lo[0]) : 0;
      t = t * t * (3 - 2 * t);
      return [lo[1]+t*(hi[1]-lo[1]), lo[2]+t*(hi[2]-lo[2]), lo[3]+t*(hi[3]-lo[3])];
    }

    var T = window.THREE;
    var canvas = document.getElementById("aal-brain-canvas");
    var tooltip = document.getElementById("aal-brain-tooltip");
    var calloutsEl = document.getElementById("aal-brain-callouts");
    if (!canvas) return;

    var rect = canvas.getBoundingClientRect();
    var W = rect.width || 700, H = rect.height || 520;

    var renderer = new T.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030712, 1);
    if (T.ACESFilmicToneMapping) {
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
    }

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

    var raycaster = new T.Raycaster();
    var mouse = new T.Vector2();
    var brainMesh = null;
    var lastROI = -1;
    var roiCenters = [];

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
        vertexColors: true, roughness: 0.4, metalness: 0.15, side: T.DoubleSide
      });
      brainMesh = new T.Mesh(geo, mat);
      brainMesh.rotation.x = -Math.PI * 0.08;
      scene.add(brainMesh);

      var wm = new T.MeshBasicMaterial({
        color: 0x6366F1, wireframe: true, transparent: true, opacity: 0.03
      });
      var wire = new T.Mesh(geo.clone(), wm);
      wire.rotation.x = brainMesh.rotation.x;
      scene.add(wire);

      /* Compute ROI 3D centers for callout labels */
      for (var ri = 0; ri < ROIS.length; ri++) {
        var cx=0, cy=0, cz=0, cnt=0;
        var ranges = ROIS[ri].ranges;
        for (var rr = 0; rr < ranges.length; rr++) {
          for (var vi = ranges[rr][0]; vi < ranges[rr][1] && vi < mesh.vertices.length; vi++) {
            cx += mesh.vertices[vi][0]; cy += mesh.vertices[vi][1]; cz += mesh.vertices[vi][2];
            cnt++;
          }
        }
        roiCenters.push(cnt > 0 ? new T.Vector3(cx/cnt, cy/cnt, cz/cnt) : new T.Vector3());
      }
    }).catch(function(e) { console.error("Brain mesh load failed:", e); });

    /* Hover */
    canvas.addEventListener("mousemove", function(e) {
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
        if (roiIdx >= 0 && roiIdx < ROIS.length) {
          var roi = ROIS[roiIdx];
          var pct = Math.round(roi.score * 100);
          tooltip.innerHTML = "<div class='aal-brain-tooltip-name' style='color:" + roi.color + "'>" + roi.label + "</div>"
            + "<div class='aal-brain-tooltip-desc'>" + roi.desc + "</div>"
            + "<div class='aal-brain-tooltip-score' style='color:" + roi.color + "'>" + pct + "% activation</div>";
          tooltip.style.display = "block";
          tooltip.style.left = (e.clientX - cr.left) + "px";
          tooltip.style.top = (e.clientY - cr.top) + "px";
          tooltip.style.borderColor = roi.color + "88";
          canvas.style.cursor = "pointer";
          if (roiIdx !== lastROI) {
            document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
            var match = document.querySelector(".aal-brain-roi-row[data-roi='" + roi.key + "']");
            if (match) match.classList.add("aal-roi-active");
            lastROI = roiIdx;
          }
        } else {
          hideTooltip();
        }
      } else {
        hideTooltip();
      }
    });

    function hideTooltip() {
      tooltip.style.display = "none";
      canvas.style.cursor = "grab";
      if (lastROI >= 0) {
        document.querySelectorAll(".aal-brain-roi-row").forEach(function(r) { r.classList.remove("aal-roi-active"); });
        lastROI = -1;
      }
    }
    canvas.addEventListener("mouseleave", hideTooltip);

    /* Floating callout labels */
    var calloutEls = [];
    function updateCallouts() {
      if (!brainMesh || roiCenters.length === 0) return;
      if (calloutEls.length === 0 && calloutsEl) {
        for (var ri = 0; ri < ROIS.length; ri++) {
          var el = document.createElement("div");
          el.className = "aal-brain-callout";
          el.style.animationDelay = (ri * 120) + "ms";
          el.innerHTML = "<span class='aal-brain-callout-dot' style='background:" + ROIS[ri].color
            + ";box-shadow:0 0 8px " + ROIS[ri].color + "'></span>"
            + "<span class='aal-brain-callout-line' style='background:" + ROIS[ri].color + "55'></span>"
            + "<span>" + ROIS[ri].label + "</span>";
          calloutsEl.appendChild(el);
          calloutEls.push(el);
        }
      }
      var cr = canvas.getBoundingClientRect();
      for (var ri = 0; ri < roiCenters.length && ri < calloutEls.length; ri++) {
        var pos = roiCenters[ri].clone();
        pos.applyAxisAngle(new T.Vector3(1,0,0), brainMesh.rotation.x);
        pos.project(camera);
        var x = (pos.x * 0.5 + 0.5) * cr.width;
        var y = (-pos.y * 0.5 + 0.5) * cr.height;
        if (pos.z < 1 && x > 20 && x < cr.width - 20 && y > 20 && y < cr.height - 40) {
          calloutEls[ri].style.left = x + "px";
          calloutEls[ri].style.top = y + "px";
          calloutEls[ri].style.opacity = "1";
        } else {
          calloutEls[ri].style.opacity = "0";
        }
      }
    }

    (function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
      updateCallouts();
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
