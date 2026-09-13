// Fetch wrapper over the REST API. Errors carry the API's detail message.

async function call(method, path, body) {
  const resp = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (resp.status === 204) return null;
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : JSON.stringify(d ?? `${resp.status} ${resp.statusText}`));
  }
  return data;
}

const enc = encodeURIComponent;

export const api = {
  schema: () => call("GET", "/api/schema"),
  nodes: () => call("GET", "/api/nodes"),
  node: (id) => call("GET", `/api/nodes/${enc(id)}`),
  createNode: (body) => call("POST", "/api/nodes", body),
  patchNode: (id, body) => call("PATCH", `/api/nodes/${enc(id)}`, body),
  deleteNode: (id) => call("DELETE", `/api/nodes/${enc(id)}`),
  nodeEdges: (id) => call("GET", `/api/nodes/${enc(id)}/edges`),
  edges: () => call("GET", "/api/edges"),
  createEdge: (body) => call("POST", "/api/edges", body),
  deleteEdge: (id) => call("DELETE", `/api/edges/${enc(id)}`),
};
