import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

test('recovery remains visible after apply-error refresh and later reload', async () => {
  const source = readFileSync(new URL('../admin-settings-panel.py', import.meta.url), 'utf8');
  const script = source.match(/<script>([\s\S]*?)<\/script>/)![1];
  const nodes = new Map();
  class Element {
    textContent = ''; children: Element[] = []; disabled = false; handlers = {};
    dataset = {}; value = ''; tagName = 'DIV';
    classes = new Set<string>();
    classList = {
      add: (x) => this.classes.add(x), remove: (x) => this.classes.delete(x),
      contains: (x) => this.classes.has(x),
      toggle: (x, on) => on ? this.classes.add(x) : this.classes.delete(x),
    };
    appendChild(x) { this.children.push(x); }
    append(...xs) { this.children.push(...xs); }
    replaceChildren(...xs) { this.children = xs; }
    addEventListener(name, fn) { this.handlers[name] = fn; }
  }
  for (const match of source.matchAll(/id="([^"]+)"/g)) nodes.set('#' + match[1], new Element());
  let held = false;
  const context = vm.createContext({
    document: {querySelector: (x) => nodes.get(x), querySelectorAll: () => [], createElement: () => new Element()},
    fetch: async (path) => {
      if (path === '/api/apply') {
        held = true;
        return {ok: false, json: async () => ({error: 'Runtime outcome uncertain'})};
      }
      return {ok: true, json: async () => ({state: {settings: [], groups: [], recovery_required: held}, password_configured: true})};
    }, confirm: () => true, alert: () => {}, location: {reload: () => {}},
  });
  vm.runInContext(script, context);
  await Bun.sleep(0);
  vm.runInContext('previewPayload={updates:{SEARCH:"true"}}', context);
  await nodes.get('#applyBtn').handlers.click();
  expect(nodes.get('#messages').children.map((x) => x.textContent).join()).toContain('Runtime outcome uncertain');
  expect(nodes.has('#recoveryNotice')).toBe(true);
  expect(nodes.get('#recoveryNotice').classList.contains('hidden')).toBe(false);
  await nodes.get('#refreshBtn').handlers.click();
  expect(nodes.get('#recoveryNotice').classList.contains('hidden')).toBe(false);
  expect(nodes.get('#previewBtn').disabled).toBe(true);
  await vm.runInContext('load()', context);
  expect(nodes.get('#recoveryNotice').classList.contains('hidden')).toBe(false);
});
