// Browse page: the graph as a tree. Children of a node are CONTAINS targets and RUNS_IN sources.

import { html, useEffect, useState } from "../../vendor/htm-preact-standalone.module.js";
import { api } from "../api.js";

// child types a node of `type` may get, from the schema triples
export function childTypes(schema, type) {
  return schema.triples
    .filter((t) => (t.edge === "CONTAINS" && t.from === type) || (t.edge === "RUNS_IN" && t.to === type))
    .map((t) => (t.edge === "CONTAINS" ? t.to : t.from));
}

function buildTree(nodes, edges) {
  const children = new Map(nodes.map((n) => [n.id, []]));
  const hasParent = new Set();
  for (const e of edges) {
    const [parent, child] = e.type === "CONTAINS" ? [e.from_id, e.to_id] : [e.to_id, e.from_id];
    if (children.has(parent) && children.has(child)) {
      children.get(parent).push(child);
      hasParent.add(child);
    }
  }
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const roots = nodes.filter((n) => !hasParent.has(n.id)).map((n) => n.id);
  return { byId, children, roots };
}

function TreeNode({ id, tree, schema }) {
  const [open, setOpen] = useState(true);
  const node = tree.byId.get(id);
  const kids = tree.children.get(id);
  return html`<li>
    <div class="row">
      <span class="toggle" onClick=${() => setOpen(!open)}>${kids.length ? (open ? "▾" : "▸") : ""}</span>
      <span class="badge">${node.type}</span>
      <a href=${`#/resource/${id}`}>${node.name}</a>
      ${childTypes(schema, node.type).map((t) => html`<a class="add" href=${`#/new/${t}/${id}`}>+ ${t}</a>`)}
    </div>
    ${open && kids.length ? html`<ul>${kids.map((k) => html`<${TreeNode} key=${k} id=${k} tree=${tree} schema=${schema} />`)}</ul>` : null}
  </li>`;
}

export function Browse() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    Promise.all([api.nodes(), api.edges(), api.schema()])
      .then(([nodes, edges, schema]) => setData({ tree: buildTree(nodes, edges), schema }))
      .catch((e) => setError(e.message));
  }, []);
  if (error) return html`<p class="error">${error}</p>`;
  if (!data) return html`<p class="muted">Loading…</p>`;
  const { tree, schema } = data;
  return html`
    <h1>Browse</h1>
    <div class="tree">
      ${tree.roots.length
        ? html`<ul>${tree.roots.map((r) => html`<${TreeNode} key=${r} id=${r} tree=${tree} schema=${schema} />`)}</ul>`
        : html`<p class="muted">The graph is empty.</p>`}
    </div>
    <p><a href="#/new/Organization">+ Organization</a></p>`;
}
