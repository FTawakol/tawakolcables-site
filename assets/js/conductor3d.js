/* Altawakol Cables — 3D stranded conductor (three.js). Geometry from the catalogue: ACSR 380/50 = 7 × 3.00 ST1A + 12/18/24 × 3.00 AL1. */
(function(){
  var host = document.getElementById('conductor3d'); if(!host) return;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fallback(){ host.classList.add('fallback'); }
  if(!window.WebGLRenderingContext){ fallback(); return; }
  var s = document.createElement('script'); s.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js'; s.onerror = fallback;
  s.onload = function(){ try { build(); } catch(e){ fallback(); } };
  document.head.appendChild(s);

  function build(){
    var THREE = window.THREE;
    var W = host.clientWidth, H = host.clientHeight;
    var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2)); renderer.setSize(W, H);
    renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.25;
    host.appendChild(renderer.domElement);
    var scene = new THREE.Scene();
    var cam = new THREE.PerspectiveCamera(32, W/H, 0.1, 200); cam.position.set(0, 10, 92);
    // lights: cool key, warm rim, soft fill — reads as brushed metal
    scene.add(new THREE.HemisphereLight(0xffffff, 0x3a4b89, 1.6));
    var key = new THREE.DirectionalLight(0xffffff, 2.6); key.position.set(18, 24, 30); scene.add(key);
    var rim = new THREE.DirectionalLight(0xfdb913, 0.35); rim.position.set(-30, 10, -20); scene.add(rim);
    var fill = new THREE.DirectionalLight(0x8fc4f3, 0.9); fill.position.set(-20, -10, 25); var fill2 = new THREE.DirectionalLight(0xffffff, 0.8); fill2.position.set(0, -30, 10); scene.add(fill2); scene.add(fill);

    var alu = new THREE.MeshStandardMaterial({color:0xe6eaf0, metalness:0.8, roughness:0.28});
    var steel = new THREE.MeshStandardMaterial({color:0x8a93a1, metalness:0.9, roughness:0.4});
    var d = 3.0, r = d/2;            // wire diameter mm, drawn 1:1 in scene units
    var group = new THREE.Group(); scene.add(group);

    // helix wire: radius R from axis, lay length L (mm), phase, direction +1/-1, from z0 to z1
    function wire(R, L, phase, dir, z0, z1, mat){
      var pts = [], n = Math.max(24, Math.round((z1-z0)/1.2));
      for(var i=0;i<=n;i++){ var z = z0 + (z1-z0)*i/n; var a = phase + dir * 2*Math.PI * (z / L); pts.push(new THREE.Vector3(R*Math.cos(a), R*Math.sin(a), z)); }
      var curve = new THREE.CatmullRomCurve3(pts);
      var geo = new THREE.TubeGeometry(curve, n, r, 18, false);
      var m = new THREE.Mesh(geo, mat);
      // flat cut ends
      var cap = new THREE.Mesh(new THREE.CircleGeometry(r, 18), mat); cap.position.copy(pts[pts.length-1]); cap.lookAt(pts[pts.length-1].clone().add(curve.getTangent(1))); m.add(cap);
      var cap0 = new THREE.Mesh(new THREE.CircleGeometry(r, 18), mat); cap0.position.copy(pts[0]); cap0.lookAt(pts[0].clone().sub(curve.getTangent(0))); m.add(cap0);
      return m;
    }
    // layers: [count, pitch radius, lay direction, lay length (mm), cut end z]
    var zStart = -40, layers = [
      {n:1,  R:0,      dir: 1, L:1e9, z1: 22, mat:steel},
      {n:6,  R:d,      dir:-1, L:  48, z1: 22, mat:steel},   // steel core 7 wires, left-hand
      {n:12, R:2*d,    dir: 1, L:  96, z1: 12, mat:alu},
      {n:18, R:3*d,    dir:-1, L: 150, z1:  2, mat:alu},
      {n:24, R:4*d,    dir: 1, L: 215, z1: -8, mat:alu}      // outer layer right-hand (lay ratio 12.66 × Ø27 ≈ 342 mm; shortened for the view)
    ];
    layers.forEach(function(l){ for(var i=0;i<l.n;i++){ group.add(wire(l.R, l.L, 2*Math.PI*i/l.n, l.dir, zStart, l.z1, l.mat)); } });
    group.rotation.y = -0.95; group.rotation.x = 0.12; group.position.set(2, 5, 0);

    // interaction: drag to spin, auto-rotate otherwise
    var dragging=false, px=0, py=0, vx=0.0035, vy=0, auto=!reduce;
    host.addEventListener('pointerdown', function(e){ dragging=true; px=e.clientX; py=e.clientY; host.setPointerCapture(e.pointerId); });
    host.addEventListener('pointermove', function(e){ if(!dragging) return; var dx=e.clientX-px, dy=e.clientY-py; px=e.clientX; py=e.clientY; group.rotation.y += dx*0.008; group.rotation.x += dy*0.005; vx = dx*0.002; });
    host.addEventListener('pointerup', function(){ dragging=false; }); host.addEventListener('pointercancel', function(){ dragging=false; });
    var visible=true; if('IntersectionObserver' in window){ new IntersectionObserver(function(en){ visible = en[0].isIntersecting; }).observe(host); }
    function onResize(){ W=host.clientWidth; H=host.clientHeight; renderer.setSize(W,H); cam.aspect=W/H; cam.updateProjectionMatrix(); }
    window.addEventListener('resize', onResize);
    function frame(){ requestAnimationFrame(frame); if(!visible) return; if(!dragging){ group.rotation.y += auto ? 0.0022 + vx*0.5 : 0; vx *= 0.96; } renderer.render(scene, cam); }
    if(reduce){ renderer.render(scene, cam); } else frame();
    host.classList.add('ready');
  }
})();
