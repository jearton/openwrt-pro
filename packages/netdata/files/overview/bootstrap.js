/* SPDX-License-Identifier: GPL-3.0-or-later
 * Native Netdata 2.13 dashboard cache adapter. Run before the native app starts.
 * It supplies layout data only; all charts are rendered by the bundled app.
 */
'use strict';

(async function () {
  const status = document.getElementById('status');
  const recovery = document.getElementById('recovery');
  document.getElementById('retry').addEventListener('click', () => location.reload());

  async function json(path) {
    const response = await fetch(path, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error('Monitor resource unavailable');
    return response.json();
  }

  function openCache() {
    return new Promise((resolve, reject) => {
      let settled = false;
      const fail = message => {
        settled = true;
        clearTimeout(timer);
        reject(new Error(message));
      };
      const timer = setTimeout(() => fail('Browser storage timed out'), 15000);
      let request;
      try { request = indexedDB.open('netdata'); }
      catch (_) { fail('Browser storage unavailable'); return; }
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains('netdata-cache'))
          request.result.createObjectStore('netdata-cache');
      };
      request.onerror = () => fail('Browser storage unavailable');
      request.onblocked = () => fail('Browser storage blocked');
      request.onsuccess = () => {
        const db = request.result;
        if (settled) { db.close(); return; }
        clearTimeout(timer);
        settled = true;
        if (!db.objectStoreNames.contains('netdata-cache')) {
          db.close();
          reject(new Error('Unsupported dashboard cache schema'));
        } else {
          resolve(db);
        }
      };
    });
  }

  function hasSavedDashboard(row, id) {
    const value = row && row.value;
    return value && value.id === id && Number.isInteger(value.version) && value.version >= 1 &&
      value.snapshot && typeof value.snapshot === 'object';
  }

  function initialize(db, dashboard) {
    return new Promise((resolve, reject) => {
      // One transaction makes simultaneous first visits harmless. Never replace
      // a native saved record, including an intentionally empty user dashboard.
      const tx = db.transaction('netdata-cache', 'readwrite');
      const store = tx.objectStore('netdata-cache');
      const request = store.get(dashboard.id);
      request.onsuccess = () => {
        const row = request.result;
        if (hasSavedDashboard(row, dashboard.id)) return;
        if (row != null && !(row.value && row.value.id === dashboard.id && row.value.version === 0)) {
          tx.abort();
          return;
        }
        if (!hasSavedDashboard(row, dashboard.id))
          store.put({value: dashboard, timestamp: Date.now()}, dashboard.id);
      };
      tx.oncomplete = resolve;
      tx.onabort = tx.onerror = () => reject(new Error('Dashboard initialization failed'));
    });
  }

  function makeDashboard(preset, contexts) {
    if (preset.schema !== 1 || preset.dashboard.id !== 'local-custom-dashboard')
      throw new Error('Unsupported overview template');
    const cards = {};
    const layout = [];
    function add(spec) {
      const {layout: box, optional, ...card} = spec;
      if (optional && !card.contextScope.some(id => contexts[id])) return;
      cards[card.id] = card.type === 'text' ? card : {...preset.chartDefaults, ...card};
      layout.push({id: card.id, minWidth: 1, minHeight: 1, moved: false, ...box});
    }
    preset.cards.forEach(add);

    const temperatures = Object.keys(contexts).filter(id =>
      /celsius|°c|degrees?\s*c/i.test(contexts[id].units || ''));
    const fans = Object.keys(contexts).filter(id => /\brpm\b/i.test(contexts[id].units || ''));
    const unavailable = [];
    if (!temperatures.length) unavailable.push('温度：未检测到指标');
    if (!fans.length) unavailable.push('风扇转速：未检测到指标');
    if (unavailable.length) add({id: 'owrt-sensor-status', type: 'text', textType: 'body',
      textAlign: 'left', text: unavailable.join('；') + '。当前硬件或采集器尚未提供这些数据。',
      layout: {left: 0, top: 40.5, width: 12, height: 2}});
    if (temperatures.length) add({id: 'owrt-temperatures', type: 'chart',
      title: '温度', customTitle: '温度', contextScope: temperatures,
      layout: {left: 0, top: 42.5, width: 6, height: 7}});
    if (fans.length) add({id: 'owrt-fans', type: 'chart', title: '风扇转速',
      customTitle: '风扇转速', contextScope: fans,
      layout: {left: temperatures.length ? 6 : 0, top: 42.5, width: 6, height: 7}});

    const now = new Date().toISOString();
    return {...preset.dashboard, version: 1, disabled: false, createdAt: now, updatedAt: now,
      snapshot: {uiState: {layout: {A: layout}, containerIds: ['A'],
        containers: {A: {name: 'System Overview'}}, cards, respectNodesScope: true}}};
  }

  try {
    const base = new URL('../', location.href);
    const [preset, info] = await Promise.all([
      json(new URL('preset.json', location.href)),
      json(new URL('api/v3/info', base))
    ]);
    const agent = info.agents && info.agents.find(item => item.ai === 0);
    const version = agent && agent.application && agent.application.package.version;
    if (!version || version.replace(/^v/, '') !== preset.agentVersion || !agent.nm)
      throw new Error('Unsupported monitor version');
    // Native 2.13 routes use its normalized space slug, not the display name
    // (the factory hostname "OpenWrt" becomes "openwrt").
    const space = agent.nm.trim().replace(/\s+/g, '-').normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9-]/g, '').toLowerCase();
    if (!space) throw new Error('Unsupported native space name');
    let metadata;
    for (let attempt = 0; attempt < 10; attempt++) {
      metadata = await json(new URL('api/v3/contexts', base));
      if (metadata.contexts && metadata.contexts['system.cpu'] && metadata.contexts['system.ram']) break;
      if (attempt === 9) throw new Error('Monitor collectors not ready');
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    const db = await openCache();
    try { await initialize(db, makeDashboard(preset, metadata.contexts)); }
    finally { db.close(); }
    // The path is the native local Dashboard route, with no cloud identity or
    // hardware-specific node IDs in the template.
    location.replace(new URL('v3/spaces/' + encodeURIComponent(space) +
      '/rooms/local/dashboard', base).href);
  } catch (error) {
    console.error('System Overview initialization:', error);
    status.textContent = '暂时无法加载系统概览。请检查监控服务和浏览器本地存储权限后重试。';
    recovery.hidden = false;
  }
})();
