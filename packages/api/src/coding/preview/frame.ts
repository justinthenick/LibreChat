import { TextDecoder } from 'node:util';
import type { PreviewPrincipal } from './types';

const unavailable = () => new Error('job_service_unavailable');

/** JSON.parse alone silently accepts duplicate keys; the already-valid token stream must not. */
function decode(bytes: Buffer): Record<string, unknown> {
  const source = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  const value: unknown = JSON.parse(source);
  const objects: Set<string>[] = [];
  for (const token of source.matchAll(/"(?:\\.|[^"\\])*"|[{}]/g)) {
    if (token[0] === '{') objects.push(new Set());
    else if (token[0] === '}') objects.pop();
    else if (/^\s*:/.test(source.slice(token.index + token[0].length))) {
      const key = JSON.parse(token[0]) as string;
      const current = objects[objects.length - 1];
      if (!current || current.has(key) || ['__proto__', 'constructor', 'prototype'].includes(key)) {
        throw unavailable();
      }
      current.add(key);
    }
  }
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw unavailable();
  return value as Record<string, unknown>;
}

/** Shared finite response validation for private pipes and HTTPS. */
export function decodePreviewReply(
  bytes: Buffer,
  id: string,
  principal: PreviewPrincipal,
): unknown {
  if (bytes.length > 270336 || bytes.indexOf(10) !== bytes.length - 1) throw unavailable();
  const frame = decode(bytes.subarray(0, -1));
  if (
    Object.keys(frame).sort().join(',') !== 'principal,request_id,result,version' ||
    frame.version !== 1 ||
    frame.request_id !== id ||
    JSON.stringify(frame.principal) !== JSON.stringify(principal)
  )
    throw unavailable();
  return frame.result;
}
