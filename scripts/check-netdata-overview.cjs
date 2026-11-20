#!/usr/bin/env node
/* Integration acceptance against a running, isolated Netdata 2.13.0 agent.
 * PLAYWRIGHT_MODULE and CHROME_EXECUTABLE may point to an installed runtime.
 * Does not change the agent or its network; browser profiles are disposable.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const entry = new URL(process.argv[2]);
const out = path.resolve(process.argv[3] || 'netdata-acceptance');
const base = new URL('../', entry);
fs.mkdirSync(out, {recursive: true});
const report = {entry: entry.href, externalRequests: [], cases: []};

async function cache(page, replacement) {
  return page.evaluate(replacement => new Promise((resolve, reject) => {
    const request = indexedDB.open('netdata');
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction('netdata-cache', replacement ? 'readwrite' : 'readonly');
      const store = tx.objectStore('netdata-cache');
      const row = store.get('local-custom-dashboard');
      let value;
      row.onsuccess = () => {
        value = replacement || row.result;
        if (replacement) store.put(replacement, 'local-custom-dashboard');
      };
      tx.oncomplete = () => { db.close(); resolve(value); };
      tx.onabort = () => { db.close(); reject(tx.error); };
    };
  }), replacement);
}

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROME_EXECUTABLE ? {executablePath: process.env.CHROME_EXECUTABLE} : {})});
  let current;
  async function fresh() {
    const context = await browser.newContext({viewport: {width: 1600, height: 1100},
      serviceWorkers: 'block', locale: 'en-US'});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.origin === entry.origin) return route.continue();
      report.externalRequests.push(url.origin);
      return route.abort('blockedbyclient');
    });
    const page = await context.newPage();
    current = page;
    return {context, page};
  }
  async function load(page, title = 'System Overview · 系统概览') {
    await page.goto(entry.href);
    await page.waitForURL(/\/v3\/spaces\/.+\/rooms\/local\/dashboard/);
    await page.getByText(title, {exact: true}).waitFor();
    await page.waitForFunction(() => document.querySelectorAll('canvas').length >= 8);
  }
  async function api(page, suffix) {
    return page.evaluate(async url => {
      const r = await fetch(url); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json();
    }, new URL(suffix, base).href);
  }
  try {
    const a = await fresh();
    await load(a.page);
    const seeded = await cache(a.page);
    const cards = Object.values(seeded.value.snapshot.uiState.cards);
    assert.equal(seeded.value.version, 1);
    assert.equal(cards.filter(c => ['gauge', 'easypiechart'].includes(c.chartLibrary)).length, 6);
    assert(cards.some(c => c.contextScope?.includes('system.cpu') && c.chartLibrary === 'dygraph'));
    const me = await api(a.page, 'api/v3/me');
    assert.equal(me.auth, 'none'); assert.equal(me.cloud_account_id, null);
    const values = {};
    for (const context of ['system.cpu', 'system.ram', 'system.io', 'system.net']) {
      const response = await api(a.page, `api/v3/data?contexts=${context}&after=-45&points=3&format=json&options=jsonwrap`);
      assert(response.result?.data?.some(row => row.slice(1).some(n => typeof n === 'number' && Number.isFinite(n))), context);
      values[context] = {labels: response.result.labels, rows: response.result.data.length};
    }
    await a.page.screenshot({path: path.join(out, 'overview.png')});
    report.cases.push({name: 'fresh anonymous browser, offline resources, native charts and live data', status: 'passed', values, cards: cards.length});

    await a.page.getByTestId('dashboardHeader-edit-button').click();
    await a.page.getByPlaceholder('Untitled Dashboard').fill('Preserved local overview');
    await a.page.getByTestId('textCardForm').first().fill('Preserved CPU and network overview');
    await a.page.getByTestId('textCardForm').first().press('Tab');
    await a.page.getByTestId('dashboardHeaderActionBar-save-button').click();
    await a.page.waitForFunction(() => document.querySelector('[data-testid="dashboardHeaderActionBar-save-button"]')?.disabled);
    await a.page.getByRole('button', {name: 'Exit', exact: true}).click();
    const saved = await cache(a.page);
    assert.equal(saved.value.name, 'Preserved local overview');
    assert(saved.value.version > 1);
    await load(a.page, 'Preserved CPU and network overview');
    assert.deepEqual(await cache(a.page), saved);
    report.cases.push({name: 'native editor save and repeat entry preserve customized layout', status: 'passed'});

    const b = await fresh();
    await load(b.page);
    const independent = await cache(b.page);
    assert.deepEqual(independent.value.snapshot, seeded.value.snapshot);
    assert.equal(independent.value.name, 'System Overview');
    await b.context.close();
    report.cases.push({name: 'second empty browser storage automatically loads the same preset', status: 'passed'});

    // User intentionally clearing a dashboard is also a saved customization.
    const empty = structuredClone(saved);
    empty.value.snapshot.uiState.cards = {};
    empty.value.snapshot.uiState.layout = {A: []};
    await cache(a.page, empty);
    await a.page.goto(entry.href); await a.page.waitForURL(/\/rooms\/local\/dashboard/);
    assert.deepEqual(await cache(a.page), empty);
    report.cases.push({name: 'intentionally empty saved layout is not overwritten', status: 'passed'});
    const unknown = {value: {id: 'other-format'}, timestamp: 1};
    await cache(a.page, unknown);
    await a.page.goto(entry.href); await a.page.locator('#recovery').waitFor({state: 'visible'});
    assert.deepEqual(await cache(a.page), unknown);
    report.cases.push({name: 'unknown existing cache fails visibly without data loss', status: 'passed'});
    await a.context.close();

    const denied = await fresh();
    await denied.context.addInitScript(() => {
      Object.defineProperty(window, 'indexedDB', {value: {open() {throw new DOMException('Test storage disabled', 'SecurityError');}}});
    });
    await denied.page.goto(entry.href);
    await denied.page.locator('#recovery').waitFor({state: 'visible'});
    assert.equal(new URL(denied.page.url()).pathname, entry.pathname);
    report.cases.push({name: 'denied browser storage offers recovery instead of blank native dashboard', status: 'passed'});
    await denied.context.close();
    report.status = 'passed';
  } catch (error) {
    report.status = 'failed'; report.error = error.message;
    if (current && !current.isClosed()) await current.screenshot({path: path.join(out, 'failure.png')}).catch(() => {});
    throw error;
  } finally {
    fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    await browser.close();
    console.log(JSON.stringify(report, null, 2));
  }
})().catch(() => { process.exitCode = 1; });
