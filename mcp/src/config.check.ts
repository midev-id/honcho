/**
 * Self-check for the MCP_SHARED_SECRET trust boundary in parseConfig().
 *
 * Run: bun run src/config.check.ts
 *
 * Deliberately a plain assert script, not a test-framework suite: this package
 * has no test runner, and the repo's `bun test` is reserved for the SDK tests
 * that need a live server (see CLAUDE.md). This one needs nothing.
 */
import { parseConfig, type Env } from "./config.js";

// ponytail: local asserts instead of node:assert -- this package's tsconfig is
// Workers-only and has no Node types, and one @types/node dependency is not
// worth three lines of code.
const assert = {
  equal(actual: unknown, expected: unknown) {
    if (actual !== expected) {
      throw new Error(`expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
  },
  throws(fn: () => unknown, pattern: RegExp) {
    let message: string | undefined;
    try {
      fn();
    } catch (e) {
      message = e instanceof Error ? e.message : String(e);
    }
    if (message === undefined) throw new Error(`expected a throw matching ${pattern}`);
    if (!pattern.test(message)) {
      throw new Error(`expected throw matching ${pattern}, got "${message}"`);
    }
  },
};

const SECRET = "s3cret-token-value";
const req = (bearer?: string) =>
  new Request("https://example.invalid/", {
    headers: bearer ? { Authorization: `Bearer ${bearer}` } : {},
  });

// With a secret configured, only the exact token gets through.
const guarded: Env = { MCP_SHARED_SECRET: SECRET };
assert.equal(parseConfig(req(SECRET), guarded).apiKey, SECRET);
assert.throws(() => parseConfig(req("wrong"), guarded), /Invalid bearer token/);
// A prefix must fail: the constant-time compare rejects on length first, and a
// `===` early exit would leak the match length.
assert.throws(() => parseConfig(req(SECRET.slice(0, -1)), guarded), /Invalid bearer token/);
assert.throws(() => parseConfig(req(SECRET + "x"), guarded), /Invalid bearer token/);
assert.throws(() => parseConfig(req(), guarded), /Missing Authorization header/);

// Whitespace around the bearer is trimmed before comparison, so a token pasted
// with a trailing newline still authenticates.
assert.equal(parseConfig(req(`  ${SECRET}  `), guarded).apiKey, SECRET);

// Without a secret configured the Worker stays a pass-through and Honcho's own
// auth is what judges the token -- the pre-existing behaviour.
const open: Env = {};
assert.equal(parseConfig(req("any-honcho-key"), open).apiKey, "any-honcho-key");
assert.throws(() => parseConfig(req(), open), /Missing Authorization header/);

// An empty or whitespace-only secret must not silently disable the check by
// being treated as "configured but matching nothing" -- it means "not set".
const blank: Env = { MCP_SHARED_SECRET: "   " };
assert.equal(parseConfig(req("anything"), blank).apiKey, "anything");

console.log("config.check.ts: all assertions passed");
