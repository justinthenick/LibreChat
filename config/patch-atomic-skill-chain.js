const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SKILLS_PATH = path.join(ROOT, 'packages/api/src/agents/skills.ts');
const HANDLERS_PATH = path.join(ROOT, 'packages/api/src/agents/handlers.ts');
const HANDLERS_SPEC_PATH = path.join(ROOT, 'packages/api/src/agents/handlers.spec.ts');

const PATCH_MARKER = 'BA_ATOMIC_MULTI_SKILL_V1';

function replaceOnce(source, needle, replacement, label) {
  const first = source.indexOf(needle);
  if (first === -1) {
    throw new Error(`${label}: expected source anchor was not found`);
  }
  if (source.indexOf(needle, first + needle.length) !== -1) {
    throw new Error(`${label}: source anchor is ambiguous`);
  }
  return source.slice(0, first) + replacement + source.slice(first + needle.length);
}

function replaceBetween(source, startMarker, endMarker, replacement, label) {
  const start = source.indexOf(startMarker);
  if (start === -1) {
    throw new Error(`${label}: start marker not found`);
  }
  const end = source.indexOf(endMarker, start);
  if (end === -1) {
    throw new Error(`${label}: end marker not found`);
  }
  return source.slice(0, start) + replacement + source.slice(end);
}

function patchSkillsSource(source) {
  if (source.includes(PATCH_MARKER)) {
    return source;
  }

  const original = `  const skillToolDef: LCTool = {\n    name: SkillToolDefinition.name,\n    description: SkillToolDefinition.description,\n    parameters: SkillToolDefinition.parameters as unknown as LCTool['parameters'],\n  };`;

  const replacement = `  // ${PATCH_MARKER}: preserve legacy skillName while allowing one ordered,\n  // bounded multi-skill invocation. The handler resolves the whole list\n  // atomically before injecting any skill content.\n  const skillToolDef: LCTool = {\n    name: SkillToolDefinition.name,\n    description:\n      SkillToolDefinition.description +\n      ' For a dependency-ordered workflow, load the complete chain in one call with skillNames (maximum 10). Use skillName for a single skill.',\n    parameters: {\n      type: 'object',\n      properties: {\n        skillName: { type: 'string', description: 'Single skill to load.' },\n        skillNames: {\n          type: 'array',\n          minItems: 1,\n          maxItems: 10,\n          items: { type: 'string' },\n          description: 'Dependency-ordered skill chain to load atomically.',\n        },\n        args: {\n          type: 'string',\n          description: 'Optional text substituted for $ARGUMENTS in every loaded skill.',\n        },\n      },\n      oneOf: [\n        { required: ['skillName'], not: { required: ['skillNames'] } },\n        { required: ['skillNames'], not: { required: ['skillName'] } },\n      ],\n      additionalProperties: false,\n    } as unknown as LCTool['parameters'],\n  };`;

  return replaceOnce(source, original, replacement, 'skills.ts');
}

function patchHandlersSource(source) {
  if (source.includes(PATCH_MARKER)) {
    return source;
  }

  const startMarker = 'async function handleSkillToolCall(';
  const endMarker = '\nfunction getFileAuthoringQueueKey(';

  const replacement = `async function handleSkillToolCall(\n  tc: ToolCallRequest,\n  mergedConfigurable: Record<string, unknown>,\n  options: ToolExecuteOptions,\n  agentId?: string,\n  req?: ServerRequest,\n): Promise<ToolExecuteResult> {\n  // ${PATCH_MARKER}: one model decision can load a complete dependency-ordered\n  // skill chain. Single-skill calls retain their previous contract.\n  const {\n    getSkillByName,\n    listSkillFiles,\n    getStrategyFunctions,\n    batchUploadCodeEnvFiles,\n    getSessionInfo,\n    checkIfActive,\n    updateSkillFileCodeEnvIds,\n  } = options;\n  const args = tc.args as { skillName?: string; skillNames?: string[]; args?: string };\n\n  if (args.skillName && args.skillNames) {\n    return errorResult(tc, 'Provide either skillName or skillNames, not both');\n  }\n\n  const rawNames = Array.isArray(args.skillNames)\n    ? args.skillNames\n    : typeof args.skillName === 'string'\n      ? [args.skillName]\n      : [];\n  if (rawNames.length === 0) {\n    return errorResult(tc, 'skillName or skillNames is required');\n  }\n  if (rawNames.length > 10) {\n    return errorResult(tc, 'skillNames supports at most 10 skills per call');\n  }\n\n  const requestedNames: string[] = [];\n  const seenNames = new Set<string>();\n  for (const rawName of rawNames) {\n    if (typeof rawName !== 'string' || !rawName.trim()) {\n      return errorResult(tc, 'Every requested skill name must be a non-empty string');\n    }\n    const name = rawName.trim();\n    if (seenNames.has(name)) {\n      continue;\n    }\n    seenNames.add(name);\n    requestedNames.push(name);\n  }\n\n  if (!getSkillByName) {\n    return errorResult(tc, 'Skill execution is not configured');\n  }\n\n  const accessibleIds = (mergedConfigurable?.accessibleSkillIds as Types.ObjectId[]) ?? [];\n  type ResolvedSkill = NonNullable<\n    Awaited<ReturnType<NonNullable<ToolExecuteOptions['getSkillByName']>>>\n  >;\n  const skills: ResolvedSkill[] = [];\n\n  // Resolve and validate the complete chain first. This makes invocation atomic:\n  // an unavailable or model-disabled skill prevents any SKILL.md from being\n  // injected, so the model cannot run a partially loaded workflow.\n  for (const name of requestedNames) {\n    const skill = await getSkillByName(name, accessibleIds, {\n      preferModelInvocable: true,\n    });\n    if (!skill) {\n      return errorResult(tc, \`Skill "\${name}" not found or not accessible\`);\n    }\n    if (skill.disableModelInvocation === true) {\n      return errorResult(tc, \`Skill "\${name}" cannot be invoked by the model\`);\n    }\n    skills.push(skill);\n  }\n\n  const prepared: Array<{ skill: ResolvedSkill; body: string }> = [];\n  for (const skill of skills) {\n    let body = skill.body;\n    if (args.args) {\n      body = body.replace(/\\$ARGUMENTS/g, args.args);\n    }\n    const filtered = filteredSkillResult(tc, req, {\n      name: skill.name,\n      description: skill.description,\n      body,\n      frontmatter: skill.frontmatter,\n    });\n    if (filtered != null) {\n      return filtered;\n    }\n    prepared.push({ skill, body });\n  }\n\n  const injectedMessages: InjectedMessage[] = prepared.map(({ skill, body }) =>\n    buildSkillPrimeMessage({ name: skill.name, body }),\n  );\n\n  let contentText =\n    prepared.length === 1\n      ? \`Skill "\${prepared[0].skill.name}" loaded. Follow the instructions below.\`\n      : \`Skills \${prepared.map(({ skill }) => \`"\${skill.name}"\`).join(' → ')} loaded in dependency order. Follow all injected skill instructions cumulatively and produce one consolidated answer.\`;\n\n  const codeEnvAvailable = mergedConfigurable?.codeEnvAvailable === true;\n  const codeExecutionContext = getCodeExecutionContext(mergedConfigurable);\n  let artifactSessionId: string | undefined;\n  const artifactFiles: Array<{\n    id: string;\n    resource_id: string;\n    name: string;\n    storage_session_id: string;\n    kind?: 'skill' | 'agent' | 'user';\n    version?: number;\n  }> = [];\n\n  for (const { skill } of prepared) {\n    if (\n      codeEnvAvailable &&\n      skill.fileCount > 0 &&\n      req &&\n      listSkillFiles &&\n      getStrategyFunctions &&\n      batchUploadCodeEnvFiles\n    ) {\n      let primeResult: PrimeSkillFilesResult | null = null;\n      try {\n        const skillFiles = await listSkillFiles(skill._id);\n        primeResult = await primeSkillFiles({\n          skill,\n          skillFiles,\n          req,\n          getStrategyFunctions,\n          batchUploadCodeEnvFiles,\n          getSessionInfo,\n          checkIfActive,\n          updateSkillFileCodeEnvIds,\n          codeExecutionContext,\n        });\n        if (primeResult) {\n          artifactSessionId ??= primeResult.storage_session_id;\n          artifactFiles.push(\n            ...primeResult.files.map((f) => ({\n              id: f.id,\n              resource_id: f.resource_id,\n              name: f.name,\n              storage_session_id: f.storage_session_id,\n              kind: 'skill' as const,\n              version: skill.version,\n            })),\n          );\n        }\n      } catch (error) {\n        if (isContentFilterError(error)) {\n          return error instanceof ContentFilterError\n            ? errorResult(tc, modelBoundContentFilterErrorMessage(error.body))\n            : errorResult(tc, error.body.message);\n        }\n        logger.error(\n          \`[handleSkillToolCall] Failed to prime files for skill "\${skill.name}":\`,\n          error instanceof Error ? error.message : error,\n        );\n      }\n      if (!primeResult) {\n        contentText +=\n          \`\\n\\nNote: skill "\${skill.name}" bundled files could not be loaded into the code environment \` +\n          \`(upload failed or was rate-limited). Paths under /mnt/data/\${SKILL_FILE_PREFIX}\${skill.name}/ \` +\n          'are NOT available to bash or code execution this turn. Use the read_file tool to view bundled files instead.';\n      }\n    }\n  }\n\n  for (const { skill } of prepared) {\n    options.onSkillResolved?.(\n      {\n        id: skill._id.toString(),\n        name: skill.name,\n        version: skill.version,\n        contentDigest: createSkillContentDigest(skill.body),\n      },\n      { agentId },\n    );\n  }\n\n  const artifact =\n    artifactSessionId && artifactFiles.length > 0\n      ? { session_id: artifactSessionId, files: artifactFiles }\n      : undefined;\n\n  return {\n    toolCallId: tc.id,\n    content: contentText,\n    status: 'success',\n    artifact,\n    injectedMessages,\n  };\n}\n`;

  return replaceBetween(source, startMarker, endMarker, replacement, 'handlers.ts');
}

const TEST_MARKER = 'BA_ATOMIC_MULTI_SKILL_TEST_V1';
function patchHandlerTests(source) {
  if (source.includes(TEST_MARKER)) {
    return source;
  }
  const tests = `\n\n// ${TEST_MARKER}\ndescribe('atomic multi-skill model invocation', () => {\n  const { Types } = jest.requireActual('mongoose') as typeof import('mongoose');\n\n  function makeHandler(names: string[]) {\n    const docs = new Map(\n      names.map((name) => [\n        name,\n        {\n          _id: new Types.ObjectId(),\n          name,\n          body: \`# \${name}\\nFollow \${name}\`,\n          version: 1,\n          fileCount: 0,\n        },\n      ]),\n    );\n    const getSkillByName: ToolExecuteOptions['getSkillByName'] = jest.fn(async (name) =>\n      (docs.get(name) ?? null) as never,\n    );\n    const loadTools: ToolExecuteOptions['loadTools'] = jest.fn(async () => ({ loadedTools: [] }));\n    return { handler: createToolExecuteHandler({ loadTools, getSkillByName }), getSkillByName };\n  }\n\n  it('loads an ordered dependency chain atomically in one skill call', async () => {\n    const { handler, getSkillByName } = makeHandler(['analyze', 'decompose', 'acceptance']);\n    const [result] = await invokeHandlerWithConfig(\n      handler,\n      [\n        {\n          id: 'call_chain',\n          name: 'skill',\n          args: { skillNames: ['analyze', 'decompose', 'acceptance'] },\n        },\n      ],\n      { accessibleSkillIds: skillsInScope() },\n    );\n\n    expect(result.status).toBe('success');\n    expect(result.content).toContain('"analyze" → "decompose" → "acceptance"');\n    expect(getSkillByName).toHaveBeenCalledTimes(3);\n    const injected = (result as unknown as { injectedMessages?: Array<{ skillName?: string }> })\n      .injectedMessages;\n    expect(injected?.map((message) => message.skillName)).toEqual([\n      'analyze',\n      'decompose',\n      'acceptance',\n    ]);\n  });\n\n  it('retains the legacy single-skill contract', async () => {\n    const { handler } = makeHandler(['analyze']);\n    const [result] = await invokeHandlerWithConfig(\n      handler,\n      [{ id: 'call_single', name: 'skill', args: { skillName: 'analyze' } }],\n      { accessibleSkillIds: skillsInScope() },\n    );\n    expect(result.status).toBe('success');\n    expect(result.content).toBe('Skill "analyze" loaded. Follow the instructions below.');\n  });\n\n  it('fails the whole chain before injection when any requested skill is unavailable', async () => {\n    const { handler } = makeHandler(['analyze', 'acceptance']);\n    const [result] = await invokeHandlerWithConfig(\n      handler,\n      [\n        {\n          id: 'call_missing',\n          name: 'skill',\n          args: { skillNames: ['analyze', 'missing', 'acceptance'] },\n        },\n      ],\n      { accessibleSkillIds: skillsInScope() },\n    );\n    expect(result.status).toBe('error');\n    expect(result.errorMessage).toContain('missing');\n    expect((result as unknown as { injectedMessages?: unknown }).injectedMessages).toBeUndefined();\n  });\n});\n`;
  return source + tests;
}

function patchFile(filePath, transform) {
  const original = fs.readFileSync(filePath, 'utf8');
  const patched = transform(original);
  if (patched === original) {
    console.log(`unchanged ${path.relative(ROOT, filePath)}`);
    return;
  }
  fs.writeFileSync(filePath, patched);
  console.log(`patched ${path.relative(ROOT, filePath)}`);
}

function main() {
  patchFile(SKILLS_PATH, patchSkillsSource);
  patchFile(HANDLERS_PATH, patchHandlersSource);
  if (process.argv.includes('--tests')) {
    patchFile(HANDLERS_SPEC_PATH, patchHandlerTests);
  }
}

if (require.main === module) {
  main();
}

module.exports = { patchSkillsSource, patchHandlersSource, patchHandlerTests, PATCH_MARKER };
