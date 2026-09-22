import type { CallbackHandlerMethods } from '@langchain/core/callbacks/base';

const TRUE_VALUES = new Set(['1', 'true', 'yes', 'on']);
const MAX_TOOL_SCHEMA_DIAGNOSTIC_DEPTH = 12;
const MAX_TOOL_SCHEMA_DIAGNOSTIC_NODES = 5000;
const TOOL_CONTAINER_KEYS = new Set([
  'tools',
  'toolDefinitions',
  'graphTools',
  'toolRegistry',
  'functions',
  'functionDeclarations',
  'function_declarations',
  'function',
]);
const TOOL_NAME_ARRAY_KEYS = new Set(['allowedFunctionNames', 'allowed_function_names']);

export const TOOL_SCHEMA_DIAGNOSTIC_PREFIX = '[AgentToolSchemaDiagnostic]';

export function isToolSchemaDiagnosticsEnabled(
  value: string | undefined = process.env.AGENT_TOOL_SCHEMA_DIAGNOSTICS,
): boolean {
  return value != null && TRUE_VALUES.has(value.trim().toLowerCase());
}

function isObject(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object';
}

/**
 * Extracts only tool/function names from provider-bound schema-like objects.
 * The traversal is intentionally bounded and cycle-safe because callback
 * payloads can contain class instances and self-references.
 */
export function collectToolSchemaNames(value: unknown): string[] {
  const names = new Set<string>();
  const seen = new WeakSet<object>();
  let visited = 0;

  const visit = (candidate: unknown, inToolContext: boolean, depth: number): void => {
    if (
      candidate == null ||
      depth > MAX_TOOL_SCHEMA_DIAGNOSTIC_DEPTH ||
      visited >= MAX_TOOL_SCHEMA_DIAGNOSTIC_NODES
    ) {
      return;
    }

    if (Array.isArray(candidate)) {
      visited++;
      for (const item of candidate) {
        visit(item, inToolContext, depth + 1);
        if (visited >= MAX_TOOL_SCHEMA_DIAGNOSTIC_NODES) {
          break;
        }
      }
      return;
    }

    if (!isObject(candidate)) {
      return;
    }

    if (seen.has(candidate)) {
      return;
    }
    seen.add(candidate);
    visited++;

    if (inToolContext && typeof candidate.name === 'string' && candidate.name.trim() !== '') {
      names.add(candidate.name.trim());
    }

    for (const [key, child] of Object.entries(candidate)) {
      if (
        TOOL_NAME_ARRAY_KEYS.has(key) &&
        Array.isArray(child) &&
        child.every((entry) => typeof entry === 'string')
      ) {
        for (const entry of child) {
          const name = entry.trim();
          if (name !== '') {
            names.add(name);
          }
        }
        continue;
      }

      const childToolContext = inToolContext || TOOL_CONTAINER_KEYS.has(key);
      visit(child, childToolContext, depth + 1);
      if (visited >= MAX_TOOL_SCHEMA_DIAGNOSTIC_NODES) {
        break;
      }
    }
  };

  visit(value, false, 0);
  return [...names].sort();
}

export function createToolSchemaDiagnosticCallback(input: {
  agentId: string;
  provider: string;
  model?: string;
  conversationId?: string;
  log: (message: string) => void;
}): CallbackHandlerMethods {
  return {
    handleChatModelStart: (
      llm,
      _messageBatches,
      modelRunId,
      parentRunId,
      extraParams,
    ): void => {
      const extraParamKeys =
        extraParams != null && typeof extraParams === 'object'
          ? Object.keys(extraParams as Record<string, unknown>).sort()
          : [];
      const event = {
        phase: 'provider-bound',
        conversationId: input.conversationId,
        agentId: input.agentId,
        provider: input.provider,
        model: input.model,
        modelRunId,
        parentRunId,
        invocationToolNames: collectToolSchemaNames(extraParams),
        serializedModelToolNames: collectToolSchemaNames(llm),
        extraParamKeys,
      };
      input.log(`${TOOL_SCHEMA_DIAGNOSTIC_PREFIX} ${JSON.stringify(event)}`);
    },
  };
}
