const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

const root = path.resolve(__dirname, '../..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const hookFile = 'client/src/hooks/SSE/useStepHandler.ts';
const messagesFile = 'client/src/utils/messages.ts';
const groupingFile = 'client/src/components/Chat/Messages/Content/ParallelContent.tsx';
const activityFile = 'client/src/utils/activityLabels.ts';
const resumableFile = 'client/src/hooks/SSE/useResumableSSE.ts';

function extract(file, name) {
  const ast = ts.createSourceFile(file, read(file), ts.ScriptTarget.Latest, true);
  let declaration;
  function visit(node) {
    if (ts.isFunctionDeclaration(node) && node.name?.text === name) {
      declaration = node.getText(ast);
    } else if (ts.isVariableDeclaration(node) && node.name.getText(ast) === name) {
      declaration = `const ${node.getText(ast)};`;
    }
    ts.forEachChild(node, visit);
  }
  visit(ast);
  assert.ok(declaration, `Missing actual ${name} declaration in ${file}`);
  return declaration.replace(/^export /, '');
}

function compile(source) {
  return ts.transpileModule(source, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  }).outputText;
}

const ContentTypes = {
  TEXT: 'text',
  THINK: 'think',
  TOOL_CALL: 'tool_call',
  AGENT_UPDATE: 'agent_update',
  IMAGE_FILE: 'image_file',
  IMAGE_URL: 'image_url',
  SUMMARY: 'summary',
  ERROR: 'error',
  ACTIVITY_LABEL: 'activity_label',
};
const StepEvents = Object.fromEntries(
  [
    'ON_RUN_STEP',
    'ON_AGENT_UPDATE',
    'ON_MESSAGE_DELTA',
    'ON_REASONING_DELTA',
    'ON_RUN_STEP_DELTA',
    'ON_RUN_STEP_COMPLETED',
    'ON_RUN_STEP_CLOSED',
    'ON_SUMMARIZE_START',
    'ON_SUMMARIZE_DELTA',
    'ON_SUMMARIZE_COMPLETE',
    'ON_SUBAGENT_UPDATE',
    'ON_SANDBOX_STARTING',
    'ON_PTC_TOOL_CALL',
  ].map((name) => [name, name.toLowerCase()]),
);
const StepTypes = { MESSAGE_CREATION: 'message_creation', TOOL_CALLS: 'tool_calls' };
const primary = 'agent_primary';
const secondary = 'agent_secondary____1';

// Execute the complete checked-in hook, with only its React/Recoil/import and
// scheduling seams mocked. Initial placeholders, grouping, and the resumable
// activity-label callback also execute their actual declarations. These are
// handler regressions, not a browser/provider
// integration test or a claim about which event caused a saved Bombadil trace.
const hookSource = compile(read(hookFile));
const activitySource = compile(read(activityFile));
const activityHandlerSource = compile(
  `${extract(resumableFile, 'applyActivityLabelToMessages')}\n` +
    'globalThis.applyActivityLabelToMessages = applyActivityLabelToMessages;',
);
const helpersSource = compile(
  [
    // These cases deliberately use real agent IDs, so ephemeral encoding is not used.
    'const isEphemeralAgentId = () => false;',
    "const appendAgentIdSuffix = (id, index) => id + '____' + index;",
    extract(messagesFile, 'createDualMessageContent'),
    extract(groupingFile, 'groupParallelContent'),
    'globalThis.createDualMessageContent = createDualMessageContent;',
    'globalThis.groupParallelContent = groupParallelContent;',
  ].join('\n'),
);

function harness(initialContent) {
  const frames = new Map();
  let nextFrame = 0;
  const context = vm.createContext({
    exports: {},
    console,
    Date,
    requestAnimationFrame(callback) {
      frames.set(++nextFrame, callback);
      return nextFrame;
    },
    cancelAnimationFrame: (id) => frames.delete(id),
    require(id) {
      if (id === 'react')
        return { useRef: (value) => ({ current: value }), useCallback: (fn) => fn };
      if (id === 'recoil') return { useRecoilCallback: (fn) => fn({ set() {}, reset() {} }) };
      if (id === 'librechat-data-provider')
        return {
          Constants: { USE_PRELIM_RESPONSE_MESSAGE_ID: 'prelim', mcp_delimiter: '_mcp_' },
          StepTypes,
          StepEvents,
          ContentTypes,
          ToolCallTypes: { TOOL_CALL: 'tool_call' },
          getNonEmptyValue: (values) => values.find(Boolean),
        };
      if (id === '~/store') return { listRegisteredSubagentProgressKeys: () => [] };
      if (id === '~/utils/approval')
        return {
          isAskUserQuestionPart: () => false,
          isAnsweredAskUserQuestionPart: () => false,
        };
      if (id === '~/common') return { MESSAGE_UPDATE_INTERVAL: Infinity };
      throw new Error(`Unexpected hook dependency: ${id}`);
    },
  });
  vm.runInContext(hookSource, context, { filename: hookFile });
  vm.runInContext(
    `(function (exports) {
    ${activitySource}
    globalThis.lastCursorContentIdx = exports.lastCursorContentIdx;
    globalThis.applyActivityLabelPart = exports.applyActivityLabelPart;
    globalThis.findActivityLabelMessageIndex = exports.findActivityLabelMessageIndex;
    globalThis.offsetActivityPhaseBoundary = exports.offsetActivityPhaseBoundary;
  })({});`,
    context,
    { filename: activityFile },
  );
  vm.runInContext(helpersSource, context);
  let messages;
  let submission;
  function start(content, messageId = 'response') {
    const userMessage = {
      messageId: `user-${messageId}`,
      conversationId: 'conversation',
      isCreatedByUser: true,
    };
    const initialResponse = {
      messageId,
      parentMessageId: userMessage.messageId,
      isCreatedByUser: false,
      content,
    };
    messages = [userMessage, initialResponse];
    submission = { userMessage, initialResponse, messages: [], isRegenerate: false };
  }
  start(
    initialContent ??
      context.createDualMessageContent({ agent_id: primary }, { agent_id: 'agent_secondary' }),
  );
  const hook = context.exports.default({
    setMessages: (next) => {
      messages = next;
    },
    getMessages: () => messages,
    announcePolite() {},
    lastAnnouncementTimeRef: { current: Date.now() },
  });
  const send = (event, data) => hook.stepHandler({ event, data }, submission);
  Object.assign(context, {
    isCurrentSubscription: () => true,
    flushPendingDeltas: hook.flushPendingDeltas,
    syncStepMessage: hook.syncStepMessage,
    getMessages: () => messages,
    setMessages: (next) => {
      messages = next;
    },
    currentSubmission: submission,
    editPrefixClearedRef: { current: false },
    editPrefixFirstPartFoldedRef: { current: false },
    activityLabelRetryFramesRef: { current: new Set() },
    PENDING_ACTION_MAX_RETRY_FRAMES: 3,
  });
  vm.runInContext(activityHandlerSource, context, { filename: resumableFile });
  return {
    hook,
    send,
    start,
    activityLabel(index, part) {
      context.applyActivityLabelToMessages({
        responseMessageId: submission.initialResponse.messageId,
        index,
        part,
      });
    },
    get response() {
      return messages.find((message) => message.messageId === submission.initialResponse.messageId);
    },
    sections() {
      // Normalize VM objects for strict assertions, preserving original content indexes.
      return JSON.parse(
        JSON.stringify(context.groupParallelContent(this.response.content).parallelSections),
      );
    },
    cursorIndex() {
      return context.lastCursorContentIdx(this.response.content);
    },
    runStep(id, index, agentId, groupId = 1, stepDetails) {
      const details = stepDetails ?? {
        type: StepTypes.MESSAGE_CREATION,
        message_creation: { message_id: `message-${id}` },
      };
      send(StepEvents.ON_RUN_STEP, {
        id,
        type: details.type,
        runId: submission.initialResponse.messageId,
        index,
        agentId,
        ...(groupId != null && { groupId }),
        stepDetails: details,
      });
    },
    text(id, text, flush = true) {
      send(StepEvents.ON_MESSAGE_DELTA, { id, delta: { content: [{ type: 'text', text }] } });
      if (flush) hook.flushPendingDeltas();
    },
    replaceVisible(response) {
      messages = [submission.userMessage, response];
    },
    drainFrames() {
      for (const [id, callback] of [...frames]) {
        frames.delete(id);
        callback();
      }
    },
    get pendingFrames() {
      return frames.size;
    },
  };
}

function assertColumns(state, groupId = 1, agents = [primary, secondary]) {
  const section = state.sections().find((entry) => entry.groupId === groupId);
  assert.ok(section, `Missing parallel group ${groupId}`);
  assert.deepEqual(
    section.columns.map((column) => column.agentId),
    agents,
  );
  return section.columns;
}

for (const first of [secondary, primary]) {
  test(`${first} can stream first without losing the other column`, () => {
    const state = harness();
    const second = first === secondary ? primary : secondary;
    assertColumns(state);
    state.runStep('first', 0, first);
    assertColumns(state);
    for (const chunk of ['first', ' chunk', ' repeated']) {
      state.text('first', chunk);
      const columns = assertColumns(state);
      assert.equal(columns.find((column) => column.agentId === second).parts.length, 0);
      assert.equal(state.response.content[0].agentId, first);
      assert.ok(state.response.content.length <= 3, 'Repeated chunks must not append placeholders');
    }
    assert.equal(state.response.content[0].text, 'first chunk repeated');
    state.runStep('second', 1, second);
    state.text('second', 'other response');
    assertColumns(state);
    assert.equal(state.response.content[0].agentId, first);
    assert.equal(state.response.content[1].agentId, second);
    assert.equal(state.response.content[1].text, 'other response');
    assert.equal(
      state.response.content.filter((part) => part?.type === '').length,
      0,
      "Real content must replace that lane's pending placeholders without shifting indexes",
    );
    assert.equal(
      state.cursorIndex(),
      1,
      'A redundant empty tail must not consume the streaming cursor',
    );
  });
}

test('future server slots can displace a pending placeholder without moving real parts', () => {
  const state = harness();
  for (let index = 0; index < 4; index += 1) {
    state.runStep(`secondary-${index}`, index, secondary);
    state.text(`secondary-${index}`, `part ${index}`);
    state.text(`secondary-${index}`, ' done');
    const columns = assertColumns(state);
    assert.equal(columns[0].parts.length, 0);
    assert.deepEqual(
      columns[1].parts.map(({ idx }) => idx),
      Array.from({ length: index + 1 }, (_, i) => i),
    );
    for (let previous = 0; previous <= index; previous += 1) {
      assert.equal(state.response.content[previous].text, `part ${previous} done`);
    }
    assert.ok(state.response.content.length <= Math.max(3, index + 2));
  }
  state.runStep('primary', 4, primary);
  state.text('primary', 'finally ready');
  assertColumns(state);
  assert.equal(
    state.response.content.length,
    5,
    'A represented lane needs no appended placeholder',
  );
  assert.equal(state.response.content[4].text, 'finally ready');
});

test('placeholder identity includes the parallel group as well as the agent', () => {
  const third = 'agent_third____1';
  const state = harness([
    { type: '', agentId: primary, groupId: 1 },
    { type: '', agentId: secondary, groupId: 1 },
    { type: '', agentId: primary, groupId: 2 },
    { type: '', agentId: third, groupId: 2 },
  ]);
  for (const [id, index, agentId, groupId] of [
    ['first-group', 0, secondary, 1],
    ['second-group', 2, third, 2],
    ['later-slot', 4, third, 2],
  ]) {
    state.runStep(id, index, agentId, groupId);
    state.text(id, id);
    assertColumns(state, 1);
    assertColumns(state, 2, [primary, third]);
    assert.equal(state.response.content[index].text, id);
  }
  assert.equal(state.response.content[0].text, 'first-group');
  assert.equal(state.response.content[2].text, 'second-group');
});

test('reasoning deltas preserve the pending lane through the same real update path', () => {
  const state = harness();
  state.runStep('reasoning', 0, secondary);
  for (const think of ['considering', ' more']) {
    state.send(StepEvents.ON_REASONING_DELTA, {
      id: 'reasoning',
      delta: { content: [{ type: 'think', think }] },
    });
    state.hook.flushPendingDeltas();
    assertColumns(state);
  }
  assert.equal(state.response.content[0].think, 'considering more');
});

test('tool start, argument chunks, and completion retain the pending lane and server index', () => {
  const state = harness();
  state.runStep('tool', 0, secondary, 1, {
    type: StepTypes.TOOL_CALLS,
    tool_calls: [{ id: 'call-1', name: 'synthetic_tool', args: '' }],
  });
  assertColumns(state);
  state.send(StepEvents.ON_RUN_STEP_DELTA, {
    id: 'tool',
    delta: { type: StepTypes.TOOL_CALLS, tool_calls: [{ args: '{"query":"test"}' }] },
  });
  assertColumns(state);
  state.send(StepEvents.ON_RUN_STEP_COMPLETED, {
    result: { id: 'tool', tool_call: { id: 'call-1', name: 'synthetic_tool', output: 'done' } },
  });
  assertColumns(state);
  assert.equal(state.response.content[0].tool_call.args, '{"query":"test"}');
  assert.equal(state.response.content[0].tool_call.output, 'done');
  assert.equal(state.response.content[0].tool_call.progress, 1);
});

test('a delta buffered before its run step also retains both lanes', () => {
  const state = harness();
  state.text('early', 'buffered');
  assertColumns(state);
  state.runStep('early', 0, secondary);
  state.hook.flushPendingDeltas();
  assertColumns(state);
  assert.equal(state.response.content[0].text, 'buffered');
});

for (const first of [secondary, primary]) {
  test(`${first} can complete two labeled tool batches while the other lane is pending`, () => {
    const state = harness();
    const second = first === secondary ? primary : secondary;
    const expected = [];
    for (let batch = 0; batch < 2; batch += 1) {
      const index = batch * 2;
      const id = `tool-${batch}`;
      const callId = `call-${batch}`;
      state.runStep(id, index, first, 1, {
        type: StepTypes.TOOL_CALLS,
        tool_calls: [{ id: callId, name: 'synthetic_tool', args: '' }],
      });
      state.send(StepEvents.ON_RUN_STEP_COMPLETED, {
        result: { id, tool_call: { id: callId, name: 'synthetic_tool', output: `done ${batch}` } },
      });
      const pending = { type: ContentTypes.ACTIVITY_LABEL, activity_label: '', pending: true };
      state.activityLabel(index + 1, pending);
      assertColumns(state);
      const resolved = {
        type: ContentTypes.ACTIVITY_LABEL,
        activity_label: `Tool batch ${batch}`,
        pending: false,
      };
      state.activityLabel(index + 1, resolved);
      assertColumns(state);
      const settled = state.response;
      state.activityLabel(index + 1, resolved);
      state.activityLabel(index + 1, pending);
      assert.strictEqual(state.response, settled, 'Replays and stale reservations must be no-ops');
      expected.push(state.response.content[index], state.response.content[index + 1]);
      assert.equal(state.response.content[index].tool_call.output, `done ${batch}`);
      assert.equal(state.response.content[index + 1].activity_label, `Tool batch ${batch}`);
    }
    state.runStep('fast-text', 4, first);
    state.text('fast-text', 'still working', false);
    state.activityLabel(5, {
      type: ContentTypes.ACTIVITY_LABEL,
      activity_label: 'Working',
      pending: false,
    });
    const columns = assertColumns(state);
    assert.equal(columns.find((column) => column.agentId === second).parts.length, 0);
    assert.equal(state.response.content[4].text, 'still working');
    for (let index = 0; index < expected.length; index += 1) {
      assert.strictEqual(state.response.content[index], expected[index]);
    }
    state.text('fast-text', ' after label');
    assertColumns(state);
    assert.equal(state.response.content[4].text, 'still working after label');
    state.runStep('slow-text', 6, second);
    state.text('slow-text', 'finally ready');
    assertColumns(state);
    assert.equal(state.response.content[6].text, 'finally ready');
    assert.equal(state.response.content.filter((part) => part?.type === '').length, 0);
    assert.equal(state.cursorIndex(), 6);
  });
}

test('a label preserves displaced column identity across different parallel groups', () => {
  const state = harness([
    { type: '', agentId: primary, groupId: 1 },
    { type: 'text', text: 'other group', agentId: primary, groupId: 2 },
    { type: 'text', text: 'same group', agentId: secondary, groupId: 1 },
  ]);
  const otherGroup = state.response.content[1];
  const sameGroup = state.response.content[2];
  state.activityLabel(0, {
    type: ContentTypes.ACTIVITY_LABEL,
    activity_label: 'A phase',
    pending: false,
  });
  assertColumns(state);
  assertColumns(state, 2, [primary]);
  assert.strictEqual(state.response.content[1], otherGroup);
  assert.strictEqual(state.response.content[2], sameGroup);
  assert.equal(state.response.content.length, 4);
  assert.equal(state.response.content[3].agentId, primary);
  assert.equal(state.response.content[3].groupId, 1);
});

test('a label does not restore a displaced placeholder for an already represented column', () => {
  for (const type of ['', ContentTypes.TEXT]) {
    const state = harness([
      { type: '', agentId: primary, groupId: 1 },
      { type, text: 'represented', agentId: primary, groupId: 1 },
      { type: '', agentId: secondary, groupId: 1 },
    ]);
    state.activityLabel(0, {
      type: ContentTypes.ACTIVITY_LABEL,
      activity_label: '',
      pending: true,
    });
    assertColumns(state);
    assert.equal(state.response.content.length, 3);
    assert.equal(state.response.content[1].agentId, primary);
    assert.equal(state.response.content[1].type, type);
  }
});

test('a represented primary lane is not appended again when its old placeholder is displaced', () => {
  const state = harness();
  state.runStep('secondary', 0, secondary);
  state.text('secondary', 'first');
  state.runStep('primary', 1, primary);
  state.text('primary', 'second');
  state.runStep('third-slot', 2, secondary);
  state.text('third-slot', 'third');
  assertColumns(state);
  assert.equal(state.response.content.length, 3);
  assert.equal(state.response.content.filter((part) => part?.type === '').length, 0);
  assert.equal(state.response.content[1].text, 'second');
});

test('clearStepMaps cancels queued work and a new submission inherits no old lanes', () => {
  const state = harness();
  state.runStep('reused-step', 0, secondary);
  state.text('reused-step', 'old queued text', false);
  assert.equal(state.pendingFrames, 1);
  state.hook.clearStepMaps();
  assert.equal(state.pendingFrames, 0);
  state.start([], 'new-response');
  state.runStep('reused-step', 0, undefined, null);
  state.text('reused-step', 'new single response');
  state.drainFrames();
  assert.equal(state.response.content.length, 1);
  assert.equal(state.response.content[0].text, 'new single response');
  assert.deepEqual(state.sections(), []);
});

test('syncStepMessage replaces old placeholders with the authoritative snapshot', () => {
  const state = harness();
  state.runStep('secondary', 0, secondary);
  state.text('secondary', 'streaming');
  assertColumns(state);
  const snapshot = {
    ...state.response,
    content: [{ type: 'text', text: 'server snapshot', agentId: secondary, groupId: 1 }],
  };
  state.replaceVisible(snapshot);
  state.hook.syncStepMessage(snapshot);
  state.text('secondary', ' continued');
  assert.equal(state.response.content.length, 1);
  assert.equal(state.response.content[0].text, 'server snapshot continued');
  assertColumns(state, 1, [secondary]);
});

test('the terminal flush-cancellation boundary cannot overwrite a full server snapshot', () => {
  const state = harness();
  state.runStep('secondary', 0, secondary);
  state.text('secondary', 'queued streaming text', false);
  assert.equal(state.pendingFrames, 1);
  state.hook.cancelPendingDeltaFlush();
  const snapshot = {
    ...state.response,
    content: [{ type: 'text', text: 'final server text', agentId: secondary, groupId: 1 }],
  };
  // The external final handler owns this cache replacement. Exercise its hook
  // boundary here without claiming to execute that handler or the server.
  state.replaceVisible(snapshot);
  state.hook.clearStepMaps();
  state.drainFrames();
  assert.equal(state.pendingFrames, 0);
  assert.strictEqual(state.response, snapshot);
  assertColumns(state, 1, [secondary]);
});

test('flushing then clearing stream state retains visible partial content and pending lanes', () => {
  const state = harness();
  state.runStep('secondary', 0, secondary);
  state.text('secondary', 'partial response', false);
  state.hook.flushPendingDeltas();
  state.hook.clearStepMaps();
  state.drainFrames();
  assert.equal(state.response.content[0].text, 'partial response');
  assertColumns(state);
  // Clearing maps is not placeholder cleanup. The existing local abort path
  // filters null entries, so an empty-type pending lane can remain after abort.
  assert.ok(state.response.content.some((part) => part?.type === '' && part.agentId === primary));
});
