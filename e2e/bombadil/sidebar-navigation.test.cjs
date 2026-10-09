const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');
const regression = require('./sidebar-navigation.regression.json');

const propertyName = 'sidebarNavigationEventuallySelectsTarget';
const specification = fs.readFileSync(path.join(__dirname, 'specification.ts'), 'utf8');

// Execute the checked-in TypeScript declarations, not a JavaScript copy of the
// predicate. Only this property's temporal operators are adapted below. This
// does not emulate Bombadil's browser, action serialization, or complete engine;
// the real pinned Bombadil run remains the integration check.
function compile(source, includeDom = false) {
  const ast = ts.createSourceFile('specification.ts', source, ts.ScriptTarget.Latest, true);
  const functions = ast.statements.filter(ts.isFunctionDeclaration);
  const declarations = ast.statements
    .filter(ts.isVariableStatement)
    .flatMap((statement) => Array.from(statement.declarationList.declarations));
  const property = declarations.find(
    (declaration) => declaration.name.getText(ast) === propertyName,
  );
  assert.ok(property, `Missing actual ${propertyName} declaration`);
  const projection = includeDom
    ? declarations.find((declaration) => declaration.name.getText(ast) === 'ui').initializer
        .arguments[0]
    : null;
  const names = functions.map((fn) => fn.name.text);
  const selected = [
    ...functions.map((fn) => fn.getText(ast)),
    `const ${property.getText(ast)};`,
    ...(projection ? [`const readUi = ${projection.getText(ast)};`] : []),
    `return { ${[...names, propertyName, ...(projection ? ['readUi'] : [])].join(', ')} };`,
  ].join('\n');
  const compiled = ts.transpileModule(selected, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None },
  }).outputText;
  return new Function('ui', 'always', 'now', 'eventually', compiled);
}

const createCurrent = compile(specification, true);
const createOriginal = compile(regression.originalSpecification);

// Small sampled-time adapter for always(now(...).implies(eventually(...).within)).
// Bombadil 0.6.1 captures a deadline and thunk once per obligation and checks
// expiry before the predicate. A later always sample creates an independent
// obligation. Passing requires every triggered obligation to have resolved;
// a truncated trace with pending work is not reported as a pass.
function harness(create = createCurrent) {
  const ui = { current: null };
  const api = create(
    ui,
    (predicate) => predicate,
    (predicate) => ({ implies: (consequent) => ({ predicate, consequent }) }),
    (predicate) => ({
      within(duration, unit) {
        assert.equal(unit, 'seconds');
        return { predicate, durationMs: duration * 1000 };
      },
    }),
  );
  return {
    api,
    run(snapshots) {
      const pending = [];
      const failures = [];
      let previousTime = -Infinity;
      for (const snapshot of snapshots) {
        assert.ok(snapshot.timeMs >= previousTime, 'Snapshots must be chronological');
        previousTime = snapshot.timeMs;
        ui.current = snapshot;
        const evaluate = (obligation) => {
          if (snapshot.timeMs > obligation.deadlineMs) {
            failures.push({ startedMs: obligation.startedMs, failedMs: snapshot.timeMs });
            return false;
          }
          return !obligation.predicate();
        };
        for (let index = pending.length - 1; index >= 0; index -= 1) {
          if (!evaluate(pending[index])) pending.splice(index, 1);
        }
        const requirement = api[propertyName]();
        if (requirement.predicate()) {
          const obligation = {
            startedMs: snapshot.timeMs,
            deadlineMs: snapshot.timeMs + requirement.consequent.durationMs,
            predicate: requirement.consequent.predicate,
          };
          if (evaluate(obligation)) pending.push(obligation);
        }
      }
      return { failures, pending };
    },
  };
}

const A = 'a0aa2d41-e089-5e5a-89b9-1a72e142957f';
const B = '37359844-e31c-5384-ab1d-36051ed8466c';
const C = 'c31eaf72-e8ec-5adb-bb55-00c3bdd87b7b';
const open = (id, index = 1) => ({ Click: { name: `Open conversation ${index}`, content: id } });
function snapshot(timeMs, overrides = {}) {
  return {
    timeMs,
    lastAction: 'Wait',
    path: `/c/${C}`,
    activeConversationIds: [C],
    activeConversationIndexes: [3],
    messageIds: ['message-1'],
    ...overrides,
  };
}
const selected = (id) => ({ path: `/c/${id}`, activeConversationIds: [id] });
function assertPass(snapshots) {
  const result = harness().run(snapshots);
  assert.deepEqual(result.failures, []);
  assert.equal(result.pending.length, 0, 'A finite trace must resolve all triggered obligations');
}
function assertFailure(snapshots, startedMs = 0) {
  const result = harness().run(snapshots);
  assert.ok(
    result.failures.some((failure) => failure.startedMs === startedMs),
    JSON.stringify(result),
  );
  return result;
}

test('the observed superseded-navigation trace fails the original property and passes the fix', () => {
  assert.equal(regression.rows.length, 44);
  const observed = regression.rows.map(
    ([traceLine, elapsedMicros, lastAction, route, indexes, count]) =>
      snapshot(elapsedMicros / 1000, {
        traceLine,
        lastAction,
        path: route,
        activeConversationIndexes: indexes,
        messageIds: Array.from({ length: count }, (_, index) => `message-${index}`),
      }),
  );
  const original = harness(createOriginal).run(observed);
  assert.deepEqual(original.failures, [{ startedMs: 56775.127, failedMs: 66933.325 }]);

  // Reconstructed metadata, NOT captured IDs: click targets use the observed
  // resulting route; active rows use that route except known stale selections
  // at 196 and 210. All original timestamps/actions/routes/indexes/counts remain.
  const staleSelection = new Map([
    [196, 'b596b8dd-e944-5170-b151-4661e10fc203'],
    [210, C],
  ]);
  const reconstructed = observed.map((state) => ({
    ...state,
    lastAction: /^Open conversation \d+$/.test(state.lastAction?.Click?.name ?? '')
      ? { Click: { ...state.lastAction.Click, content: state.path.slice('/c/'.length) } }
      : state.lastAction,
    activeConversationIds: state.activeConversationIndexes.length
      ? [staleSelection.get(state.traceLine) ?? state.path.slice('/c/'.length)]
      : [],
  }));
  assertPass(reconstructed);
});

for (const [description, finalState] of [
  ['wrong route with correct active ID', { path: `/c/${B}`, activeConversationIds: [A] }],
  ['correct route with wrong active ID', { path: `/c/${A}`, activeConversationIds: [B] }],
  ['correct route with no active ID', { path: `/c/${A}`, activeConversationIds: [] }],
  ['correct route with two active IDs', { path: `/c/${A}`, activeConversationIds: [A, B] }],
  ['an extra active row with no ID', { ...selected(A), activeConversationIndexes: [1, 2] }],
  ['correct route and active ID with empty messages', { ...selected(A), messageIds: [] }],
]) {
  test(`an unsuperseded navigation fails for ${description}`, () => {
    assertFailure([
      snapshot(0, { lastAction: open(A) }),
      snapshot(9999, finalState),
      snapshot(10001, finalState),
    ]);
  });
}

test('loading can finish before the original deadline', () => {
  assertPass([
    snapshot(0, { lastAction: open(A), ...selected(A), messageIds: [] }),
    snapshot(9999, selected(A)),
    snapshot(10001, selected(A)),
  ]);
});

test('a different sidebar target can supersede before the deadline', () => {
  assertPass([
    snapshot(0, { lastAction: open(A) }),
    snapshot(9999, { lastAction: open(B, 2), ...selected(B), messageIds: [] }),
    snapshot(10001, selected(B)),
  ]);
});

test('the exact deadline still permits rendering or explicit supersession', () => {
  assertPass([snapshot(0, { lastAction: open(A) }), snapshot(10000, selected(A))]);
  assertPass([
    snapshot(0, { lastAction: open(A) }),
    snapshot(10000, { lastAction: open(B, 2), ...selected(B) }),
  ]);
});

test('supersession after expiry cannot forgive the old obligation', () => {
  const result = assertFailure([
    snapshot(0, { lastAction: open(A) }),
    snapshot(10000.001, { lastAction: open(B, 2), ...selected(B) }),
  ]);
  assert.deepEqual(result.failures, [{ startedMs: 0, failedMs: 10000.001 }]);
});

test('rendering the requested target after expiry is also too late', () => {
  assertFailure([snapshot(0, { lastAction: open(A) }), snapshot(10001, selected(A))]);
});

test('same-target repeated clicks cannot reset the first deadline, even after reordering', () => {
  const result = assertFailure([
    snapshot(0, { lastAction: open(A, 5) }),
    snapshot(9000, { lastAction: open(A, 1) }),
    snapshot(10001, selected(A)),
  ]);
  assert.deepEqual(result.failures, [{ startedMs: 0, failedMs: 10001 }]);
  assert.equal(result.pending.length, 0, 'The second obligation can succeed while the first fails');
});

for (const [description, lastAction] of [
  ['Wait', 'Wait'],
  ['Reload', 'Reload'],
  ['model click', { Click: { name: 'Model selector', content: B } }],
  ['composer click', { Click: { name: 'Message input', content: B } }],
  ['same-conversation branch', { Click: { name: 'Create branch from parallel response' } }],
  ['sidebar click without ID', { Click: { name: 'Open conversation 2' } }],
]) {
  test(`${description} does not excuse an unresolved target or arbitrary route change`, () => {
    assertFailure([
      snapshot(0, { lastAction: open(A) }),
      snapshot(5000, { lastAction, ...selected(B) }),
      snapshot(10001, selected(B)),
    ]);
  });
}

test('explicit New conversation supersedes an outstanding navigation', () => {
  assertPass([
    snapshot(0, { lastAction: open(A) }),
    snapshot(5000, {
      lastAction: { Click: { name: 'New conversation' } },
      path: '/c/new',
      activeConversationIds: [],
      messageIds: [],
    }),
    snapshot(10001, { path: '/c/new', activeConversationIds: [], messageIds: [] }),
  ]);
});

test('a route change to /c/new without its explicit action does not supersede', () => {
  assertFailure([
    snapshot(0, { lastAction: open(A) }),
    snapshot(5000, { path: '/c/new', activeConversationIds: [], messageIds: [] }),
    snapshot(10001, { path: '/c/new', activeConversationIds: [], messageIds: [] }),
  ]);
});

test('the latest of several different targets retains its own deadline and must render', () => {
  const trace = [
    snapshot(0, { lastAction: open(A), messageIds: [] }),
    snapshot(3000, { lastAction: open(B, 2), messageIds: [] }),
    snapshot(6000, { lastAction: open(C, 3), messageIds: [] }),
  ];
  assertPass([...trace, snapshot(15999, selected(C))]);
  const result = assertFailure([...trace, snapshot(16001, selected(B))], 6000);
  assert.deepEqual(result.failures, [{ startedMs: 6000, failedMs: 16001 }]);
});

test('only a named sidebar click with valid ID content starts or supersedes an obligation', () => {
  const { clickedConversationId, navigationWasSuperseded } = harness().api;
  assert.equal(clickedConversationId(open(A, 5)), A);
  assert.equal(navigationWasSuperseded(open(A, 1), A), false);
  assert.equal(navigationWasSuperseded(open(B, 5), A), true);
  for (const action of [
    null,
    undefined,
    1,
    'Wait',
    'Reload',
    {},
    { Click: null },
    { Click: 'Open conversation 1' },
    { Click: { content: A } },
    { Click: { name: 'Open conversation 1' } },
    ...[null, undefined, '', 'new', 42, {}].map((content) => open(content)),
    ...['Model selector', 'Open conversation 1 extra', 'Open conversation x'].map((name) => ({
      Click: { name, content: B },
    })),
  ]) {
    assert.equal(clickedConversationId(action), null, JSON.stringify(action));
    assert.equal(navigationWasSuperseded(action, A), false, JSON.stringify(action));
  }
});

// Explicit DOM seam, not a reimplementation of conversationTargets/readUi:
// rows provide only attributes, selection, geometry, and hit-testing. The actual
// production selectors, visibility checks, extraction, and action creation run.
function documentState(rows, route = `/c/${C}`) {
  const elements = rows.map(({ id, active = false, visible = true }, index) => ({
    id: `row-${index}`,
    textContent: `Conversation ${index + 1}`,
    getAttribute: (name) => (name === 'data-conversation-id' ? (id ?? null) : null),
    querySelector: (selector) => (selector === '[aria-current="page"]' && active ? {} : null),
    getBoundingClientRect: () => ({
      left: 0,
      top: index * 20,
      width: visible ? 100 : 0,
      height: 20,
    }),
    contains: () => false,
  }));
  return {
    lastAction: 'Wait',
    window: {
      location: { pathname: route },
      innerWidth: 1000,
      innerHeight: 1000,
      getComputedStyle: () => ({ display: 'block', visibility: 'visible', pointerEvents: 'auto' }),
    },
    document: {
      activeElement: null,
      querySelector: () => null,
      querySelectorAll: (selector) => (selector === '[data-testid="convo-item"]' ? elements : []),
      elementFromPoint: (_x, y) => elements[Math.floor(y / 20)] ?? null,
    },
  };
}

test('DOM extraction carries a stable ID in Click.content and retains active indexes', () => {
  const { conversationTargets, clickAction, readUi, clickedConversationId } = harness().api;
  const dom = documentState([
    { id: C, active: true },
    { id: A },
    { id: B, visible: false },
    {},
    { id: 'new' },
  ]);
  const targets = conversationTargets(dom);
  assert.deepEqual(targets, [{ name: 'Open conversation 2', content: A, point: { x: 50, y: 30 } }]);
  assert.equal(clickedConversationId(clickAction(targets[0])[0]), A);
  const state = readUi(dom);
  assert.deepEqual(state.activeConversationIds, [C]);
  assert.deepEqual(state.activeConversationIndexes, [1]);
  assert.deepEqual(state.conversationItems, targets);
});

test('the actual DOM extractor and property succeed when the target moves from row 2 to row 1', () => {
  const { conversationTargets, clickAction, readUi } = harness().api;
  const before = documentState([{ id: C, active: true }, { id: A }]);
  const click = clickAction(conversationTargets(before)[0])[0];
  const after = readUi(documentState([{ id: A, active: true }, { id: C }], `/c/${A}`));
  assert.deepEqual(after.activeConversationIndexes, [1]);
  assert.deepEqual(after.activeConversationIds, [A]);
  assertPass([
    snapshot(0, { lastAction: click }),
    snapshot(200, { ...after, messageIds: ['rendered-message'] }),
  ]);
});

test('an active DOM row without an ID cannot hide a second active selection', () => {
  const state = harness().api.readUi(
    documentState([{ id: A, active: true }, { active: true }], `/c/${A}`),
  );
  assert.deepEqual(state.activeConversationIds, [A]);
  assert.deepEqual(state.activeConversationIndexes, [1, 2]);
  assertFailure([
    snapshot(0, { lastAction: open(A) }),
    snapshot(9999, { ...state, messageIds: ['rendered-message'] }),
    snapshot(10001, { ...state, messageIds: ['rendered-message'] }),
  ]);
});
