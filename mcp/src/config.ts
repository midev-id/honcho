import { Honcho } from "@honcho-ai/sdk";

export interface HonchoConfig {
  apiKey: string;
  baseUrl: string;
  /** From X-Honcho-Workspace-ID when set. */
  workspaceId?: string;
}

export interface Env {
  HONCHO_API_URL?: string;
  ALERT_WEBHOOK_URL?: string;
  /**
   * Shared secret every MCP client must present as its bearer token.
   *
   * Set this whenever the upstream Honcho has `AUTH_USE_AUTH=false` (e.g. a
   * self-hosted instance left open on a private network): this Worker is then
   * the ONLY thing standing between the public internet and an unauthenticated
   * Honcho, and without it any non-empty bearer would be accepted.
   *
   * When unset, the bearer is forwarded to Honcho unverified and Honcho's own
   * auth is what rejects bad tokens -- the original behaviour, kept so hosted
   * deployments that rely on per-user Honcho keys are unaffected.
   */
  MCP_SHARED_SECRET?: string;
}

/**
 * Constant-time string equality. A plain `===` leaks how many leading
 * characters matched via its early exit, which is enough to recover a secret
 * one character at a time.
 */
function secretsMatch(a: string, b: string): boolean {
  const ab = new TextEncoder().encode(a);
  const bb = new TextEncoder().encode(b);
  // Length is not secret (it is visible in the request), but the comparison
  // below needs equal lengths to be meaningful, so reject early.
  if (ab.length !== bb.length) return false;
  let diff = 0;
  for (let i = 0; i < ab.length; i++) diff |= ab[i] ^ bb[i];
  return diff === 0;
}

/**
 * Parse configuration from request headers and Worker env bindings.
 * Throws only when the Authorization bearer token is missing/empty.
 *
 * The Honcho API URL is read from the `HONCHO_API_URL` env var when set,
 * allowing operators to run this Worker alongside a self-hosted Honcho
 * instance (see the "Self-Hosted Honcho" section in README.md). It is
 * intentionally not exposed as a request header: routing public requests
 * to an internal URL would be a latency and security regression.
 *
 * Optional `X-Honcho-Workspace-ID` becomes the default `workspace_id` on
 * tools. If the header is omitted, each tool call must pass `workspace_id`.
 */
export function parseConfig(request: Request, env: Env = {}): HonchoConfig {
  const authHeader = request.headers.get("Authorization");
  const bearerMatch = authHeader?.trim().match(/^Bearer\s+(.*)$/i);
  if (!bearerMatch) {
    throw new Error(
      "Missing Authorization header. Provide 'Authorization: Bearer <your-honcho-key>'.",
    );
  }
  const apiKey = bearerMatch[1].trim();
  if (!apiKey) {
    throw new Error("Authorization header is empty after 'Bearer '.");
  }

  // When a shared secret is configured this Worker is the trust boundary, so
  // the bearer is checked here rather than being handed to Honcho to judge.
  const expected = env.MCP_SHARED_SECRET?.trim();
  if (expected && !secretsMatch(apiKey, expected)) {
    throw new Error("Invalid bearer token.");
  }

  const workspaceId =
    request.headers.get("X-Honcho-Workspace-ID")?.trim() || undefined;

  return {
    apiKey,
    baseUrl: env.HONCHO_API_URL?.trim() || "https://api.honcho.dev",
    workspaceId,
  };
}

export const MISSING_WORKSPACE_ID_MESSAGE =
  "Missing workspace_id. Pass workspace_id on the next tool call, or set the X-Honcho-Workspace-ID header on the connection so it is used automatically.";

export function resolveWorkspaceId(
  config: HonchoConfig,
  workspaceId?: string,
): string {
  const id = workspaceId?.trim() || config.workspaceId?.trim();
  if (!id) {
    throw new Error(MISSING_WORKSPACE_ID_MESSAGE);
  }
  return id;
}

export function createClient(
  config: HonchoConfig,
  workspaceId: string,
): Honcho {
  return new Honcho({
    apiKey: config.apiKey,
    baseURL: config.baseUrl,
    workspaceId,
  });
}

/** Client used only for credential-scoped ops (list workspaces). */
export function createUnscopedClient(config: HonchoConfig): Honcho {
  return new Honcho({
    apiKey: config.apiKey,
    baseURL: config.baseUrl,
  });
}

export function createClientFactory(
  config: HonchoConfig,
): (workspaceId?: string) => Honcho {
  const cache = new Map<string, Honcho>();
  return (workspaceId?: string) => {
    const id = resolveWorkspaceId(config, workspaceId);
    let client = cache.get(id);
    if (!client) {
      client = createClient(config, id);
      cache.set(id, client);
    }
    return client;
  };
}
