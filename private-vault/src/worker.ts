export interface Env {
  VAULT: R2Bucket;
}

// Map a request URL pathname to an R2 object key.
// `/` resolves to `index.html`. Any path containing `..` or other
// traversal-style segments is rejected up front.
function resolveKey(pathname: string): string | null {
  const trimmed = pathname.replace(/^\/+/, "");
  const key = trimmed === "" ? "index.html" : trimmed;

  if (key.includes("..") || key.includes("\\") || key.startsWith("/")) {
    return null;
  }

  return key;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (req.method !== "GET" && req.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }

    const url = new URL(req.url);
    const key = resolveKey(url.pathname);
    if (!key) {
      return new Response("Bad request", { status: 400 });
    }

    const obj = await env.VAULT.get(key);
    if (!obj) {
      return new Response("Not found", { status: 404 });
    }

    const headers = new Headers();
    obj.writeHttpMetadata(headers);
    headers.set("Cache-Control", "private, no-store");
    headers.set("X-Content-Type-Options", "nosniff");
    headers.set("Referrer-Policy", "no-referrer");

    if (req.method === "HEAD") {
      return new Response(null, { headers });
    }

    return new Response(obj.body, { headers });
  },
};
