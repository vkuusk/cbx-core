// Resource page: view, edit, delete one node and see its edges. NewResource creates a node
// under a parent and links it with the edge the schema allows.

import { html, useEffect, useState } from "../../vendor/htm-preact-standalone.module.js";
import { api } from "../api.js";

const BINDING = ["provider", "native_type", "native_id", "region"];

const tagsToText = (tags) => Object.entries(tags ?? {}).map(([k, v]) => `${k}=${v}`).join("\n");
const textToTags = (text) =>
  Object.fromEntries(text.split("\n").filter((l) => l.includes("=")).map((l) => {
    const i = l.indexOf("=");
    return [l.slice(0, i).trim(), l.slice(i + 1).trim()];
  }));

// form state <-> API body
function toForm(node, attrNames) {
  return {
    name: node.name ?? "",
    ...Object.fromEntries(BINDING.map((k) => [k, node[k] ?? ""])),
    attrs: Object.fromEntries(attrNames.map((a) => [a, node.attrs?.[a] ?? ""])),
    tags: tagsToText(node.tags),
    native: JSON.stringify(node.native ?? {}, null, 2),
  };
}

function toBody(form) {
  const attrs = Object.fromEntries(Object.entries(form.attrs).filter(([, v]) => v !== ""));
  return {
    name: form.name,
    ...Object.fromEntries(BINDING.map((k) => [k, form[k] || null])),
    attrs,
    tags: textToTags(form.tags),
    native: JSON.parse(form.native || "{}"),
  };
}

// `locked`: provider cannot change after create
function Form({ type, schema, form, setForm, attrNames, onSubmit, submitLabel, extra, locked }) {
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setAttr = (k) => (e) => setForm({ ...form, attrs: { ...form.attrs, [k]: e.target.value } });
  const nativeIdHint = schema.providers[form.provider]?.native_id ?? "";
  return html`<form class="res" onSubmit=${(e) => { e.preventDefault(); onSubmit(); }}>
    <label>type</label><div><span class="badge">${type}</span> <span class="muted">${schema.types[type]?.description}</span></div>
    <label>name</label><input value=${form.name} onInput=${set("name")} required />
    <label>provider</label>
    <select value=${form.provider} onChange=${set("provider")} disabled=${locked}>
      <option value="">—</option>
      ${Object.keys(schema.providers).map((p) => html`<option value=${p}>${p}</option>`)}
    </select>
    <label>native_type</label><input value=${form.native_type} onInput=${set("native_type")} />
    <label>native_id</label><input value=${form.native_id} onInput=${set("native_id")} placeholder=${nativeIdHint} />
    <label>region</label><input value=${form.region} onInput=${set("region")} />
    ${attrNames.map((a) => html`<label>${a}</label><input value=${form.attrs[a]} onInput=${setAttr(a)} />`)}
    <label>tags</label><textarea placeholder="key=value per line" value=${form.tags} onInput=${set("tags")} />
    <label>native</label><textarea value=${form.native} onInput=${set("native")} />
    <div class="actions"><button class="primary" type="submit">${submitLabel}</button>${extra}</div>
  </form>`;
}

function EdgeTable({ title, edges, names, other, onDelete }) {
  if (!edges.length) return null;
  return html`<h2>${title}</h2>
    <table>
      ${edges.map((e) => html`<tr>
        <td>${e.type}</td>
        <td><a href=${`#/resource/${other(e)}`}>${names.get(other(e)) ?? other(e)}</a></td>
        <td><button class="danger" onClick=${() => onDelete(e.id)}>unlink</button></td>
      </tr>`)}
    </table>`;
}

// Add an outgoing edge: pick an edge type the schema allows from this node's type, then a
// target among nodes of the allowed type.
function AddLink({ node, nodes, schema, onAdd }) {
  const options = schema.triples.filter((t) => t.from === node.type);
  const [edge, setEdge] = useState(options[0]?.edge ?? "");
  const [target, setTarget] = useState("");
  if (!options.length) return null;
  const toTypes = new Set(options.filter((t) => t.edge === edge).map((t) => t.to));
  const targets = nodes.filter((n) => toTypes.has(n.type) && n.id !== node.id);
  return html`<h2>Link</h2>
    <div class="actions">
      <select value=${edge} onChange=${(e) => { setEdge(e.target.value); setTarget(""); }}>
        ${[...new Set(options.map((t) => t.edge))].map((e) => html`<option value=${e}>${e}</option>`)}
      </select>
      <select value=${target} onChange=${(e) => setTarget(e.target.value)}>
        <option value="">— choose target —</option>
        ${targets.map((n) => html`<option value=${n.id}>${n.type} · ${n.name}</option>`)}
      </select>
      <button type="button" disabled=${!target} onClick=${() => { onAdd({ type: edge, from_id: node.id, to_id: target }); setTarget(""); }}>Add</button>
    </div>`;
}

export function Resource({ id }) {
  const [state, setState] = useState(null);
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [confirm, setConfirm] = useState(false);

  const load = () =>
    Promise.all([api.node(id), api.nodeEdges(id), api.nodes(), api.schema()])
      .then(([node, edges, nodes, schema]) => {
        const attrNames = schema.types[node.type]?.attributes ?? [];
        setState({ node, edges, nodes, schema, names: new Map(nodes.map((n) => [n.id, n.name])), attrNames });
        setForm(toForm(node, attrNames));
        setError(null);
      })
      .catch((e) => setError(e.message));
  useEffect(() => { load(); setConfirm(false); }, [id]);

  if (error) return html`<p class="error">${error}</p>`;
  if (!state) return html`<p class="muted">Loading…</p>`;
  const { node, edges, nodes, schema, names, attrNames } = state;

  const save = () => {
    try { api.patchNode(id, toBody(form)).then(load).catch((e) => setError(e.message)); }
    catch (e) { setError(e.message); }
  };
  const remove = () => api.deleteNode(id).then(() => { location.hash = "#/browse"; }).catch((e) => setError(e.message));
  const unlink = (eid) => api.deleteEdge(eid).then(load).catch((e) => setError(e.message));
  const link = (body) => api.createEdge(body).then(load).catch((e) => setError(e.message));

  const del = confirm
    ? html`<button type="button" class="danger" onClick=${remove}>Confirm delete</button>
           <button type="button" onClick=${() => setConfirm(false)}>Cancel</button>`
    : html`<button type="button" class="danger" onClick=${() => setConfirm(true)}>Delete</button>`;

  return html`
    <h1>${node.name} <span class="muted">${node.type}</span></h1>
    <p class="muted">id ${node.id} · created ${node.created_at} · updated ${node.updated_at}</p>
    <${Form} type=${node.type} schema=${schema} form=${form} setForm=${setForm} attrNames=${attrNames}
             onSubmit=${save} submitLabel="Save" extra=${del} locked=${true} />
    <${EdgeTable} title="Outgoing" edges=${edges.out} names=${names} other=${(e) => e.to_id} onDelete=${unlink} />
    <${EdgeTable} title="Incoming" edges=${edges.in} names=${names} other=${(e) => e.from_id} onDelete=${unlink} />
    <${AddLink} node=${node} nodes=${nodes} schema=${schema} onAdd=${link} />`;
}

export function NewResource({ type, parentId }) {
  const [ctx, setCtx] = useState(null);
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.schema(), parentId ? api.node(parentId) : null])
      .then(([schema, parent]) => {
        const attrNames = schema.types[type]?.attributes ?? [];
        setCtx({ schema, parent, attrNames });
        setForm(toForm({ provider: parent?.provider, region: parent?.region }, attrNames));
      })
      .catch((e) => setError(e.message));
  }, [type, parentId]);

  if (error && !form) return html`<p class="error">${error}</p>`;
  if (!form) return html`<p class="muted">Loading…</p>`;
  const { schema, parent, attrNames } = ctx;

  // the edge that links the new node to its parent
  const link = parent && schema.triples.find(
    (t) => (t.edge === "CONTAINS" && t.from === parent.type && t.to === type) ||
           (t.edge === "RUNS_IN" && t.from === type && t.to === parent.type));

  const create = async () => {
    try {
      const node = await api.createNode({ type, ...toBody(form) });
      if (link) {
        const [from_id, to_id] = link.edge === "CONTAINS" ? [parent.id, node.id] : [node.id, parent.id];
        await api.createEdge({ type: link.edge, from_id, to_id });
      }
      location.hash = `#/resource/${node.id}`;
    } catch (e) { setError(e.message); }
  };

  return html`
    <h1>New ${type}</h1>
    ${parent ? html`<p class="muted">under <a href=${`#/resource/${parent.id}`}>${parent.name}</a> (${parent.type})</p>` : null}
    ${error ? html`<p class="error">${error}</p>` : null}
    <${Form} type=${type} schema=${schema} form=${form} setForm=${setForm} attrNames=${attrNames}
             onSubmit=${create} submitLabel="Create"
             extra=${html`<a href=${parent ? `#/resource/${parent.id}` : "#/browse"}><button type="button">Cancel</button></a>`} />`;
}
