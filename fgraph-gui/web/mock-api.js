// Dev-only mock of the pywebview js_api bridge, so the UI can be opened and
// interacted with in a plain browser (Chrome) for debugging -- the real desktop
// app never sets ?mock=1, so this never activates outside explicit testing.
(() => {
  if (new URLSearchParams(location.search).get('mock') !== '1') return;

  const USERS = [
    { name: 'saiva', path: 'C:\\Users\\saiva', isCurrentUser: true },
    { name: 'CodexSandboxOffline', path: 'C:\\Users\\CodexSandboxOffline', isCurrentUser: false },
    { name: 'WsiAccount', path: 'C:\\Users\\WsiAccount', isCurrentUser: false },
  ];

  const SUBFOLDERS = {
    'C:\\Users\\saiva': ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos', 'OneDrive'],
  };

  function fakeGraph(root) {
    const nodes = [{ id: root, name: root.split('\\').pop(), path: root, isDir: true, size: 0, sizeHuman: '', depth: 0, leafCount: 12, color: '#5e6ad2', val: 1.1 }];
    const links = [];
    const names = ['report.docx', 'photo.jpg', 'song.mp3', 'archive.zip', 'app.exe', 'data.json', 'Subfolder A', 'Subfolder B', 'notes.md', 'video.mp4'];
    names.forEach((name, i) => {
      const id = `${root}\\${name}`;
      const isDir = name.startsWith('Subfolder');
      nodes.push({
        id, name, path: id, isDir,
        size: isDir ? 0 : (i + 1) * 123456,
        sizeHuman: isDir ? '' : `${i + 1} MB`,
        depth: 1,
        leafCount: isDir ? 3 : 0,
        color: isDir ? '#80dcdc' : '#5edc82',
        val: isDir ? 0.6 : 0.4,
        expandable: isDir, // Subfolder A/B are unexpanded aggregates for testing expand_folder
      });
      links.push({ source: root, target: id });
    });
    return { nodes, links, root };
  }

  // Larger fake tree for perf/smoothness testing (Part B) without needing a real huge
  // folder -- triggered via ?mockbig=1 alongside ?mock=1.
  function fakeBigGraph(root, totalNodes = 3000) {
    const nodes = [{ id: root, name: root.split('\\').pop(), path: root, isDir: true, size: 0, sizeHuman: '', depth: 0, leafCount: totalNodes, color: '#5e6ad2', val: 1.1 }];
    const links = [];
    const categories = [
      { ext: 'js', color: '#5adc82' }, { ext: 'md', color: '#e6dc82' }, { ext: 'png', color: '#e678dc' },
      { ext: 'mp4', color: '#78b4e6' }, { ext: 'mp3', color: '#e6a05a' }, { ext: 'zip', color: '#be5a5a' },
      { ext: 'exe', color: '#ff5a5a' }, { ext: 'json', color: '#78dcdc' },
    ];
    const folderCount = 25;
    const filesPerFolder = Math.floor((totalNodes - folderCount) / folderCount);
    let count = 1;
    for (let f = 0; f < folderCount && count < totalNodes; f++) {
      const folderId = `${root}\\folder-${f}`;
      nodes.push({ id: folderId, name: `folder-${f}`, path: folderId, isDir: true, size: 0, sizeHuman: '', depth: 1, leafCount: filesPerFolder, color: '#64dcdc', val: 0.8 });
      links.push({ source: root, target: folderId });
      count++;
      for (let i = 0; i < filesPerFolder && count < totalNodes; i++) {
        const cat = categories[i % categories.length];
        const fileId = `${folderId}\\file-${i}.${cat.ext}`;
        nodes.push({ id: fileId, name: `file-${i}.${cat.ext}`, path: fileId, isDir: false, size: (i + 1) * 1024, sizeHuman: `${i + 1} KB`, depth: 2, leafCount: 0, color: cat.color, val: 0.3 });
        links.push({ source: folderId, target: fileId });
        count++;
      }
    }
    return { nodes, links, root };
  }

  window.pywebview = {
    api: {
      async default_depth() { return 2; },
      async legend() {
        return [
          { label: 'code', color: '#5adc82' },
          { label: 'docs', color: '#e6dc82' },
          { label: 'image', color: '#e678dc' },
          { label: 'video', color: '#78b4e6' },
          { label: 'audio', color: '#e6a05a' },
          { label: 'archive', color: '#be5a5a' },
          { label: 'executable', color: '#ff5a5a' },
          { label: 'data', color: '#78dcdc' },
          { label: 'other', color: '#969696' },
          { label: 'folder (color = depth)', color: '#64dcdc' },
        ];
      },
      async list_users() { return { root: 'C:\\Users', users: USERS }; },
      async list_subfolders(path) {
        const names = SUBFOLDERS[path] || ['SubfolderX', 'SubfolderY'];
        return { root: path, folders: names.map(n => ({ name: n, path: `${path}\\${n}` })) };
      },
      async scan(path, depth) {
        console.log('[mock] scan', path, depth);
        const big = new URLSearchParams(location.search).get('mockbig') === '1';
        const cap = big ? 3000 : 500;
        for (const pct of [10, 35, 60, 85]) {
          await new Promise(r => setTimeout(r, big ? 60 : 250));
          window.__scanProgress && window.__scanProgress(Math.round(cap * pct / 100), cap, `${path}\\fake-subdir-${pct}`);
        }
        await new Promise(r => setTimeout(r, big ? 60 : 250));
        window.__scanProgress && window.__scanProgress(cap, cap, null);
        return big ? fakeBigGraph(path, cap) : fakeGraph(path);
      },
      async expand_folder(path, depth) {
        console.log('[mock] expand_folder', path, depth);
        await new Promise(r => setTimeout(r, 200));
        const childDepth = (parseInt(depth, 10) || 0) + 1;
        const names = ['inner-file-1.txt', 'inner-file-2.png', 'inner-folder'];
        const children = names.map((name, i) => {
          const id = `${path}\\${name}`;
          const isDir = name === 'inner-folder';
          return {
            id, name, path: id, isDir,
            size: isDir ? 0 : (i + 1) * 2048,
            sizeHuman: isDir ? '' : `${i + 1} KB`,
            depth: childDepth,
            leafCount: isDir ? 4 : 0,
            color: isDir ? '#64dcdc' : '#5adc82',
            val: isDir ? 0.6 : 0.3,
            expandable: isDir,
          };
        });
        return { path, children, error: null };
      },
      async browse_folder() { return null; },
      async open_path(path) { console.log('[mock] open_path', path); return { ok: true }; },
      async client_error(msg) { console.error('[mock client_error]', msg); },
    },
  };
  window.dispatchEvent(new Event('pywebviewready'));
})();
