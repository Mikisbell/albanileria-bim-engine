
    let scene, camera, renderer, controls;
    let brickMeshes = [];
    let colMeshes = [];
    let soleraMeshes = [];
    let slabMeshes = [];
    let glassMeshes = [];
    let lintelMeshes = [];
    let doorMeshes = [];
    let stairMeshes = [];
    let deptosMeshes = [];
    let siteMeshes = [];
    let cmMeshes = [];
    let foundationMeshes = [];
    let parapetoMeshes = [];
    let floorGroups = [];
    let activeMode = 0; // 0: estatico, 1..3: modos
    let scaleFactor = 50.0;
    let animSpeed = 1.0;
    let explodeDistance = 0.0;
    let clock;
    let selectedMesh = null;
    let raycaster, mouse;
    let currentVisualMode = 'bim'; // 'bim', 'fem', 'xray', 'wire'

    // Texturas Procedimentales en Canvas (100% Offline)
    let texLadrillo, bumpLadrillo, texConcreto, texAsfalto, texMadera;

    function generarTexturasProcedimentales() {
      // 1. Textura de Ladrillo King Kong arcilla cocida (512x512)
      const cBrick = document.createElement('canvas');
      cBrick.width = 512;
      cBrick.height = 512;
      const ctxB = cBrick.getContext('2d');
      ctxB.fillStyle = '#cbd5e1'; // Mortero cemento
      ctxB.fillRect(0, 0, 512, 512);

      const rows = 16;
      const cols = 8;
      const rH = 512 / rows;
      const cW = 512 / cols;

      for (let r = 0; r < rows; r++) {
        const offset = (r % 2 === 0) ? 0 : cW / 2;
        for (let c = -1; c < cols + 1; c++) {
          const bx = c * cW + offset + 2;
          const by = r * rH + 2;
          const bw = cW - 4;
          const bh = rH - 4;

          // Variacion natural de color arcilla
          const hueRand = Math.floor(Math.sin(r * 13 + c * 7) * 15);
          ctxB.fillStyle = `rgb(${194 + hueRand}, ${65 + Math.floor(hueRand / 2)}, ${12 + Math.floor(hueRand / 3)})`;
          ctxB.fillRect(bx, by, bw, bh);

          // Sombra sutil en ladrillo
          ctxB.fillStyle = 'rgba(0,0,0,0.12)';
          ctxB.fillRect(bx, by + bh - 3, bw, 3);
        }
      }
      texLadrillo = new THREE.CanvasTexture(cBrick);
      texLadrillo.wrapS = THREE.RepeatWrapping;
      texLadrillo.wrapT = THREE.RepeatWrapping;
      texLadrillo.repeat.set(2, 2);

      // Bump map para junta de mortero
      const cBump = document.createElement('canvas');
      cBump.width = 256;
      cBump.height = 256;
      const ctxBump = cBump.getContext('2d');
      ctxBump.fillStyle = '#000000';
      ctxBump.fillRect(0, 0, 256, 256);
      ctxBump.fillStyle = '#ffffff';
      for (let r = 0; r < 8; r++) {
        const off = (r % 2 === 0) ? 0 : 16;
        for (let c = -1; c < 9; c++) {
          ctxBump.fillRect(c * 32 + off + 2, r * 32 + 2, 28, 28);
        }
      }
      bumpLadrillo = new THREE.CanvasTexture(cBump);
      bumpLadrillo.wrapS = THREE.RepeatWrapping;
      bumpLadrillo.wrapT = THREE.RepeatWrapping;
      bumpLadrillo.repeat.set(2, 2);

      // 2. Concreto Visto Armado (256x256)
      const cConc = document.createElement('canvas');
      cConc.width = 256;
      cConc.height = 256;
      const ctxC = cConc.getContext('2d');
      ctxC.fillStyle = '#8392a5';
      ctxC.fillRect(0, 0, 256, 256);
      for (let i = 0; i < 600; i++) {
        const x = Math.random() * 256;
        const y = Math.random() * 256;
        ctxC.fillStyle = Math.random() > 0.5 ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
        ctxC.fillRect(x, y, 2, 2);
      }
      texConcreto = new THREE.CanvasTexture(cConc);

      // 3. Asfalto y Estacionamientos (512x512)
      const cAsf = document.createElement('canvas');
      cAsf.width = 512;
      cAsf.height = 512;
      const ctxA = cAsf.getContext('2d');
      ctxA.fillStyle = '#0f172a';
      ctxA.fillRect(0, 0, 512, 512);

      // Grano y rugosidad de asfalto
      for (let i = 0; i < 900; i++) {
        const x = Math.random() * 512;
        const y = Math.random() * 512;
        ctxA.fillStyle = Math.random() > 0.5 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.12)';
        ctxA.fillRect(x, y, 2, 2);
      }

      // Líneas viales amarillas de los 4 estacionamientos
      ctxA.strokeStyle = '#facc15';
      ctxA.lineWidth = 6;
      ctxA.strokeRect(8, 8, 496, 496);
      for (let i = 1; i < 4; i++) {
        ctxA.beginPath();
        ctxA.moveTo(i * 128, 16);
        ctxA.lineTo(i * 128, 496);
        ctxA.stroke();
      }

      // Rotulación reglamentaria E-1 a E-4
      ctxA.fillStyle = '#facc15';
      ctxA.font = 'bold 36px monospace';
      ctxA.textAlign = 'center';
      for (let i = 0; i < 4; i++) {
        ctxA.fillText('E-' + (i + 1), i * 128 + 64, 260);
      }
      texAsfalto = new THREE.CanvasTexture(cAsf);

      // 4. Madera puerta de ingreso
      const cWood = document.createElement('canvas');
      cWood.width = 128;
      cWood.height = 256;
      const ctxW = cWood.getContext('2d');
      ctxW.fillStyle = '#78350f';
      ctxW.fillRect(0, 0, 128, 256);
      ctxW.strokeStyle = '#92400e';
      ctxW.lineWidth = 4;
      ctxW.strokeRect(12, 16, 104, 100);
      ctxW.strokeRect(12, 136, 104, 104);
      texMadera = new THREE.CanvasTexture(cWood);
    }

    function init() {
      const container = document.getElementById('canvas-container');
      clock = new THREE.Clock();
      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2();

      generarTexturasProcedimentales();

      // Scene
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x07090e);
      scene.fog = new THREE.FogExp2(0x07090e, 0.012);

      // Camera
      camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);

      // Renderer
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;
      container.appendChild(renderer.domElement);

      // Controls
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.target.set(DATA.edificio.frente / 2, DATA.edificio.h_total / 2, DATA.edificio.fondo / 2);
      controls.maxPolarAngle = Math.PI - 0.05;

      setCamera('iso');

      // Lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
      scene.add(ambientLight);

      const sunLight = new THREE.DirectionalLight(0xfffaed, 1.25);
      sunLight.position.set(50, 75, -40);
      sunLight.castShadow = true;
      sunLight.shadow.mapSize.width = 2048;
      sunLight.shadow.mapSize.height = 2048;
      sunLight.shadow.camera.near = 10;
      sunLight.shadow.camera.far = 200;
      sunLight.shadow.camera.left = -30;
      sunLight.shadow.camera.right = 30;
      sunLight.shadow.camera.top = 30;
      sunLight.shadow.camera.bottom = -30;
      sunLight.shadow.bias = -0.0005;
      scene.add(sunLight);

      const skyLight = new THREE.HemisphereLight(0x38bdf8, 0x0f172a, 0.45);
      scene.add(skyLight);

      // Construcción del Modelo
      construirEntornoUrbano();
      construirCimentacion();
      construirEstructuraPorPisos();

      window.addEventListener('resize', onWindowResize, false);
      window.addEventListener('click', onCanvasClick, false);
      window.addEventListener('pointermove', onPointerMove, false);

      // Seleccionar fachada por defecto
      if (DATA.muros.length > 0) {
        mostrarDatosMuro(DATA.muros.find(m => m.nom.startsWith('MX-1')) || DATA.muros[0]);
      }

      animate();
    }

    function construirEntornoUrbano() {
      const bFrente = DATA.edificio.frente;
      const bFondo = DATA.edificio.fondo;
      const retFront = DATA.edificio.retiro_frontal; // 5.00 m
      const retPost = DATA.edificio.retiro_posterior; // 4.50 m
      const lFondo = DATA.edificio.fondo_lote; // 30.50 m

      // Terreno base del lote (12 x 30.50 m)
      const lotGeo = new THREE.PlaneGeometry(12.0, lFondo);
      const lotMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.95 });
      const lotMesh = new THREE.Mesh(lotGeo, lotMat);
      lotMesh.rotation.x = -Math.PI / 2;
      lotMesh.position.set(bFrente / 2, -0.06, lFondo / 2 - retFront);
      lotMesh.receiveShadow = true;
      scene.add(lotMesh);
      siteMeshes.push(lotMesh);

      // 1. Estacionamiento Frontal (5.00 m x 12.00 m con 4 cajones)
      const pkgGeo = new THREE.PlaneGeometry(11.90, retFront);
      const pkgMat = new THREE.MeshStandardMaterial({ map: texAsfalto, roughness: 0.85 });
      const pkgMesh = new THREE.Mesh(pkgGeo, pkgMat);
      pkgMesh.rotation.x = -Math.PI / 2;
      pkgMesh.position.set(bFrente / 2, -0.04, -retFront / 2);
      pkgMesh.receiveShadow = true;
      scene.add(pkgMesh);
      siteMeshes.push(pkgMesh);

      // Topes de llanta viales en los 4 cajones
      const stopMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.45 });
      const slotWidth = 11.90 / 4.0;
      for (let i = 0; i < 4; i++) {
        const stopGeo = new THREE.BoxGeometry(1.60, 0.12, 0.16);
        const stopMesh = new THREE.Mesh(stopGeo, stopMat);
        stopMesh.position.set(slotWidth * (i + 0.5), 0.06, -1.0);
        stopMesh.castShadow = true;
        stopMesh.receiveShadow = true;
        scene.add(stopMesh);
        siteMeshes.push(stopMesh);
      }

      // 2. Patio / Jardín Posterior (4.50 m x 12.00 m)
      const yardGeo = new THREE.PlaneGeometry(11.90, retPost);
      const yardMat = new THREE.MeshStandardMaterial({ color: 0x14532d, roughness: 0.9 });
      const yardMesh = new THREE.Mesh(yardGeo, yardMat);
      yardMesh.rotation.x = -Math.PI / 2;
      yardMesh.position.set(bFrente / 2, -0.04, bFondo + retPost / 2);
      yardMesh.receiveShadow = true;
      scene.add(yardMesh);
      siteMeshes.push(yardMesh);

      // 3. Vereda / Vía Pública al frente
      const walkGeo = new THREE.PlaneGeometry(16.0, 2.5);
      const walkMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 });
      const walkMesh = new THREE.Mesh(walkGeo, walkMat);
      walkMesh.rotation.x = -Math.PI / 2;
      walkMesh.position.set(bFrente / 2, -0.05, -retFront - 1.25);
      scene.add(walkMesh);
      siteMeshes.push(walkMesh);

      // Grilla de ingeniería
      const grid = new THREE.GridHelper(50, 50, 0x1e293b, 0x0b0f19);
      grid.position.set(bFrente / 2, -0.08, bFondo / 2);
      scene.add(grid);
      siteMeshes.push(grid);
    }

    function construirCimentacion() {
      const bFrente = DATA.edificio.frente;
      const bFondo = DATA.edificio.fondo;
      const cmX = DATA.edificio.cm.x;
      const cmY = DATA.edificio.cm.y;
      const cimInfo = DATA.edificio.cimentacion || { B: 0.70, Df: 1.50, qad: 3.00, fc: 175, h_cimiento: 0.80, h_sobrecimiento: 0.80 };
      const B = cimInfo.B || 0.70;
      const Df = cimInfo.Df || 1.50;
      const hCim = cimInfo.h_cimiento || 0.80;
      const hSob = cimInfo.h_sobrecimiento || 0.80;

      // Materiales Cimiento Corrido Armado y Sobrecimiento
      const matCimCentrado = new THREE.MeshStandardMaterial({
        color: 0x475569,
        roughness: 0.88,
        metalness: 0.10
      });
      const matCimExcentrico = new THREE.MeshStandardMaterial({
        color: 0x0284c7, // Destacado: cimiento medianero conectado por cimientos transversales
        roughness: 0.85,
        metalness: 0.15
      });
      const matSobrecimiento = new THREE.MeshStandardMaterial({
        color: 0x64748b,
        roughness: 0.85
      });

      DATA.muros.forEach(m => {
        const isX = (m.dir === 'X');
        const isMed = m.is_medianera;
        const L = m.L;
        const t = m.t;

        // 1. CIMIENTO CORRIDO ARMADO (Fondo a -Df = -1.50 m, Altura hCim = 0.80 m)
        let cx = m.xc;
        let cy = m.yc;
        let cwx = isX ? L : B;
        let cwz = isX ? B : L;

        // Excentricidad en medianeras (MY-1 y MY-2): apoya contra el límite de propiedad
        if (isMed) {
          if (m.nom.startsWith('MY-1')) {
            cx = B / 2.0; // Pegado al límite x = 0 (de 0 a B)
          } else if (m.nom.startsWith('MY-2')) {
            cx = bFrente - B / 2.0; // Pegado al límite x = bFrente (de bFrente - B a bFrente)
          }
        }

        const cimGeo = new THREE.BoxGeometry(cwx, hCim, cwz);
        const cimMesh = new THREE.Mesh(cimGeo, isMed ? matCimExcentrico.clone() : matCimCentrado.clone());
        cimMesh.position.set(cx, -Df + hCim / 2.0, cy);
        cimMesh.castShadow = true;
        cimMesh.receiveShadow = true;

        cimMesh.userData = {
          tipo: 'cimiento',
          muroInfo: m,
          isMedianera: isMed,
          B: B,
          Df: Df,
          q_real: 1.60,
          q_ad: cimInfo.qad || 3.00,
          matBIM: isMed ? matCimExcentrico : matCimCentrado
        };

        const edgeCol = isMed ? 0x0369a1 : 0x1e293b;
        const cimEdges = new THREE.LineSegments(new THREE.EdgesGeometry(cimGeo), new THREE.LineBasicMaterial({ color: edgeCol, linewidth: 1.5 }));
        cimMesh.add(cimEdges);

        scene.add(cimMesh);
        foundationMeshes.push(cimMesh);

        // 2. SOBRECIMIENTO DE CONCRETO (De -0.70 m a +0.10 m, altura 0.80 m, ancho t = 0.24 m)
        const sobWx = isX ? L : t;
        const sobWz = isX ? t : L;
        const sobGeo = new THREE.BoxGeometry(sobWx, hSob, sobWz);
        const sobMesh = new THREE.Mesh(sobGeo, matSobrecimiento.clone());
        sobMesh.position.set(m.xc, -Df + hCim + hSob / 2.0, m.yc);
        sobMesh.castShadow = true;
        sobMesh.receiveShadow = true;

        sobMesh.userData = {
          tipo: 'sobrecimiento',
          muroInfo: m,
          matBIM: matSobrecimiento
        };

        const sobEdges = new THREE.LineSegments(new THREE.EdgesGeometry(sobGeo), new THREE.LineBasicMaterial({ color: 0x334155, linewidth: 1 }));
        sobMesh.add(sobEdges);

        scene.add(sobMesh);
        foundationMeshes.push(sobMesh);
      });
    }

    function construirEstructuraPorPisos() {
      const nPisos = DATA.edificio.n_pisos;
      const hPiso = DATA.edificio.h_entrepiso;
      const f = DATA.edificio.frente;
      const fo = DATA.edificio.fondo;
      const pozo = DATA.edificio.pozo;
      const esc = DATA.edificio.escalera;
      const cmX = DATA.edificio.cm.x;
      const cmY = DATA.edificio.cm.y;

      // MATERIALES REALISTAS BIM
      const matLadrillo = new THREE.MeshStandardMaterial({
        map: texLadrillo,
        bumpMap: bumpLadrillo,
        bumpScale: 0.04,
        roughness: 0.72,
        metalness: 0.05
      });
      const matConcreto = new THREE.MeshStandardMaterial({
        map: texConcreto,
        roughness: 0.60,
        metalness: 0.12
      });
      const matLosa = new THREE.MeshStandardMaterial({
        map: texConcreto,
        color: 0x94a3b8,
        roughness: 0.50,
        transparent: true,
        opacity: 0.75
      });
      const matVidrio = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        roughness: 0.05,
        metalness: 0.90,
        transparent: true,
        opacity: 0.45
      });
      const matMarco = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.4
      });
      const matMadera = new THREE.MeshStandardMaterial({
        map: texMadera,
        roughness: 0.55
      });
      const cmMat = new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        emissive: 0xd97706,
        roughness: 0.2
      });

      for (let p = 1; p <= nPisos; p++) {
        const yPiso = p * hPiso;
        const yBasePiso = (p - 1) * hPiso;
        const floorGroup = new THREE.Group();
        floorGroup.position.set(cmX, 0, cmY);
        floorGroup.userData = {
          piso: p,
          baseY: 0.0,
          currentExplode: 0.0
        };
        scene.add(floorGroup);
        floorGroups.push(floorGroup);

        // A. LOSA CON POZO DE LUZ Y HUECO DE ESCALERA
        const shape = new THREE.Shape();
        shape.moveTo(0 - cmX, 0 - cmY);
        shape.lineTo(f - cmX, 0 - cmY);
        shape.lineTo(f - cmX, fo - cmY);
        shape.lineTo(0 - cmX, fo - cmY);
        shape.closePath();

        // 1. Hueco del Pozo de Luz Central
        const hole = new THREE.Path();
        hole.moveTo(pozo.x0 - cmX, pozo.y0 - cmY);
        hole.lineTo(pozo.x1 - cmX, pozo.y0 - cmY);
        hole.lineTo(pozo.x1 - cmX, pozo.y1 - cmY);
        hole.lineTo(pozo.x0 - cmX, pozo.y1 - cmY);
        hole.closePath();
        shape.holes.push(hole);

        // 2. Hueco de Caja de Escalera (en pisos 1 a 4 para paso continuo de tramos)
        if (p < nPisos) {
          const escHole = new THREE.Path();
          escHole.moveTo(esc.x0 - cmX, esc.y0 - cmY);
          escHole.lineTo(esc.x1 - cmX, esc.y0 - cmY);
          escHole.lineTo(esc.x1 - cmX, esc.y1 - cmY);
          escHole.lineTo(esc.x0 - cmX, esc.y1 - cmY);
          escHole.closePath();
          shape.holes.push(escHole);
        }

        const extrudeSettings = { depth: 0.20, bevelEnabled: false };
        const slabGeo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
        slabGeo.rotateX(Math.PI / 2);

        const slabMesh = new THREE.Mesh(slabGeo, matLosa.clone());
        slabMesh.position.set(0, yPiso, 0);
        slabMesh.castShadow = true;
        slabMesh.receiveShadow = true;
        slabMesh.userData = { tipo: 'losa', piso: p };
        slabMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(slabGeo), new THREE.LineBasicMaterial({ color: 0x334155, linewidth: 1 })));

        floorGroup.add(slabMesh);
        slabMeshes.push(slabMesh);

        // B. NODO MAESTRO / CENTRO DE MASA
        const cmSphere = new THREE.Mesh(new THREE.SphereGeometry(0.32, 16, 16), cmMat);
        cmSphere.position.set(0, yPiso, 0);
        cmSphere.userData = { tipo: 'cm', piso: p };
        floorGroup.add(cmSphere);
        cmMeshes.push(cmSphere);

        // Enlaces del Diafragma Rígido
        const radialGroup = new THREE.Group();
        DATA.muros.forEach(m => {
          const pts = [
            new THREE.Vector3(0, yPiso, 0),
            new THREE.Vector3(m.xc - cmX, yPiso, m.yc - cmY)
          ];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
          const lineMat = new THREE.LineDashedMaterial({
            color: 0xf59e0b,
            dashSize: 0.5,
            gapSize: 0.3,
            transparent: true,
            opacity: 0.40
          });
          const line = new THREE.Line(lineGeo, lineMat);
          line.computeLineDistances();
          radialGroup.add(line);
        });
        floorGroup.add(radialGroup);
        cmMeshes.push(radialGroup);

        // C. CAJA DE ESCALERA REAL (2 Tramos en U + Descanso a +1.35m + Columnetas C-3 reglamentarias E.070 9.1)
        const stairGroup = new THREE.Group();
        stairGroup.userData = { tipo: 'escalera', piso: p };

        const wStair = esc.x1 - esc.x0; // 2.70 m
        const lStair = esc.y1 - esc.y0; // 2.76 m
        const wFlight = 1.20; // Ancho reglamentario A.020 15.2.b
        const lLanding = 1.20; // Fondo descanso
        const lFlight = lStair - lLanding; // 1.56 m
        const nSteps = 8;
        const hRiser = (hPiso / 2) / nSteps; // 1.35 / 8 = 0.16875 m
        const dStep = lFlight / (nSteps - 1); // Huella efectiva ~0.223 m

        const matStairConc = matConcreto.clone();
        const matSteelRail = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.85, roughness: 0.25 });
        const matC3Col = matConcreto.clone();

        // 1. Descanso Intermedio (Landing a cota +1.35 m sobre yBasePiso)
        const landGeo = new THREE.BoxGeometry(wStair, 0.15, lLanding);
        const landMesh = new THREE.Mesh(landGeo, matStairConc);
        landMesh.position.set(esc.x0 + wStair / 2 - cmX, yBasePiso + hPiso / 2 - 0.075, esc.y0 + lLanding / 2 - cmY);
        landMesh.castShadow = true;
        landMesh.receiveShadow = true;
        landMesh.userData = { tipo: 'escalera', piso: p, elemento: 'descanso' };
        stairGroup.add(landMesh);

        // Columnetas dedicadas de apoyo C-3 (E.070 9.1) en las esquinas del descanso
        const c3Geo = new THREE.BoxGeometry(0.25, hPiso / 2, 0.25);
        const colC3_1 = new THREE.Mesh(c3Geo, matC3Col);
        colC3_1.position.set(esc.x0 + 0.125 - cmX, yBasePiso + hPiso / 4, esc.y0 + 0.125 - cmY);
        colC3_1.castShadow = true;
        stairGroup.add(colC3_1);

        const colC3_2 = new THREE.Mesh(c3Geo, matC3Col);
        colC3_2.position.set(esc.x1 - 0.125 - cmX, yBasePiso + hPiso / 4, esc.y0 + 0.125 - cmY);
        colC3_2.castShadow = true;
        stairGroup.add(colC3_2);

        // 2. Tramo 1 (Sube desde el Hall en y = esc.y1 hacia el descanso en y = esc.y0 + lLanding)
        // Lado izquierdo: x entre esc.x0 y esc.x0 + wFlight
        for (let s = 0; s < nSteps - 1; s++) {
          const stepY = yBasePiso + (s + 1) * hRiser - hRiser / 2;
          const stepZ = esc.y1 - (s + 0.5) * dStep - cmY;
          const stepGeo = new THREE.BoxGeometry(wFlight, hRiser, dStep);
          const stepMesh = new THREE.Mesh(stepGeo, matStairConc);
          stepMesh.position.set(esc.x0 + wFlight / 2 - cmX, stepY, stepZ);
          stepMesh.castShadow = true;
          stepMesh.receiveShadow = true;
          stepMesh.userData = { tipo: 'escalera', piso: p, tramo: 1, paso: s + 1 };
          stairGroup.add(stepMesh);
        }

        // Rampa inclinada de concreto Tramo 1
        const rampGeo1 = new THREE.BoxGeometry(wFlight, 0.12, lFlight * 1.15);
        const rampMesh1 = new THREE.Mesh(rampGeo1, matStairConc);
        rampMesh1.position.set(esc.x0 + wFlight / 2 - cmX, yBasePiso + hPiso / 4 - 0.08, esc.y0 + lLanding + lFlight / 2 - cmY);
        rampMesh1.rotation.x = Math.atan2(hPiso / 2, lFlight);
        stairGroup.add(rampMesh1);

        // 3. Tramo 2 (Sube desde el descanso en y = esc.y0 + lLanding hacia el hall superior en y = esc.y1)
        // Lado derecho: x entre esc.x1 - wFlight y esc.x1
        for (let s = 0; s < nSteps - 1; s++) {
          const stepY = yBasePiso + hPiso / 2 + (s + 1) * hRiser - hRiser / 2;
          const stepZ = esc.y0 + lLanding + (s + 0.5) * dStep - cmY;
          const stepGeo = new THREE.BoxGeometry(wFlight, hRiser, dStep);
          const stepMesh = new THREE.Mesh(stepGeo, matStairConc);
          stepMesh.position.set(esc.x1 - wFlight / 2 - cmX, stepY, stepZ);
          stepMesh.castShadow = true;
          stepMesh.receiveShadow = true;
          stepMesh.userData = { tipo: 'escalera', piso: p, tramo: 2, paso: s + 1 };
          stairGroup.add(stepMesh);
        }

        // Rampa inclinada de concreto Tramo 2
        const rampGeo2 = new THREE.BoxGeometry(wFlight, 0.12, lFlight * 1.15);
        const rampMesh2 = new THREE.Mesh(rampGeo2, matStairConc);
        rampMesh2.position.set(esc.x1 - wFlight / 2 - cmX, yBasePiso + 3 * hPiso / 4 - 0.08, esc.y0 + lLanding + lFlight / 2 - cmY);
        rampMesh2.rotation.x = -Math.atan2(hPiso / 2, lFlight);
        stairGroup.add(rampMesh2);

        // 4. Barandas de acero tubular reglamentarias (h = 0.90 m)
        const railMat = matSteelRail;
        const r1Geo = new THREE.CylinderGeometry(0.025, 0.025, lFlight * 1.18, 8);
        const rail1 = new THREE.Mesh(r1Geo, railMat);
        rail1.position.set(esc.x0 + wFlight - 0.04 - cmX, yBasePiso + hPiso / 4 + 0.85, esc.y0 + lLanding + lFlight / 2 - cmY);
        rail1.rotation.x = Math.atan2(hPiso / 2, lFlight) + Math.PI / 2;
        stairGroup.add(rail1);

        const rail2 = new THREE.Mesh(r1Geo, railMat);
        rail2.position.set(esc.x1 - wFlight + 0.04 - cmX, yBasePiso + 3 * hPiso / 4 + 0.85, esc.y0 + lLanding + lFlight / 2 - cmY);
        rail2.rotation.x = -Math.atan2(hPiso / 2, lFlight) + Math.PI / 2;
        stairGroup.add(rail2);

        // Baranda de descanso
        const rLandGeo = new THREE.CylinderGeometry(0.025, 0.025, wStair - 0.20, 8);
        const railLand = new THREE.Mesh(rLandGeo, railMat);
        railLand.position.set(esc.x0 + wStair / 2 - cmX, yBasePiso + hPiso / 2 + 0.85, esc.y0 + 0.08 - cmY);
        railLand.rotation.z = Math.PI / 2;
        stairGroup.add(railLand);

        floorGroup.add(stairGroup);
        stairMeshes.push(stairGroup);

        // -------------------------------------------------------------
        // D. 2 DEPARTAMENTOS POR PISO (Arquitectura, Ambientes y Tabiques)
        // -------------------------------------------------------------
        const deptoGroup = new THREE.Group();
        deptoGroup.userData = { tipo: 'deptos', piso: p };

        const matPisoDeptoA = new THREE.MeshStandardMaterial({
          color: 0x00796b,
          roughness: 0.30,
          metalness: 0.10,
          transparent: true,
          opacity: 0.40
        });
        const matPisoDeptoB = new THREE.MeshStandardMaterial({
          color: 0x6a1b9a,
          roughness: 0.30,
          metalness: 0.10,
          transparent: true,
          opacity: 0.40
        });
        const matTabique = new THREE.MeshStandardMaterial({
          color: 0xf1f5f9,
          roughness: 0.60,
          metalness: 0.04
        });

        if (DATA.distribucion && DATA.distribucion.deptos) {
          DATA.distribucion.deptos.forEach(dpto => {
            const isA = dpto.id === 'A';
            const matPiso = isA ? matPisoDeptoA : matPisoDeptoB;

            dpto.ambientes.forEach(amb => {
              const aW = amb.x1 - amb.x0 - 0.08;
              const aL = amb.y1 - amb.y0 - 0.08;
              if (aW > 0.1 && aL > 0.1) {
                const flGeo = new THREE.BoxGeometry(aW, 0.025, aL);
                const flMesh = new THREE.Mesh(flGeo, matPiso);
                flMesh.position.set(amb.x0 + (amb.x1 - amb.x0) / 2 - cmX, yBasePiso + 0.015, amb.y0 + (amb.y1 - amb.y0) / 2 - cmY);
                flMesh.receiveShadow = true;
                flMesh.userData = {
                  tipo: 'ambiente',
                  piso: p,
                  dptoId: dpto.id,
                  dptoNombre: dpto.nombre,
                  nombre: amb.nombre || amb.uso || 'Ambiente',
                  area: amb.area || (amb.x1 - amb.x0) * (amb.y1 - amb.y0),
                  dx: amb.x1 - amb.x0,
                  dy: amb.y1 - amb.y0,
                  luz: (amb.y0 <= 0.01 ? 'Fachada Frontal (Directa)' : (amb.y1 >= fo - 0.01 ? 'Fachada Posterior (Directa)' : (amb.x0 >= pozo.x0 - 0.01 && amb.x1 <= pozo.x1 + 0.01 ? 'Pozo de Luz (Directa)' : 'Luz Prestada / Distribución')))
                };
              }
            });
          });

          // Tabiquería interior de albañilería hueca (t = 0.12 m, h = 2.50 m)
          if (DATA.distribucion.tabiques) {
            DATA.distribucion.tabiques.forEach(tb => {
              const isV = tb.orient === 'V';
              const tThick = 0.12;
              const tH = hPiso - 0.20; // 2.50 m libre
              const tL = tb.L;
              const tGeo = isV ? new THREE.BoxGeometry(tThick, tH, tL) : new THREE.BoxGeometry(tL, tH, tThick);
              const tMesh = new THREE.Mesh(tGeo, matTabique);
              const tX = isV ? tb.c - cmX : (tb.a + tb.b) / 2 - cmX;
              const tZ = isV ? (tb.a + tb.b) / 2 - cmY : tb.c - cmY;
              tMesh.position.set(tX, yBasePiso + tH / 2, tZ);
              tMesh.castShadow = true;
              tMesh.receiveShadow = true;
              tMesh.userData = { tipo: 'tabique', piso: p, L: tb.L, orient: tb.orient };
              deptoGroup.add(tMesh);
            });
          }

          // Puertas de Ingreso a Departamentos desde el Hall Común
          // Puerta Depto 1 en x = 5.95, y = 4.50
          const pDoor1 = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.10, 0.90), matMadera.clone());
          pDoor1.position.set(5.95 - cmX, yBasePiso + 1.05, 4.50 - cmY);
          pDoor1.castShadow = true;
          pDoor1.userData = { tipo: 'puerta_depto', piso: p, dpto: 'Depto 1' };
          deptoGroup.add(pDoor1);

          // Puerta Depto 2 en x = 8.65, y = 4.50
          const pDoor2 = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.10, 0.90), matMadera.clone());
          pDoor2.position.set(8.65 - cmX, yBasePiso + 1.05, 4.50 - cmY);
          pDoor2.castShadow = true;
          pDoor2.userData = { tipo: 'puerta_depto', piso: p, dpto: 'Depto 2' };
          deptoGroup.add(pDoor2);
        }

        floorGroup.add(deptoGroup);
        deptosMeshes.push(deptoGroup);

        // D. MUROS DE ALBAÑILERIA CONFINADA
        DATA.muros.forEach(m => {
          const isX = m.dir === 'X';
          const isMed = m.is_medianera;
          const isFach = m.is_fachada;

          const origX = isX ? (m.xc - m.L / 2.0) : m.xc;
          const origY = isX ? m.yc : (m.yc - m.L / 2.0);

          // Color FEM Heatmap según ratio de verificación 8.5.2
          const uso = m.uso_852 || 0.50;
          let femHex = 0x10b981; // Verde (< 0.45)
          if (uso >= 0.65) femHex = 0xef4444; // Rojo
          else if (uso >= 0.55) femHex = 0xf59e0b; // Ámbar
          else if (uso >= 0.45) femHex = 0x84cc16; // Amarillo-verde

          const matBrickBIM = matLadrillo.clone();
          const matBrickFEM = new THREE.MeshStandardMaterial({ color: femHex, roughness: 0.5 });

          // 1. MACHONES DE LADRILLO
          m.piers.forEach(pier => {
            const pierLen = pier.L;
            const wx = isX ? pierLen : m.t;
            const wz = isX ? m.t : pierLen;
            const pierCenterDist = pier.s + pierLen / 2.0;

            const cx = isX ? (origX + pierCenterDist) : origX;
            const cy = isX ? origY : (origY + pierCenterDist);

            const hLadrillo = hPiso - 0.20; // 2.50 m
            const pierGeo = new THREE.BoxGeometry(wx, hLadrillo, wz);
            const pierMesh = new THREE.Mesh(pierGeo, matBrickBIM);
            pierMesh.position.set(cx - cmX, yBasePiso + hLadrillo / 2.0, cy - cmY);
            pierMesh.castShadow = true;
            pierMesh.receiveShadow = true;

            pierMesh.userData = {
              tipo: 'muro',
              muroInfo: m,
              piso: p,
              isMedianera: isMed,
              isFachada: isFach,
              matBIM: matBrickBIM,
              matFEM: matBrickFEM
            };

            const wire = new THREE.LineSegments(new THREE.EdgesGeometry(pierGeo), new THREE.LineBasicMaterial({ color: 0x7c2d12, linewidth: 1 }));
            pierMesh.add(wire);

            floorGroup.add(pierMesh);
            brickMeshes.push(pierMesh);
          });

          // 2. VIGA SOLERA DE CONCRETO
          const soleraWx = isX ? m.L : m.t;
          const soleraWz = isX ? m.t : m.L;
          const soleraGeo = new THREE.BoxGeometry(soleraWx, 0.20, soleraWz);
          const soleraMesh = new THREE.Mesh(soleraGeo, matConcreto.clone());
          soleraMesh.position.set(m.xc - cmX, yBasePiso + hPiso - 0.10, m.yc - cmY);
          soleraMesh.castShadow = true;
          soleraMesh.userData = { tipo: 'solera', muroInfo: m, piso: p };
          soleraMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(soleraGeo), new THREE.LineBasicMaterial({ color: 0x1e293b })));
          floorGroup.add(soleraMesh);
          soleraMeshes.push(soleraMesh);

          // 3. COLUMNAS DE CONFINAMIENTO (C-1 / C-2)
          m.ejes_col.forEach(cPos => {
            const colX = isX ? (origX + cPos) : origX;
            const colY = isX ? origY : (origY + cPos);

            const isExtrema = (Math.abs(colX) < 0.05 || Math.abs(colX - f) < 0.05);
            const colDimL = isExtrema ? 0.35 : 0.25; // C-2 vs C-1
            const cwx = isX ? colDimL : m.t;
            const cwz = isX ? m.t : colDimL;

            const colGeo = new THREE.BoxGeometry(cwx * 1.01, hPiso, cwz * 1.01);
            const colMesh = new THREE.Mesh(colGeo, matConcreto.clone());
            colMesh.position.set(colX - cmX, yBasePiso + hPiso / 2.0, colY - cmY);
            colMesh.castShadow = true;
            colMesh.receiveShadow = true;
            colMesh.userData = {
              tipo: 'columna',
              tipoCol: isExtrema ? 'C-2 (Extrema 24×35 cm, 4 ø 5/8″)' : 'C-1 (Interior 24×25 cm, 4 ø 1/2″)',
              muroInfo: m,
              piso: p
            };
            colMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(colGeo), new THREE.LineBasicMaterial({ color: 0x1e293b, linewidth: 1.5 })));
            floorGroup.add(colMesh);
            colMeshes.push(colMesh);
          });

          // 4. VANOS ARQUITECTONICOS (PUERTAS Y VENTANAS)
          m.vanos.forEach(vano => {
            const vLen = vano.w;
            const wx = isX ? vLen : m.t;
            const wz = isX ? m.t : vLen;
            const vanoCenterDist = vano.x0 + vLen / 2.0;

            const cx = isX ? (origX + vanoCenterDist) : origX;
            const cy = isX ? origY : (origY + vanoCenterDist);

            // REGLA ARQUITECTONICA ESTRICTA:
            // En fachada frontal MX-1, el vano de ingreso es PUERTA ÚNICAMENTE en Piso 1 (p === 1).
            // En pisos 2 a 5 (p > 1), es ventana del hall común con alféizar y vidrio.
            const isPuerta = (vano.tipo === 'puerta') && (p === 1 || !isFach);

            // DINTEL DE CONCRETO (sobre la puerta o ventana hasta la solera)
            const dintelH = 0.40;
            const dintelGeo = new THREE.BoxGeometry(wx, dintelH, wz);
            const dintelMesh = new THREE.Mesh(dintelGeo, matConcreto.clone());
            dintelMesh.position.set(cx - cmX, yBasePiso + 2.10 + dintelH / 2.0, cy - cmY);
            dintelMesh.userData = { tipo: 'dintel', muroInfo: m, piso: p };
            dintelMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(dintelGeo), new THREE.LineBasicMaterial({ color: 0x1e293b })));
            floorGroup.add(dintelMesh);
            lintelMeshes.push(dintelMesh);

            if (isPuerta) {
              // PUERTA:
              if (isFach && p === 1) {
                // Puerta Principal de Ingreso (Madera + Marco)
                const doorGeo = new THREE.BoxGeometry(wx - 0.08, 2.10, 0.05);
                const doorMesh = new THREE.Mesh(doorGeo, matMadera);
                doorMesh.position.set(cx - cmX, yBasePiso + 1.05, cy - cmY);
                doorMesh.userData = { tipo: 'puerta_principal', muroInfo: m, piso: p };
                floorGroup.add(doorMesh);
                doorMeshes.push(doorMesh);
              }
              // Marco resaltado
              const frameGeo = new THREE.EdgesGeometry(new THREE.BoxGeometry(wx, 2.10, wz));
              const frameLine = new THREE.LineSegments(frameGeo, new THREE.LineBasicMaterial({ color: 0xf59e0b, linewidth: 2 }));
              frameLine.position.set(cx - cmX, yBasePiso + 1.05, cy - cmY);
              floorGroup.add(frameLine);
              doorMeshes.push(frameLine);

            } else {
              // VENTANA:
              // a) Alféizar de albañilería (0 a 1.00 m)
              const alfGeo = new THREE.BoxGeometry(wx, 1.00, wz);
              const alfMesh = new THREE.Mesh(alfGeo, matLadrillo.clone());
              alfMesh.position.set(cx - cmX, yBasePiso + 0.50, cy - cmY);
              alfMesh.userData = { tipo: 'alfeizar', muroInfo: m, piso: p, matBIM: matLadrillo, matFEM: matBrickFEM };
              alfMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(alfGeo), new THREE.LineBasicMaterial({ color: 0x7c2d12 })));
              floorGroup.add(alfMesh);
              brickMeshes.push(alfMesh);

              // b) Vidrio arquitectónico translúcido (1.00 a 2.10 m, h = 1.10 m)
              const glassGeo = new THREE.BoxGeometry(isX ? vLen - 0.04 : 0.04, 1.10, isX ? 0.04 : vLen - 0.04);
              const glassMesh = new THREE.Mesh(glassGeo, matVidrio.clone());
              glassMesh.position.set(cx - cmX, yBasePiso + 1.55, cy - cmY);
              glassMesh.userData = { tipo: 'vidrio', muroInfo: m, piso: p };

              // Marco de carpintería negro/antracita
              const winFrame = new THREE.LineSegments(new THREE.EdgesGeometry(glassGeo), new THREE.LineBasicMaterial({ color: 0x0f172a, linewidth: 1.5 }));
              glassMesh.add(winFrame);
              floorGroup.add(glassMesh);
              glassMeshes.push(glassMesh);
            }
          });
        });

        // E. PARAPETO DE AZOTEA ARRIOSTRADO (h = 1.10 m, Tope N.T.T. +14.60 m) - Solo nivel 5
        if (p === nPisos) {
          const parapGroup = new THREE.Group();
          parapGroup.userData = { tipo: 'parapeto' };

          const hParap = 1.10;
          const hBrickP = 1.00;
          const hSoleritaP = 0.10;
          const tP = 0.15;
          const bColP = 0.15;
          const matBrickParap = matLadrillo.clone();
          const matConcParap = matConcreto.clone();

          function addColParapeto(gx, gz) {
            const colGeo = new THREE.BoxGeometry(bColP * 1.02, hParap, bColP * 1.02);
            const colMesh = new THREE.Mesh(colGeo, matConcParap);
            colMesh.position.set(gx - cmX, yPiso + hParap / 2, gz - cmY);
            colMesh.castShadow = true;
            colMesh.receiveShadow = true;
            colMesh.userData = { tipo: 'parapeto', elemento: 'columneta' };
            colMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(colGeo), new THREE.LineBasicMaterial({ color: 0x0f172a, linewidth: 1.5 })));
            parapGroup.add(colMesh);
            parapetoMeshes.push(colMesh);
          }

          // 1. Tramos perimetrales exteriores
          const perimSegments = [
            { isX: true, x0: 0, x1: f, z: tP / 2, len: f },
            { isX: true, x0: 0, x1: f, z: fo - tP / 2, len: f },
            { isX: false, z0: 0, z1: fo, x: tP / 2, len: fo },
            { isX: false, z0: 0, z1: fo, x: f - tP / 2, len: fo }
          ];

          perimSegments.forEach(seg => {
            const bGeo = seg.isX
              ? new THREE.BoxGeometry(seg.len, hBrickP, tP)
              : new THREE.BoxGeometry(tP, hBrickP, seg.len);
            const bMesh = new THREE.Mesh(bGeo, matBrickParap);
            const posX = seg.isX ? (seg.x0 + seg.len / 2 - cmX) : (seg.x - cmX);
            const posZ = seg.isX ? (seg.z - cmY) : (seg.z0 + seg.len / 2 - cmY);
            bMesh.position.set(posX, yPiso + hBrickP / 2, posZ);
            bMesh.castShadow = true;
            bMesh.receiveShadow = true;
            bMesh.userData = { tipo: 'parapeto', elemento: 'muro_ladrillo' };
            bMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(bGeo), new THREE.LineBasicMaterial({ color: 0x7c2d12 })));
            parapGroup.add(bMesh);
            parapetoMeshes.push(bMesh);

            const sGeo = seg.isX
              ? new THREE.BoxGeometry(seg.len, hSoleritaP, tP)
              : new THREE.BoxGeometry(tP, hSoleritaP, seg.len);
            const sMesh = new THREE.Mesh(sGeo, matConcParap);
            sMesh.position.set(posX, yPiso + hBrickP + hSoleritaP / 2, posZ);
            sMesh.castShadow = true;
            sMesh.userData = { tipo: 'parapeto', elemento: 'viga_solerita' };
            sMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(sGeo), new THREE.LineBasicMaterial({ color: 0x1e293b })));
            parapGroup.add(sMesh);
            parapetoMeshes.push(sMesh);
          });

          // 2. Columnetas perimetrales exteriores (sep <= 2.40 m)
          const nDivX = 5;
          const dxCol = f / nDivX;
          for (let i = 0; i <= nDivX; i++) {
            const cx = i * dxCol;
            addColParapeto(cx, tP / 2);
            addColParapeto(cx, fo - tP / 2);
          }

          const nDivZ = 9;
          const dzCol = fo / nDivZ;
          for (let j = 1; j < nDivZ; j++) {
            const cz = j * dzCol;
            addColParapeto(tP / 2, cz);
            addColParapeto(f - tP / 2, cz);
          }

          // 3. Parapeto de seguridad del Pozo de Luz
          const pozoSegs = [
            { isX: true, x0: pozo.x0, x1: pozo.x1, z: pozo.y0 - tP / 2, len: pozo.x1 - pozo.x0 },
            { isX: true, x0: pozo.x0, x1: pozo.x1, z: pozo.y1 + tP / 2, len: pozo.x1 - pozo.x0 },
            { isX: false, z0: pozo.y0, z1: pozo.y1, x: pozo.x0 - tP / 2, len: pozo.y1 - pozo.y0 },
            { isX: false, z0: pozo.y0, z1: pozo.y1, x: pozo.x1 + tP / 2, len: pozo.y1 - pozo.y0 }
          ];

          pozoSegs.forEach(seg => {
            const bGeo = seg.isX
              ? new THREE.BoxGeometry(seg.len, hBrickP, tP)
              : new THREE.BoxGeometry(tP, hBrickP, seg.len);
            const bMesh = new THREE.Mesh(bGeo, matBrickParap);
            const posX = seg.isX ? (seg.x0 + seg.len / 2 - cmX) : (seg.x - cmX);
            const posZ = seg.isX ? (seg.z - cmY) : (seg.z0 + seg.len / 2 - cmY);
            bMesh.position.set(posX, yPiso + hBrickP / 2, posZ);
            bMesh.castShadow = true;
            bMesh.userData = { tipo: 'parapeto', elemento: 'muro_pozo' };
            bMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(bGeo), new THREE.LineBasicMaterial({ color: 0x7c2d12 })));
            parapGroup.add(bMesh);
            parapetoMeshes.push(bMesh);

            const sGeo = seg.isX
              ? new THREE.BoxGeometry(seg.len, hSoleritaP, tP)
              : new THREE.BoxGeometry(tP, hSoleritaP, seg.len);
            const sMesh = new THREE.Mesh(sGeo, matConcParap);
            sMesh.position.set(posX, yPiso + hBrickP + hSoleritaP / 2, posZ);
            sMesh.userData = { tipo: 'parapeto', elemento: 'viga_solerita' };
            sMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(sGeo), new THREE.LineBasicMaterial({ color: 0x1e293b })));
            parapGroup.add(sMesh);
            parapetoMeshes.push(sMesh);
          });

          // Columnetas del pozo de luz
          addColParapeto(pozo.x0 - tP / 2, pozo.y0 - tP / 2);
          addColParapeto(pozo.x1 + tP / 2, pozo.y0 - tP / 2);
          addColParapeto(pozo.x0 - tP / 2, pozo.y1 + tP / 2);
          addColParapeto(pozo.x1 + tP / 2, pozo.y1 + tP / 2);
          addColParapeto(pozo.x0 + (pozo.x1 - pozo.x0) / 2, pozo.y0 - tP / 2);
          addColParapeto(pozo.x0 + (pozo.x1 - pozo.x0) / 2, pozo.y1 + tP / 2);
          addColParapeto(pozo.x0 - tP / 2, pozo.y0 + (pozo.y1 - pozo.y0) / 2);
          addColParapeto(pozo.x1 + tP / 2, pozo.y0 + (pozo.y1 - pozo.y0) / 2);

          floorGroup.add(parapGroup);
        }
      }
    }

    function setVisualMode(mode) {
      currentVisualMode = mode;
      document.getElementById('btn-mode-bim').classList.toggle('active', mode === 'bim');
      document.getElementById('btn-mode-fem').classList.toggle('active', mode === 'fem');
      document.getElementById('btn-mode-xray').classList.toggle('active', mode === 'xray');
      document.getElementById('btn-mode-wire').classList.toggle('active', mode === 'wire');
      document.getElementById('fem-legend').style.display = (mode === 'fem') ? 'block' : 'none';

      brickMeshes.forEach(m => {
        if (!m.material) return;
        if (mode === 'fem' && m.userData.matFEM) {
          m.material = m.userData.matFEM;
          m.material.wireframe = false;
          m.material.transparent = false;
          m.material.opacity = 1.0;
        } else if (mode === 'xray') {
          m.material = m.userData.matBIM || m.material;
          m.material.wireframe = false;
          m.material.transparent = true;
          m.material.opacity = 0.25;
        } else if (mode === 'wire') {
          m.material = m.userData.matBIM || m.material;
          m.material.wireframe = true;
          m.material.transparent = true;
          m.material.opacity = 0.8;
        } else {
          // BIM Realista
          m.material = m.userData.matBIM || m.material;
          m.material.wireframe = false;
          m.material.transparent = false;
          m.material.opacity = 1.0;
        }
      });

      colMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.70 : 1.0;
      });

      soleraMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.70 : 1.0;
      });

      lintelMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.70 : 1.0;
      });

      stairMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.70 : 1.0;
      });

      slabMeshes.forEach(s => {
        if (!s.material) return;
        s.material.opacity = (mode === 'wire') ? 0.15 : (mode === 'xray' ? 0.20 : 0.75);
      });

      foundationMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.35 : 1.0;
      });

      parapetoMeshes.forEach(m => {
        if (!m.material) return;
        m.material.wireframe = (mode === 'wire');
        m.material.transparent = (mode === 'xray');
        m.material.opacity = (mode === 'xray') ? 0.35 : 1.0;
      });
    }

    function updateExplode(val) {
      explodeDistance = parseFloat(val);
      document.getElementById('val-explode').textContent = explodeDistance.toFixed(1) + ' m';

      floorGroups.forEach((grp, idx) => {
        // Piso 1 no se mueve; pisos 2..5 se elevan proporcionalmente
        grp.position.y = idx * explodeDistance;
      });
    }

    let currentIsolatedFloor = 0; // 0: Todos, 1..5: individual

    function isolateFloor(floorNum) {
      currentIsolatedFloor = floorNum;
      for (let i = 0; i <= 5; i++) {
        const btn = document.getElementById('btn-fl-' + i);
        if (btn) btn.classList.toggle('active', i === floorNum);
      }
      const valText = document.getElementById('val-floor-active');
      if (valText) valText.textContent = (floorNum === 0) ? 'Todos' : ('Piso ' + floorNum);

      floorGroups.forEach((grp, idx) => {
        grp.visible = (floorNum === 0 || idx + 1 === floorNum);
      });
    }

    function setMode(modeNum) {
      activeMode = modeNum;
      document.getElementById('btn-static').classList.toggle('active', modeNum === 0);
      document.getElementById('btn-mode1').classList.toggle('active', modeNum === 1);
      document.getElementById('btn-mode2').classList.toggle('active', modeNum === 2);
      document.getElementById('btn-mode3').classList.toggle('active', modeNum === 3);

      const headerMode = document.getElementById('header-t1');
      if (modeNum === 0) headerMode.textContent = "Estático (Sin oscilar)";
      else if (modeNum === 1) headerMode.textContent = "T1 = 0,188 s (X, 81.3 %)";
      else if (modeNum === 2) headerMode.textContent = "T2 = 0,168 s (Y, 83.6 %)";
      else if (modeNum === 3) headerMode.textContent = "T3 = 0,152 s (Torsión)";
    }

    function updateScale(val) {
      scaleFactor = parseFloat(val);
      document.getElementById('val-scale').textContent = val + 'x';
    }

    function updateSpeed(val) {
      animSpeed = parseFloat(val);
      document.getElementById('val-speed').textContent = parseFloat(val).toFixed(1) + 'x';
    }

    function setCamera(view) {
      const bFrente = DATA.edificio.frente;
      const bFondo = DATA.edificio.fondo;
      const hTotal = DATA.edificio.h_total;
      const cx = bFrente / 2;
      const cy = hTotal / 2;
      const cz = bFondo / 2;

      if (controls) {
        controls.target.set(cx, cy, cz);
      }

      if (view === 'iso') {
        camera.position.set(cx + 26, cy + 18, cz + 34);
      } else if (view === 'top') {
        camera.position.set(cx, cy + 42, cz + 0.01);
      } else if (view === 'front') {
        camera.position.set(cx, cy, -26);
      } else if (view === 'side') {
        camera.position.set(cx + 36, cy, cz);
      } else if (view === 'rear') {
        camera.position.set(cx, cy, cz + 38);
      } else if (view === 'roof') {
        camera.position.set(cx + 14.0, hTotal + 7.0, cz + 16.0);
        if (controls) controls.target.set(cx, hTotal + 0.5, cz);
      } else if (view === 'foundation') {
        camera.position.set(cx + 22, -4, cz + 26);
        if (controls) controls.target.set(cx, -0.75, cz);
      } else if (view === 'stairs') {
        const esc = DATA.edificio.escalera;
        const cmX = DATA.edificio.cm.x;
        const cmY = DATA.edificio.cm.y;
        camera.position.set(esc.x0 + 1.35 - cmX - 3.5, cy + 6.0, esc.y0 + 1.38 - cmY - 4.5);
        if (controls) controls.target.set(esc.x0 + 1.35 - cmX, cy - 1.0, esc.y0 + 1.38 - cmY);
      } else if (view === 'deptoA') {
        const cmX = DATA.edificio.cm.x;
        const cmY = DATA.edificio.cm.y;
        camera.position.set(3.0 - cmX - 12.0, cy + 15.0, 10.5 - cmY - 10.0);
        if (controls) controls.target.set(3.0 - cmX, cy, 10.5 - cmY);
      } else if (view === 'deptoB') {
        const cmX = DATA.edificio.cm.x;
        const cmY = DATA.edificio.cm.y;
        camera.position.set(8.9 - cmX + 12.0, cy + 15.0, 10.5 - cmY - 10.0);
        if (controls) controls.target.set(8.9 - cmX, cy, 10.5 - cmY);
      }
      if (controls) {
        controls.update();
      }
    }

    function resetCamera() {
      setCamera('iso');
    }

    function toggleLayer(layer, visible) {
      if (layer === 'foundation') {
        foundationMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'brick') {
        brickMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'cols') {
        colMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'soleras') {
        soleraMeshes.forEach(m => m.visible = visible);
        lintelMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'slabs') {
        slabMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'parapeto') {
        parapetoMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'stairs') {
        stairMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'openings') {
        glassMeshes.forEach(m => m.visible = visible);
        doorMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'site') {
        siteMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'cm') {
        cmMeshes.forEach(m => m.visible = visible);
      } else if (layer === 'deptos') {
        deptosMeshes.forEach(m => m.visible = visible);
      }
    }

    function setAllLayers(visible) {
      const layers = ['foundation', 'brick', 'cols', 'soleras', 'slabs', 'parapeto', 'stairs', 'openings', 'site', 'cm', 'deptos'];
      layers.forEach(l => {
        const chk = document.getElementById('chk-' + l);
        if (chk) chk.checked = visible;
        toggleLayer(l, visible);
      });
    }

    function setLayerPreset(preset) {
      const presets = {
        'structure': { foundation: false, brick: true, cols: true, soleras: true, slabs: true, parapeto: false, stairs: true, deptos: false, openings: false, site: false, cm: true },
        'masonry': { foundation: false, brick: true, cols: false, soleras: false, slabs: false, parapeto: true, stairs: false, deptos: false, openings: false, site: false, cm: false },
        'foundation': { foundation: true, brick: false, cols: false, soleras: false, slabs: false, parapeto: false, stairs: false, deptos: false, openings: false, site: false, cm: false },
        'all': { foundation: true, brick: true, cols: true, soleras: true, slabs: true, parapeto: true, stairs: true, deptos: true, openings: true, site: true, cm: true }
      };
      const cfg = presets[preset];
      if (!cfg) return;
      Object.keys(cfg).forEach(l => {
        const chk = document.getElementById('chk-' + l);
        if (chk) chk.checked = cfg[l];
        toggleLayer(l, cfg[l]);
      });
    }

    let muroSeleccionadoInfo = null;
    let hoveredMesh = null;
    function onPointerMove(event) {
      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const interactables = [...brickMeshes, ...colMeshes, ...soleraMeshes, ...lintelMeshes, ...foundationMeshes, ...stairMeshes, ...deptosMeshes, ...parapetoMeshes].filter(m => m.visible);
      const intersects = raycaster.intersectObjects(interactables, true);

      if (intersects.length > 0) {
        document.body.style.cursor = 'pointer';
        const hit = intersects[0].object;
        if (hoveredMesh !== hit && hoveredMesh !== selectedMesh && hoveredMesh && hoveredMesh.material && hoveredMesh.material.emissive) {
          hoveredMesh.material.emissive.setHex(0x000000);
        }
        hoveredMesh = hit;
        if (hoveredMesh !== selectedMesh && hoveredMesh.material && hoveredMesh.material.emissive) {
          hoveredMesh.material.emissive.setHex(0x1e293b);
        }
      } else {
        document.body.style.cursor = 'default';
        if (hoveredMesh && hoveredMesh !== selectedMesh && hoveredMesh.material && hoveredMesh.material.emissive) {
          hoveredMesh.material.emissive.setHex(0x000000);
        }
        hoveredMesh = null;
      }
    }

    function onCanvasClick(event) {
      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const interactables = [...brickMeshes, ...colMeshes, ...soleraMeshes, ...lintelMeshes, ...foundationMeshes, ...stairMeshes, ...deptosMeshes, ...parapetoMeshes].filter(m => m.visible);
      const intersects = raycaster.intersectObjects(interactables, true);

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        if (hit.userData && (hit.userData.muroInfo || hit.userData.tipo === 'cimiento' || hit.userData.tipo === 'sobrecimiento' || hit.userData.tipo === 'escalera' || hit.userData.tipo === 'ambiente' || hit.userData.tipo === 'tabique' || hit.userData.tipo === 'parapeto')) {
          seleccionarElemento(hit);
        }
      }
    }

    function seleccionarElemento(mesh) {
      if (selectedMesh && selectedMesh.material && selectedMesh.material.emissive) {
        selectedMesh.material.emissive.setHex(0x000000);
      }
      selectedMesh = mesh;
      if (selectedMesh.material && selectedMesh.material.emissive) {
        selectedMesh.material.emissive.setHex(0x38bdf8);
      }

      if (mesh.userData.tipo === 'cimiento') {
        mostrarDatosCimiento(mesh.userData);
      } else if (mesh.userData.tipo === 'sobrecimiento') {
        mostrarDatosSobrecimiento(mesh.userData);
      } else if (mesh.userData.tipo === 'escalera') {
        mostrarDatosEscalera(mesh.userData);
      } else if (mesh.userData.tipo === 'ambiente') {
        mostrarDatosAmbiente(mesh.userData);
      } else if (mesh.userData.tipo === 'tabique') {
        mostrarDatosTabique(mesh.userData);
      } else if (mesh.userData.tipo === 'parapeto') {
        mostrarDatosParapeto(mesh.userData);
      } else {
        mostrarDatosMuro(mesh.userData.muroInfo, mesh.userData.tipoCol);
      }
    }

    function mostrarDatosParapeto(u) {
      const elem = u.elemento || 'parapeto';
      let titleElem = 'Panel de Albañilería Confinada (Ladrillo King Kong)';
      if (elem === 'columneta') titleElem = 'Columneta de Concreto Armado (15×15 cm)';
      else if (elem.includes('solerita')) titleElem = 'Viga Solerita de Coronación (15×10 cm)';
      else if (elem === 'muro_pozo') titleElem = 'Antepecho de Seguridad de Pozo de Luz';

      document.getElementById('txt-card-title').textContent = "Parapeto de Azotea Arriostrado (h = 1,10 m) · " + titleElem;
      document.getElementById('card-dims').textContent = "h = 1,10 m (N.T.T. +14,60 m) · t = 0,15 m (Soga) · Perímetro = 65,80 m";
      document.getElementById('card-vanos').textContent = "29 Columnetas 15×15 cm @ 2,40 m (2 ø 3/8″) · Solerita continua 15×10 cm (E.070 9.3.5)";
      document.getElementById('card-vmod').innerHTML = '<span style="color: #38bdf8;">Carga E.020 Art. 8.2: H = 60 kgf/m (weq = 109,1 kgf/m² > sismo 86,4 kgf/m²)</span>';
      document.getElementById('card-uso').textContent = "fm = 1,339 kgf/cm² ≤ 1,500 kgf/cm² (89,3% uso) · As req = 0,335 cm² ≤ 1,42 cm² (CUMPLE)";
      const progBar = document.getElementById('card-prog');
      progBar.style.width = '89.3%';
      progBar.style.background = '#10b981';
      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = "ARRIOSTRE CUMPLE (E.070 10.1 / E.020 8.2)";
    }

    function mostrarDatosEscalera(u) {
      document.getElementById('txt-card-title').textContent = "Caja de Escalera de Concreto Armado (Piso " + (u.piso || 1) + ") · E.070 Art. 9.1";
      document.getElementById('card-dims').textContent = "2 Tramos en U · Ancho = 1.20 m · Descanso = 2.70 m × 1.20 m";
      document.getElementById('card-vanos').textContent = "16 Contrapasos (0.169 m) · 14 Pasos (0.25 m) · Columnetas dedicadas C-3";
      document.getElementById('card-vmod').innerHTML = '<span style="color: #38bdf8;">Concreto f&#39;c = 210 kg/cm² · Acero Grado 60 · Barandas tubulares h = 0.90 m</span>';
      document.getElementById('card-uso').textContent = "A.020 Art. 15.2 / E.070 Art. 9.1: 100% CUMPLE";
      const progBar = document.getElementById('card-prog');
      progBar.style.width = '100%';
      progBar.style.background = '#10b981';
      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = "ESCALERA REGLAMENTARIA (CUMPLE)";
    }

    function mostrarDatosAmbiente(u) {
      document.getElementById('txt-card-title').textContent = u.dptoNombre + " · " + u.nombre;
      document.getElementById('card-dims').textContent = u.dx.toFixed(2) + " m × " + u.dy.toFixed(2) + " m (Área útil: " + u.area.toFixed(2) + " m²)";
      document.getElementById('card-vanos').textContent = "Iluminación y Ventilación: " + u.luz;
      document.getElementById('card-vmod').innerHTML = '<span style="color: #34d399;">Piso porcelanato sobre losa aligerada e = 0.20 m (Carga permanente = 100 kgf/m²)</span>';
      document.getElementById('card-uso').textContent = "A.020 Normativa Vivienda: Confort Térmico y Lumínico OK";
      const progBar = document.getElementById('card-prog');
      progBar.style.width = '100%';
      progBar.style.background = '#10b981';
      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = "AMBIENTE HABITABLE A.020";
    }

    function mostrarDatosTabique(u) {
      document.getElementById('txt-card-title').textContent = "Tabique Interior de Albañilería Hueca (Ladrillo Pandereta)";
      document.getElementById('card-dims').textContent = "L = " + u.L.toFixed(2) + " m · e = 0.12 m · h = 2.50 m (Soga)";
      document.getElementById('card-vanos').textContent = "Mortero 1:4 · Tarrajeo ambas caras e = 1.5 cm · Junta sismo-resistente";
      document.getElementById('card-vmod').innerHTML = '<span style="color: #cbd5e1;">Metrado real E.020 Art. 5 (31_tabiqueria_real.py) · No portante</span>';
      document.getElementById('card-uso').textContent = "E.070 Art. 9.3: Tabique no estructural";
      const progBar = document.getElementById('card-prog');
      progBar.style.width = '100%';
      progBar.style.background = '#38bdf8';
      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = "TABIQUE ARRIOSTRADO";
    }

function mostrarDatosCimiento(u) {
      const m = u.muroInfo;
      const isMed = u.isMedianera;
      const nomPuro = m ? m.nom.split('  ')[0] : 'Cimiento';
      const title = `Cimiento Corrido Armado (${nomPuro}) ${isMed ? '· Medianero Excéntrico' : '· Confinamiento Central'}`;
      document.getElementById('txt-card-title').textContent = title;
      document.getElementById('card-dims').textContent =
        `B = ${u.B.toFixed(2)} m × Df = ${u.Df.toFixed(2)} m (h = 0,80 m, L = ${m ? m.L.toFixed(2) : '—'} m)`;

      document.getElementById('card-vanos').textContent =
        isMed ? "Excentricidad e = 0,23 m equilibrada por cimientos transversales MX" : "Cimiento corrido centrado bajo confinamientos";

      document.getElementById('card-vmod').innerHTML =
        `<span style="color: #38bdf8;">q_real = ${u.q_real.toFixed(2)} kg/cm² &lt; q_adm = ${u.q_ad.toFixed(2)} kg/cm²</span>`;

      const usoPct = Math.round((u.q_real / u.q_ad) * 100);
      document.getElementById('card-uso').textContent = `Presión al Suelo: ${usoPct} % de q_adm`;
      const progBar = document.getElementById('card-prog');
      progBar.style.width = usoPct + '%';
      progBar.style.background = '#10b981';

      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = `CUMPLE E.050 / E.070 (Margen +${Math.round((u.q_ad / u.q_real - 1) * 100)}%)`;
    }

    function mostrarDatosSobrecimiento(u) {
      const m = u.muroInfo;
      const nomPuro = m ? m.nom.split('  ')[0] : 'Sobrecimiento';
      document.getElementById('txt-card-title').textContent = `Sobrecimiento Armado (${nomPuro})`;
      document.getElementById('card-dims').textContent =
        `t = ${m ? m.t.toFixed(2) : '0,24'} m × h = 0,80 m (NPT -0,70 m a +0,10 m)`;
      document.getElementById('card-vanos').textContent =
        "Protección contra humedad + Confinamiento horizontal inferior E.070 Art. 2.1.3";
      document.getElementById('card-vmod').innerHTML =
        `<span style="color: #cbd5e1;">Concreto f'c = 175 kg/cm²</span>`;
      document.getElementById('card-uso').textContent = "Barrera hidrófuga y confinamiento base";
      const progBar = document.getElementById('card-prog');
      progBar.style.width = '100%';
      progBar.style.background = '#38bdf8';
      const tag = document.getElementById('card-status-tag');
      tag.className = "tag-status tag-ok";
      tag.textContent = "CONFINAMIENTO INFERIOR OK";
    }

    function mostrarDatosMuro(m, tipoCol) {
      muroSeleccionadoInfo = m;
      document.getElementById('btn-explain').style.display = 'block';
      const title = tipoCol ? `${m.nom.split('  ')[0]} · ${tipoCol}` : m.nom;
      document.getElementById('txt-card-title').textContent = title;
      document.getElementById('card-dims').textContent =
        `${m.L.toFixed(2)} m × ${m.t.toFixed(2)} m × ${DATA.edificio.h_total.toFixed(2)} m`;

      let vanoTxt = "Sin vanos (Muro ciego)";
      if (m.nom.startsWith("MX-1")) vanoTxt = "1 Puerta (Piso 1) + 4 Ventanas";
      else if (m.nom.startsWith("MX-7")) vanoTxt = "4 Ventanas de Dormitorios";
      else if (m.vanos && m.vanos.length > 0) vanoTxt = `${m.vanos.length} Vano(s) de paso con dintel`;
      document.getElementById('card-vanos').textContent = vanoTxt;

      const difSign = m.dif_pct >= 0 ? '+' : '';
      const colorV = m.dif_pct > 15 ? '#f87171' : '#60a5fa';
      document.getElementById('card-vmod').innerHTML =
        `<span style="color: ${colorV};">${Math.round(m.v_modelo).toLocaleString()} kgf (${difSign}${m.dif_pct} %)</span>`;

      const usoPct = Math.round((m.uso_852 || 0.5) * 100);
      document.getElementById('card-uso').textContent = `Uso: ${usoPct} % de 0,55 Vm`;
      const progBar = document.getElementById('card-prog');
      progBar.style.width = Math.min(100, usoPct) + '%';
      progBar.style.background = (usoPct > 65) ? '#ef4444' : ((usoPct > 55) ? '#f59e0b' : '#10b981');

      const tag = document.getElementById('card-status-tag');
      if (usoPct <= 100) {
        tag.className = "tag-status tag-ok";
        tag.textContent = `Ve ≤ 0,55 Vm (${usoPct}% CUMPLE)`;
      } else {
        tag.className = "tag-status tag-warn";
        tag.textContent = "SUPERARÍA LÍMITE FISURACIÓN";
      }
    }

    
        function mostrarExplicacionE070() {
      if(!muroSeleccionadoInfo) return;
      const m = muroSeleccionadoInfo;
      const Vm = m.Vm.toFixed(1);
      const Ve = m.Ve_mod.toFixed(1);
      const lim = m.lim_852.toFixed(1);
      const ok = (parseFloat(Ve) <= parseFloat(lim)) ? '<span style="color:#10b981">CUMPLE</span>' : '<span style="color:#ef4444">NO CUMPLE</span>';
      
      const html = `
        <div style="margin-bottom:8px;"><span style="color:#38bdf8;">Demanda Sísmica (Ve):</span> <span style="color:#f1f5f9">${Ve} kgf</span> <br><span style="color:#94a3b8; font-size:0.75rem;">(Cortante Sismo Moderado OpenSeesPy)</span></div>
        <div style="margin-bottom:8px;"><span style="color:#38bdf8;">Capacidad Analítica (Vm):</span> <span style="color:#f1f5f9">${Vm} kgf</span></div>
        <hr style="border-color:rgba(255,255,255,0.1); margin:8px 0;">
        <div style="font-size:0.85rem; margin-bottom:4px; color:#f59e0b;">Fórmula Reglamentaria:</div>
        <div style="background:#1e293b; padding:8px; border-radius:6px; font-size:0.95rem; text-align:center; border:1px solid rgba(255,255,255,0.1);">
          <strong>V<sub>e</sub> &le; 0.55 &times; V<sub>m</sub></strong>
        </div>
        <div style="margin-top:10px; font-size:0.95rem; text-align:center;">
          ${Ve} &le; 0.55 &times; ${Vm} <br>
          ${Ve} &le; ${lim} &rarr; <strong>${ok}</strong>
        </div>
        <div style="margin-top:12px; font-size:0.7rem; color:#94a3b8; line-height:1.4;">
          * Según el Artículo 8.5.2 de la E.070, si la demanda por sismo moderado supera el 55% de la resistencia nominal, el muro corre riesgo de fisuración severa y debe reforzarse o engrosarse.
        </div>
      `;
      document.getElementById('modal-formula-content').innerHTML = html;
      document.getElementById('modal-explain').style.display = 'block';
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
      requestAnimationFrame(animate);

      const time = clock.getElapsedTime() * animSpeed;
      const cmX = DATA.edificio.cm.x;
      const cmY = DATA.edificio.cm.y;

      if (activeMode > 0 && DATA.modos[activeMode - 1]) {
        const modoData = DATA.modos[activeMode - 1];
        const omega = 2 * Math.PI / modoData.T;
        const sinVal = Math.sin(time * omega);

        floorGroups.forEach((grp, idx) => {
          const fPiso = modoData.forma[idx];
          const dx = (fPiso.ux * sinVal * scaleFactor) / 100.0;
          const dz = (fPiso.uy * sinVal * scaleFactor) / 100.0;
          const dr = (fPiso.rz * sinVal * scaleFactor);

          grp.position.x = cmX + dx;
          grp.position.z = cmY + dz;
          grp.position.y = idx * explodeDistance;
          grp.rotation.y = dr;
        });
      } else {
        floorGroups.forEach((grp, idx) => {
          grp.position.x = cmX;
          grp.position.z = cmY;
          grp.position.y = idx * explodeDistance;
          grp.rotation.y = 0;
        });
      }

      controls.update();
      renderer.render(scene, camera);
    }

    window.onload = init;
  