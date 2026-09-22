import {
  collectToolSchemaNames,
  createToolSchemaDiagnosticCallback,
  isToolSchemaDiagnosticsEnabled,
} from './toolSchemaDiagnostics';

describe('toolSchemaDiagnostics', () => {
  describe('isToolSchemaDiagnosticsEnabled', () => {
    it.each(['1', 'true', 'TRUE', ' yes ', 'on'])('accepts enabled value %p', (value) => {
      expect(isToolSchemaDiagnosticsEnabled(value)).toBe(true);
    });

    it.each([undefined, '', '0', 'false', 'off', 'no'])('rejects disabled value %p', (value) => {
      expect(isToolSchemaDiagnosticsEnabled(value)).toBe(false);
    });
  });

  it('collects Google function declaration names', () => {
    expect(
      collectToolSchemaNames({
        tools: [
          {
            functionDeclarations: [
              { name: 'list_repositories', parameters: { type: 'object' } },
              { name: 'create_task', parameters: { type: 'object' } },
            ],
          },
        ],
      }),
    ).toEqual(['create_task', 'list_repositories']);
  });

  it('collects OpenAI/LangChain and direct tool definition names', () => {
    expect(
      collectToolSchemaNames({
        toolDefinitions: [{ name: 'read_file' }],
        tools: [{ type: 'function', function: { name: 'git_diff' } }],
        toolRegistry: [{ name: 'task_status' }],
      }),
    ).toEqual(['git_diff', 'read_file', 'task_status']);
  });

  it('ignores unrelated name fields outside tool-shaped containers', () => {
    expect(
      collectToolSchemaNames({
        name: 'not-a-tool',
        metadata: { name: 'also-not-a-tool' },
        tools: [{ name: 'real_tool' }],
      }),
    ).toEqual(['real_tool']);
  });

  it('is cycle-safe and captures allowed function names', () => {
    const cycle: Record<string, unknown> = {
      toolConfig: {
        functionCallingConfig: {
          allowedFunctionNames: ['alpha', 'beta'],
        },
      },
    };
    cycle.self = cycle;
    expect(collectToolSchemaNames(cycle)).toEqual(['alpha', 'beta']);
  });

  it('logs only bounded tool-name metadata from model start callbacks', () => {
    const logs: string[] = [];
    const callback = createToolSchemaDiagnosticCallback({
      agentId: 'agent-test',
      provider: 'google',
      model: 'gemini-test',
      conversationId: 'conversation-test',
      log: (message) => logs.push(message),
    });

    callback.handleChatModelStart?.(
      {
        kwargs: {
          tools: [{ functionDeclarations: [{ name: 'serialized_tool', description: 'secret-ish' }] }],
        },
      },
      [[]],
      'run-1',
      'parent-1',
      {
        options: {
          tools: [{ functionDeclarations: [{ name: 'bound_tool', description: 'do not log me' }] }],
        },
        apiKey: 'must-not-be-logged',
      },
    );

    expect(logs).toHaveLength(1);
    expect(logs[0]).toContain('"invocationToolNames":["bound_tool"]');
    expect(logs[0]).toContain('"serializedModelToolNames":["serialized_tool"]');
    expect(logs[0]).toContain('"extraParamKeys":["apiKey","options"]');
    expect(logs[0]).not.toContain('must-not-be-logged');
    expect(logs[0]).not.toContain('do not log me');
    expect(logs[0]).not.toContain('secret-ish');
  });
});
