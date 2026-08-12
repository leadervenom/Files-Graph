(() => {
  window.addEventListener('error', e => {
    try { window.pywebview?.api?.client_error(`${e.message} @ ${e.filename}:${e.lineno}`); } catch (_) {}
  });
  window.addEventListener('unhandledrejection', e => {
    try { window.pywebview?.api?.client_error(`unhandled rejection: ${e.reason}`); } catch (_) {}
  });

  const graphEl = document.getElementById('graph');
  const loadingEl = document.getElementById('loading');
  const loadingPercentEl = document.getElementById('loadingPercent');
  const progressBarEl = document.getElementById('progressBar');
  const loadingDetailEl = document.getElementById('loadingDetail');
  const pathInput = document.getElementById('pathInput');
  const depthInput = document.getElementById('depthInput');
  const scanBtn = document.getElementById('scanBtn');
  const browseBtn = document.getElementById('browseBtn');
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const openBtn = document.getElementById('openBtn');
  const statusEl = document.getElementById('status');
  const infoCard = document.getElementById('infoCard');
  const legendEl = document.getElementById('legend');
  const chooserEl = document.getElementById('chooser');
  const chooserTitleEl = document.getElementById('chooserTitle');
  const chooserSubEl = document.getElementById('chooserSub');
  const chooserBackEl = document.getElementById('chooserBack');
  const userListEl = document.getElementById('userList');
  const nodeGlowEl = document.getElementById('nodeGlow');

  let selectedId = null;
  let currentData = { nodes: [], links: [] };
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const Graph = ForceGraph3D()(graphEl)
    .backgroundColor('#020203')
    .nodeLabel(n => n.name)
    .nodeVal(n => (n.id === selectedId ? n.val * 1.9 : n.val))
    .nodeColor(n => {
      if (n.id === selectedId) return '#ff4d4d';
      if (n.expandable && !n.expanded) return dimColor(n.color);
      return n.color;
    })
    .nodeOpacity(0.95)
    .nodeResolution(8)
    .linkColor(() => 'rgba(160,170,220,0.35)')
    .linkWidth(0.35)
    .linkCurvature(0.18)
    .linkDirectionalParticles(prefersReducedMotion ? 0 : 2)
    .linkDirectionalParticleWidth(1.3)
    .linkDirectionalParticleSpeed(0.004)
    .linkDirectionalParticleColor(() => '#8f9bff')
    .d3AlphaDecay(0.025)
    .d3VelocityDecay(0.28)
    .warmupTicks(60)
    // Physics used to run forever even after the graph visually settled, competing
    // with the render loop every frame -- the real cause of "spinning isn't smooth".
    // Let it settle then stop; graphData() reheats automatically for new nodes.
    .cooldownTicks(150)
    .cooldownTime(6000)
    .onNodeClick(handleNodeClick)
    .onNodeDragEnd(n => {
      // Un-pin after a drag so the node eases back under its neighbors' pull
      // instead of staying frozen where it was dropped -- reads as "alive".
      delete n.fx; delete n.fy; delete n.fz;
    });

  // More links visible at once (e.g. after several expansions) means more per-frame
  // particle animation cost -- thin them out past a threshold instead of a fixed value.
  function applyParticleGate() {
    if (prefersReducedMotion) return;
    Graph.linkDirectionalParticles(currentData.links.length > 800 ? 1 : 2);
  }

  // Gentle idle "breathing" instead of a flat constant spin: slowly sine-modulates
  // autoRotateSpeed. Self-terminating -- checks autoRotate every tick and simply
  // stops looping the moment the user takes control (first drag), so it never runs
  // as dead weight after interaction starts.
  function startIdleDrift() {
    if (prefersReducedMotion) return;
    const driftStart = Date.now();
    const tick = () => {
      if (!Graph.controls().autoRotate) return;
      const t = (Date.now() - driftStart) / 1000;
      Graph.controls().autoRotateSpeed = 0.5 + 0.2 * Math.sin((t * Math.PI * 2) / 20);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  Graph.controls().autoRotate = !prefersReducedMotion;
  Graph.controls().autoRotateSpeed = 0.5;
  Graph.controls().addEventListener('start', () => { Graph.controls().autoRotate = false; });
  startIdleDrift();

  window.addEventListener('resize', () => Graph.width(window.innerWidth).height(window.innerHeight));

  // 3d-force-graph has no built-in onNodeDoubleClick (that call threw and killed the
  // whole script before this fix) -- detect it manually from two clicks on the same
  // node within a normal double-click window.
  let lastClickId = null;
  let lastClickTime = 0;
  function handleNodeClick(node) {
    const now = Date.now();
    const isDoubleClick = node && node.id === lastClickId && now - lastClickTime < 400;
    lastClickId = node ? node.id : null;
    lastClickTime = now;
    selectNode(node);
    if (!isDoubleClick || !node) return;
    if (node.isDir && node.expandable && !node.expanded) {
      expandNode(node);
    } else {
      openSelected();
    }
  }

  // Open-world style: an unexpanded folder is just an aggregate node until you
  // double-click it, at which point its immediate children load and merge into the
  // live graph (existing nodes keep their position/velocity; only new ones spring in).
  async function expandNode(node) {
    if (node.expanded || node._expanding) return;
    node._expanding = true;
    setStatus(`Expanding ${node.name}…`);
    const result = await window.pywebview.api.expand_folder(node.path, node.depth);
    node._expanding = false;
    if (result.error) {
      setStatus(result.error);
      return;
    }
    const existingIds = new Set(currentData.nodes.map(n => n.id));
    const newNodes = result.children.filter(c => !existingIds.has(c.id));
    const newLinks = newNodes.map(c => ({ source: node.id, target: c.id, _burst: true }));
    currentData.nodes.push(...newNodes);
    currentData.links.push(...newLinks);
    node.expanded = true;
    node.expandable = false;
    Graph.graphData(currentData);

    // Brief "data flowing in" burst on just the newly added links, then settle back
    // to the normal gated baseline after ~1.2s -- bounded and self-restoring, never
    // a permanent change, so it can't reintroduce the perpetual-render jank that
    // cooldownTicks/cooldownTime was added to fix.
    if (prefersReducedMotion) {
      applyParticleGate();
    } else {
      Graph.linkDirectionalParticles(l => (l._burst ? 6 : (currentData.links.length > 800 ? 1 : 2)));
      Graph.linkDirectionalParticleWidth(l => (l._burst ? 2.2 : 1.3));
      setTimeout(() => {
        newLinks.forEach(l => { delete l._burst; });
        applyParticleGate();
        Graph.linkDirectionalParticleWidth(1.3);
      }, 1200);
    }
    setStatus(`${currentData.nodes.length} items`);
    if (selectedId === node.id) selectNode(node); // refresh info card now that it's expanded
  }

  // Unexpanded ("aggregate") folders get a duller tint so it's clear at a glance they
  // still have hidden detail, without any extra 3D marker geometry.
  function dimColor(hex) {
    const c = hex.replace('#', '');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    const mix = v => Math.round(v * 0.55 + 70 * 0.45);
    return `rgb(${mix(r)},${mix(g)},${mix(b)})`;
  }

  // Soft glow that tracks the selected node across screen space -- the 3D scene's
  // internal three.js instance isn't reachable from here to build custom glow
  // objects (THREE isn't exposed globally by the vendored bundle), so this is a 2D
  // CSS overlay positioned via Graph.graph2ScreenCoords instead. Self-stops the
  // moment selection changes or clears, never runs with nothing selected.
  let glowRafId = null;
  function stopNodeGlow() {
    if (glowRafId) cancelAnimationFrame(glowRafId);
    glowRafId = null;
    nodeGlowEl.style.opacity = '0';
  }
  function startNodeGlow(node) {
    nodeGlowEl.style.background = `radial-gradient(circle, ${node.color} 0%, transparent 70%)`;
    const track = () => {
      if (selectedId !== node.id) { stopNodeGlow(); return; }
      const pos = Graph.graph2ScreenCoords(node.x || 0, node.y || 0, node.z || 0);
      nodeGlowEl.style.left = `${pos.x}px`;
      nodeGlowEl.style.top = `${pos.y}px`;
      nodeGlowEl.style.opacity = '0.55';
      glowRafId = requestAnimationFrame(track);
    };
    track();
  }

  function selectNode(node) {
    selectedId = node ? node.id : null;
    Graph.nodeColor(Graph.nodeColor());
    Graph.nodeVal(Graph.nodeVal());
    stopNodeGlow();
    if (!node) {
      infoCard.innerHTML = `<div class="name">—</div><div class="path">Nothing selected.</div>`;
      return;
    }
    startNodeGlow(node);
    const isUnexpanded = node.isDir && node.expandable && !node.expanded;
    const meta = node.isDir
      ? `${isUnexpanded ? '~' : ''}${node.leafCount} items inside${isUnexpanded ? ' — double-click to expand' : ''}`
      : node.sizeHuman;
    infoCard.innerHTML = `
      <div class="name">[${node.isDir ? 'Folder' : 'File'}] ${escapeHtml(node.name)}</div>
      <div class="path">${escapeHtml(node.path)}</div>
      <div>${escapeHtml(meta)}</div>
    `;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function baseName(p) {
    if (!p) return '';
    const parts = String(p).split(/[\\/]/).filter(Boolean);
    return parts[parts.length - 1] || p;
  }

  // Cross-fades status text instead of an instant swap -- purely a quick 150ms
  // transition (see #status's CSS transition), not continuous motion.
  let statusTimer = null;
  function setStatus(text) {
    if (prefersReducedMotion) {
      statusEl.textContent = text;
      return;
    }
    statusEl.style.opacity = '0';
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => {
      statusEl.textContent = text;
      statusEl.style.opacity = '1';
    }, 120);
  }

  async function openSelected() {
    if (!selectedId) return;
    await window.pywebview.api.open_path(selectedId);
  }
  openBtn.addEventListener('click', openSelected);

  // Called from Python (via evaluate_js) roughly every 20 items scanned, so the
  // percentage is real progress against the same cap the scan itself stops at --
  // not a fake spinner. Keeps the wait legible instead of an indefinite freeze.
  window.__scanProgress = (count, cap, currentDir) => {
    const pct = cap > 0 ? Math.min(100, Math.round((count / cap) * 100)) : 0;
    loadingPercentEl.textContent = `${pct}%`;
    progressBarEl.style.width = `${pct}%`;
    loadingDetailEl.textContent = currentDir
      ? `Scanning ${baseName(currentDir)}… (${count} items so far)`
      : `${count} items scanned`;
  };

  async function doScan() {
    setStatus('Scanning…');
    loadingPercentEl.textContent = '0%';
    progressBarEl.style.width = '0%';
    loadingDetailEl.textContent = 'Starting…';
    loadingEl.style.opacity = '1';
    const data = await window.pywebview.api.scan(pathInput.value, depthInput.value);
    loadingEl.style.opacity = '0';
    if (data.error) {
      setStatus(data.error);
      return;
    }
    currentData = data;
    selectedId = null;
    selectNode(null);
    Graph.graphData(data);
    applyParticleGate();
    setStatus(`${data.nodes.length} items`);
    Graph.controls().autoRotate = !prefersReducedMotion;
    startIdleDrift(); // the previous drift loop already stopped itself on first drag
  }

  scanBtn.addEventListener('click', doScan);
  pathInput.addEventListener('keydown', e => { if (e.key === 'Enter') doScan(); });
  depthInput.addEventListener('keydown', e => { if (e.key === 'Enter') doScan(); });

  browseBtn.addEventListener('click', async () => {
    const chosen = await window.pywebview.api.browse_folder();
    if (chosen) {
      pathInput.value = chosen;
      doScan();
    }
  });

  function runSearch() {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) return;
    const matches = currentData.nodes.filter(n => n.name.toLowerCase().includes(q));
    if (!matches.length) {
      setStatus('No matches.');
      return;
    }
    setStatus(`${matches.length} match(es).`);
    const node = matches[0];
    selectNode(node);
    const distance = 120;
    const ratio = node.x || node.y || node.z ? 1 + distance / Math.hypot(node.x, node.y, node.z) : 1;
    Graph.cameraPosition(
      { x: node.x * ratio, y: node.y * ratio, z: node.z * ratio },
      node,
      900
    );
  }
  searchBtn.addEventListener('click', runSearch);
  searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') runSearch(); });

  async function buildLegend() {
    const items = await window.pywebview.api.legend();
    legendEl.innerHTML = items.map((it, i) => `
      <div class="legend-row" style="animation-delay: ${i * 40}ms">
        <span class="swatch" style="background:${it.color}; color:${it.color};"></span>
        <span>${escapeHtml(it.label)}</span>
      </div>
    `).join('');
  }

  function initials(name) {
    const parts = String(name).trim().split(/\s+/);
    return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase() || name[0]?.toUpperCase() || '?';
  }

  function startScanFor(path) {
    chooserEl.classList.add('hidden');
    pathInput.value = path;
    doScan();
  }

  async function buildChooser() {
    chooserBackEl.classList.add('hidden');
    chooserTitleEl.textContent = 'fgraph';
    chooserSubEl.textContent = 'Whose files do you want to explore?';
    userListEl.innerHTML = `<div class="chooser-empty">Loading accounts…</div>`;

    const result = await window.pywebview.api.list_users();
    const users = result.users || [];
    if (!users.length) {
      userListEl.innerHTML = `<div class="chooser-empty">Couldn't find any accounts under ${escapeHtml(result.root || 'C:\\Users')}.</div>`;
      return;
    }
    userListEl.innerHTML = users.map(u => `
      <button class="user-card${u.isCurrentUser ? ' current' : ''}" data-name="${escapeHtml(u.name)}" data-path="${escapeHtml(u.path)}">
        <span class="user-avatar">${escapeHtml(initials(u.name))}</span>
        <span class="meta">
          <span>${escapeHtml(u.name)}</span>
          ${u.isCurrentUser ? '<span class="tag">this account</span>' : ''}
        </span>
      </button>
    `).join('');
    userListEl.querySelectorAll('.user-card').forEach(card => {
      card.addEventListener('click', () => showSubfolders(card.dataset.name, card.dataset.path));
    });
  }

  // Step 2: pick a folder inside the chosen account -- much faster to scan/test than
  // the whole profile, with "entire account" always offered as the first option.
  async function showSubfolders(name, path) {
    chooserBackEl.classList.remove('hidden');
    chooserTitleEl.textContent = name;
    chooserSubEl.textContent = 'Pick a folder to scan (or the whole account).';
    userListEl.innerHTML = `<div class="chooser-empty">Loading folders…</div>`;

    const result = await window.pywebview.api.list_subfolders(path);
    const folders = result.folders || [];
    const wholeAccountCard = `
      <button class="user-card current" data-path="${escapeHtml(path)}">
        <span class="user-avatar">${escapeHtml(initials(name))}</span>
        <span class="meta">
          <span>Entire ${escapeHtml(name)} account</span>
          <span class="tag">everything · slower</span>
        </span>
      </button>
    `;
    const folderCards = folders.map(f => `
      <button class="user-card" data-path="${escapeHtml(f.path)}">
        <span class="user-avatar">${escapeHtml(initials(f.name))}</span>
        <span class="meta"><span>${escapeHtml(f.name)}</span></span>
      </button>
    `).join('');
    userListEl.innerHTML = wholeAccountCard + folderCards;
    userListEl.querySelectorAll('.user-card').forEach(card => {
      card.addEventListener('click', () => startScanFor(card.dataset.path));
    });
  }

  chooserBackEl.addEventListener('click', buildChooser);

  async function init() {
    depthInput.value = await window.pywebview.api.default_depth();
    await buildLegend();
    await buildChooser();
  }

  // pywebviewready fires once; if it already fired before this script attached its
  // listener (a real race on some systems), window.pywebview.api is present immediately
  // and we must init directly instead of waiting for an event that will never come again.
  // A short poll is a second safety net in case neither path fires as expected.
  let started = false;
  const startOnce = () => { if (!started) { started = true; init(); } };
  if (window.pywebview && window.pywebview.api) {
    startOnce();
  } else {
    window.addEventListener('pywebviewready', startOnce);
    const poll = setInterval(() => {
      if (started) { clearInterval(poll); return; }
      if (window.pywebview && window.pywebview.api) {
        clearInterval(poll);
        startOnce();
      }
    }, 200);
  }
})();
