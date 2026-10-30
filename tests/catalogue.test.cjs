// Exercise the actual generated script against a small DOM adapter, without
// network or npm dependencies. Browser layout is checked separately.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../catalogue.html'), 'utf8');
const payload = html.match(/<script id="catalogue-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.value = ''; this.dataset = {}; this.listeners = {}; this.textContent = ''; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = [...nodes]; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
}
function app() {
  const ids = Object.fromEntries(['catalogue-data', 'metrics', 'query', 'language', 'kind', 'curated', 'curated-count', 'results', 'result-count', 'more'].map(id => [id, new Element('div')]));
  ids['catalogue-data'].textContent = payload;
  const context = { document: { getElementById: id => ids[id], createElement: tag => new Element(tag) } };
  vm.runInNewContext(script, context);
  return {
    ids,
    versions: () => ids.curated.children.filter(n => n.dataset.versionId).map(n => n.dataset.versionId),
    entries: () => ids.results.children.filter(n => n.dataset.discoveryId).map(n => n.dataset.discoveryId),
    set(id, value) { ids[id].value = value; ids[id].listeners[id === 'query' ? 'input' : 'change'](); },
    more() { ids.more.listeners.click(); },
  };
}

test('initial counts and discovery pagination', () => {
  const a = app();
  assert.equal(a.versions().length, 17);
  assert.equal(a.entries().length, 60);
  assert.match(a.ids['result-count'].textContent, /509/);
  a.more(); assert.equal(a.entries().length, 120);
  for (let i = 0; i < 10; i++) a.more();
  assert.equal(a.entries().length, 509);
  assert.equal(new Set(a.entries()).size, 509);
  assert.equal(a.ids.more.hidden, true);
});
test('curated-only author and multiword searches', () => {
  const a = app(); a.set('query', 'Kots 1902');
  assert(a.versions().includes('ru-kots-1902'));
  assert(a.versions().every(id => id.startsWith('ru-kots-')));
  a.set('query', 'Коц'); assert(a.versions().includes('ru-kots-1902'));
  a.set('query', 'Kerr 1919'); assert(a.versions().includes('en-kerr-iww-1919'));
  a.set('query', 'ru-kots-1902'); assert.deepEqual(a.versions(), ['ru-kots-1902']);
});
test('Chinese and English language aliases filter both result groups', () => {
  const a = app(); a.set('query', '中文');
  assert.equal(a.versions().length, 8);
  assert(a.entries().length > 0);
  a.set('query', ''); a.set('language', 'Russian');
  assert.equal(a.versions().length, 2);
  assert(a.entries().length > 0);
});
test('discovery-type filter leaves matching curated records visible', () => {
  const a = app(); a.set('kind', 'supporting');
  assert.equal(a.versions().length, 17);
  assert.match(a.ids['result-count'].textContent, /121/);
  a.set('language', 'Russian'); a.set('query', 'Kots');
  assert(a.versions().includes('ru-kots-1902'));
});
test('empty search, filter resets and linked records', () => {
  const a = app(); a.more(); a.set('query', 'no-such-version-97463');
  assert.equal(a.versions().length, 0); assert.equal(a.entries().length, 0);
  assert.equal(a.ids.more.hidden, true);
  a.set('query', ''); assert.equal(a.entries().length, 60);
  a.set('kind', 'reviewed');
  const expected = JSON.parse(payload).entries.filter(r => r.canonical_version_ids.length).length;
  assert.equal(a.entries().length, expected);
});
