const BACKEND_BASE_URL =
  process.env.SUPPLIER_API_URL ?? "http://127.0.0.1:8000";

function buildTargetUrl(requestUrl: string, path: string[]): URL {
  const incomingUrl = new URL(requestUrl);
  const targetUrl = new URL(
    path.join("/"),
    BACKEND_BASE_URL.endsWith("/")
      ? BACKEND_BASE_URL
      : `${BACKEND_BASE_URL}/`,
  );
  targetUrl.search = incomingUrl.search;
  return targetUrl;
}

async function proxyRequest(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const targetUrl = buildTargetUrl(request.url, path);

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const accept = request.headers.get("accept");
  if (accept) {
    headers.set("accept", accept);
  }

  const method = request.method.toUpperCase();
  const shouldSendBody = method !== "GET" && method !== "HEAD";

  try {
    const upstreamResponse = await fetch(targetUrl, {
      method,
      headers,
      body: shouldSendBody ? await request.text() : undefined,
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    const upstreamContentType = upstreamResponse.headers.get("content-type");
    if (upstreamContentType) {
      responseHeaders.set("content-type", upstreamContentType);
    }

    return new Response(await upstreamResponse.text(), {
      status: upstreamResponse.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "backend unavailable" },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
