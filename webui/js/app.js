// App frame and hash router: #/browse (default) · #/resource/<id> · #/new/<type>[/<parentId>]

import { html, render, useEffect, useState } from "../vendor/htm-preact-standalone.module.js";
import { Browse } from "./views/browse.js";
import { Resource, NewResource } from "./views/resource.js";

function useHash() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const onChange = () => setHash(location.hash);
    addEventListener("hashchange", onChange);
    return () => removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

function route(hash) {
  const parts = hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  switch (parts[0]) {
    case "resource": return { page: "resource", view: html`<${Resource} id=${parts[1]} />` };
    case "new": return { page: "browse", view: html`<${NewResource} type=${parts[1]} parentId=${parts[2]} />` };
    default: return { page: "browse", view: html`<${Browse} />` };
  }
}

function App() {
  const { page, view } = route(useHash());
  return html`
    <header>
      <span class="brand">CBX Core</span>
      <nav><a href="#/browse" class=${page === "browse" ? "active" : ""}>Browse</a>
        <a href="/api/docs" target="_blank" rel="noopener">API docs</a></nav>
    </header>
    <main>${view}</main>`;
}

render(html`<${App} />`, document.getElementById("app"));
