/**
 * Neutrally API client for plugin hooks.
 * All calls are authenticated via the CLI token from ~/.neutrally/credentials.json
 */

const DEFAULT_TIMEOUT_MS = 6000;

/**
 * Fetch with a timeout. Returns null on timeout or network error.
 */
async function fetchSafe(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * GET /api/memory/context — user profile, stack, projects, recent conversations
 */
export async function fetchContext(apiBase, headers) {
  try {
    const res = await fetchSafe(`${apiBase}/api/memory/context`, { headers });
    if (!res?.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * GET /api/memory/search?query= — semantic search across conversations
 */
export async function searchMemory(apiBase, headers, query) {
  try {
    const res = await fetchSafe(
      `${apiBase}/api/memory/search?query=${encodeURIComponent(query)}`,
      { headers }
    );
    if (!res?.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

/**
 * GET /api/memory/recent?limit= — most recent messages across all conversations
 */
export async function fetchRecentMessages(apiBase, headers, limit = 5) {
  try {
    const res = await fetchSafe(
      `${apiBase}/api/memory/recent?limit=${limit}`,
      { headers }
    );
    if (!res?.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : (data?.messages || []);
  } catch {
    return [];
  }
}

/**
 * GET /api/v1/memory?type= — stored memory items
 */
export async function fetchMemoryItems(apiBase, headers, type = null) {
  try {
    const url = type
      ? `${apiBase}/api/v1/memory?type=${encodeURIComponent(type)}`
      : `${apiBase}/api/v1/memory`;
    const res = await fetchSafe(url, { headers });
    if (!res?.ok) return [];
    const data = await res.json();
    return data?.items || [];
  } catch {
    return [];
  }
}

/**
 * POST /api/v1/memory — save a structured memory item
 */
export async function saveMemoryItem(apiBase, headers, { type, title, content, metadata = {} }) {
  try {
    const res = await fetchSafe(
      `${apiBase}/api/v1/memory`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ type, title, content, metadata }),
      },
      10000
    );
    return res?.ok ?? false;
  } catch {
    return false;
  }
}

/**
 * Flush an array of session exchanges to the Neutrally API as memory items.
 * Each exchange = { userMessage, tools[], projectName, projectPath }
 */
export async function flushExchanges(apiBase, headers, exchanges) {
  const results = [];
  for (const exchange of exchanges) {
    if (!exchange.userMessage && !exchange.tools?.length) continue;

    const toolLines = (exchange.tools || []).map(t => `  · ${t}`).join('\n');
    const content = [
      exchange.userMessage ? `User: ${exchange.userMessage}` : null,
      toolLines ? `Claude:\n${toolLines}` : null,
    ]
      .filter(Boolean)
      .join('\n');

    if (!content.trim()) continue;

    const now = new Date();
    const dateStr = now.toISOString().slice(0, 16).replace('T', ' ');
    const project = exchange.projectName || 'session';
    const title = `Claude Code · ${project} · ${dateStr}`;

    const ok = await saveMemoryItem(apiBase, headers, {
      type: 'note',
      title,
      content,
      metadata: {
        source: 'claude-code-plugin',
        projectPath: exchange.projectPath || '',
        capturedAt: now.toISOString(),
      },
    });
    results.push(ok);
  }
  return results;
}
