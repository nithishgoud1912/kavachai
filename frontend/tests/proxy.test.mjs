import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
import vm from 'node:vm';

function proxy(fetch) {
  const source = fs.readFileSync('app/api/v1/proxy.ts', 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
  const context = { exports: {}, process: { env: {} }, Request, Response, Headers, URL, Uint8Array, AbortController, setTimeout, clearTimeout, fetch };
  vm.runInNewContext(compiled, context);
  return context.exports.proxyToBackend;
}

test('forwards query and cookie authentication without masking errors', async () => {
  const forward = proxy(async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/api/v1/models?type=rules');
    assert.equal(options.headers.get('authorization'), 'Bearer test-token');
    return Response.json({ detail: 'denied' }, { status: 403 });
  });
  const result = await forward(new Request('http://localhost/api/v1/models?type=rules', { headers: { cookie: 'kavach_session=test-token' } }));
  assert.equal(result.status, 403);
  assert.deepEqual(await result.json(), { detail: 'denied' });
});

test('offline backend produces 503, never simulated success', async () => {
  const result = await proxy(async () => { throw Error('offline'); })(new Request('http://localhost/api/v1/tasks'));
  assert.equal(result.status, 503);
});

test('rejects cross-origin writes and malformed cookies before forwarding', async () => {
  const forward = proxy(async () => { assert.fail('must not forward'); });
  assert.equal((await forward(new Request('http://localhost/api/v1/tasks', { method: 'POST', headers: { origin: 'http://other' } }))).status, 403);
  assert.equal((await forward(new Request('http://localhost/api/v1/tasks', { headers: { cookie: 'kavach_session=%broken' } }))).status, 400);
});

test('enforces streamed body limit before calling the backend', async () => {
  const forward = proxy(async () => { assert.fail('must not forward'); });
  const result = await forward(new Request('http://localhost/api/v1/tasks', { method: 'POST', body: new Uint8Array(24 * 1024 * 1024 + 1) }));
  assert.equal(result.status, 413);
});

test('sets HttpOnly session only after MFA is complete', async () => {
  for (const mfa_required of [true, false]) {
    const forward = proxy(async () => Response.json({ session_id: 'token', mfa_required }));
    const result = await forward(new Request('https://localhost/api/v1/auth/login', { method: 'POST', body: '{}' }));
    const cookie = result.headers.get('set-cookie');
    if (mfa_required) assert.equal(cookie, null);
    else assert.match(cookie, /HttpOnly; SameSite=Strict; Path=\/; Secure;/);
  }
});
