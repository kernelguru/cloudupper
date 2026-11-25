/* CloudUpper – Frontend (ohne Build-Schritt, Vanilla JS) */
"use strict";

// ------------------------------------------------------------------ Icons
const ICONS = {
  upload: '<path d="M12 16V4m0 0-4.5 4.5M12 4l4.5 4.5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  download: '<path d="M12 4v12m0 0-4.5-4.5M12 16l4.5-4.5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  bolt: '<path d="M13 3 5 13.5h6L10 21l8-10.5h-6L13 3Z"/>',
  list: '<path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
  cloud: '<path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 8.5 4.75 4.75 0 0 1 17.5 18H7Z"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>',
  folderPlus: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path d="M12 10v6M9 13h6"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/>',
  server: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
  phone: '<rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M11 18.5h2"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.9-3.9M4 4v4h4M4 13a8 8 0 0 0 14.9 3.9M20 20v-4h-4"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>',
  retry: '<path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>',
  arrow: '<path d="M5 12h14m0 0-5-5m5 5-5 5"/>',
  logout: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 16l4-4-4-4M14 12H4"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9M17 6l3 3M14 9l2 2"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
};
const icon = (n, cls = "") => `<svg class="ic ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ""}</svg>`;
function hydrateIcons(root = document) {
  root.querySelectorAll("i[data-icon]").forEach((el) => { el.outerHTML = icon(el.dataset.icon); });
}

// Farben/Labels der rclone-Typen
const TYPES = {
  drive: { label: "Google Drive", color: "#1a73e8" },
  onedrive: { label: "OneDrive", color: "#0a64d6" },
  hidrive: { label: "HiDrive", color: "#ff7a00" },
  dropbox: { label: "Dropbox", color: "#0061fe" },
  webdav: { label: "WebDAV", color: "#0082c9" },
  sftp: { label: "SFTP", color: "#4b5563" },
  s3: { label: "S3", color: "#c7511f" },
  pcloud: { label: "pCloud", color: "#17bed0" },
  mega: { label: "MEGA", color: "#d9272e" },
  box: { label: "Box", color: "#0061d5" },
  local: { label: "Server", color: "#6d5efc" },
};
const typeInfo = (t) => TYPES[t] || { label: t, color: "#6b7280" };
const logo = (t, size = 44) => `<div class="logo" style="background:${typeInfo(t).color};width:${size}px;height:${size}px">${icon(t === "local" ? "server" : "cloud")}</div>`;

// ------------------------------------------------------------------ Helfer
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem("cu." + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("cu." + k, JSON.stringify(v)); } catch { /* privat */ } },
};
function fmtBytes(n) {
  if (n == null || n < 0) return "–";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${u[i]}`;
}
function fmtEta(s) {
  if (s == null || s < 0) return "";
  s = Math.round(s);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 12));
const joinPath = (...p) => p.filter(Boolean).join("/").replace(/\/+/g, "/").replace(/^\/|\/$/g, "");

function toast(msg, kind = "") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = msg;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), kind === "err" ? 6000 : 3200);
}

async function api(path, opts = {}) {
  const init = { credentials: "same-origin", method: opts.method || (opts.body ? "POST" : "GET"), headers: {} };
  if (opts.body !== undefined) { init.body = JSON.stringify(opts.body); init.headers["Content-Type"] = "application/json"; }
  const r = await fetch("/api" + path, init);
  if (r.status === 401 && path !== "/login") { showLogin(); throw new Error("Nicht angemeldet"); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : r.statusText || "Fehler");
  return data;
}

// ------------------------------------------------------------------ Zustand
const S = {
  view: "upload",
  status: {},
  remotes: [],
  jobs: [],
  uploadMode: store.get("uploadMode", "server"),
  local: { path: store.get("localPath", ""), entries: [], sel: new Set(), filter: "", loading: false },
  move: false,
  device: { queue: [], busy: false },
  dest: {
    upload: store.get("dest.upload", null),
    torbox: store.get("dest.torbox", { remote: "", path: "downloads" }),
  },
  recent: store.get("recentDest", []),
  torbox: { kind: "torrents", items: [], sel: new Map(), open: new Set(), filter: "", loading: false, error: "" },
  about: {},
};

// ------------------------------------------------------------------ Navigation
const TITLES = { upload: "Hochladen", torbox: "TorBox", jobs: "Aufträge", clouds: "Clouds" };
function go(view) {
  S.view = view;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  $("#viewTitle").textContent = TITLES[view];
  if (location.hash.slice(1).split("?")[0] !== view) history.replaceState(null, "", "#" + view);
  render();
  if (view === "upload" && S.uploadMode === "server") loadLocal();
  if (view === "torbox") loadTorbox();
  if (view === "clouds") loadAbout();
  if (view === "jobs") pollJobs();
  window.scrollTo({ top: 0 });
}

function render() {
  const v = S.view;
  const top = $("#topActions");
  top.innerHTML = "";
  if (v === "upload" && S.uploadMode === "server") top.innerHTML = `<button class="icon-btn" data-action="local-refresh" aria-label="Aktualisieren">${icon("refresh")}</button>`;
  if (v === "torbox") top.innerHTML = `<button class="icon-btn" data-action="tb-refresh" aria-label="Aktualisieren">${icon("refresh", S.torbox.loading ? "spin" : "")}</button>`;
  if (v === "jobs") top.innerHTML = `<button class="btn sm" data-action="jobs-clear">Erledigte entfernen</button>`;
  if (v === "clouds" && S.status.auth) top.innerHTML = `<button class="icon-btn" data-action="logout" aria-label="Abmelden">${icon("logout")}</button>`;
  $("#view").innerHTML = ({ upload: viewUpload, torbox: viewTorbox, jobs: viewJobs, clouds: viewClouds })[v]();
}

let renderQueued = false;
function scheduleRender() {
  if (renderQueued) return;
  renderQueued = true;
  setTimeout(() => { renderQueued = false; render(); }, 250);
}

// ------------------------------------------------------------------ Ziel-Komponente
function destLabel(d) {
  if (!d) return "Bitte Ziel wählen";
  return `${d.remote || "Server"}:/${d.path || ""}`;
}
function destType(d) {
  if (!d || !d.remote) return "local";
  return (S.remotes.find((r) => r.name === d.remote) || {}).type || "cloud";
}
function destCard(ctx, title) {
  const d = S.dest[ctx];
  const valid = d && (!d.remote || S.remotes.some((r) => r.name === d.remote));
  return `<div class="card dest">
    ${logo(valid ? destType(d) : "local")}
    <div class="grow"><div class="label">${esc(title)}</div>
      <div class="val ellipsis">${valid ? esc(destLabel(d)) : "Noch kein Ziel gewählt"}</div></div>
    <button class="btn sm" data-action="pick-dest" data-ctx="${ctx}">Ändern</button>
  </div>`;
}

// ------------------------------------------------------------------ Ansicht: Upload
function viewUpload() {
  const seg = `<div class="seg">
      <button class="${S.uploadMode === "server" ? "active" : ""}" data-action="upload-mode" data-mode="server">${icon("server")} Vom Server</button>
      <button class="${S.uploadMode === "device" ? "active" : ""}" data-action="upload-mode" data-mode="device">${icon("phone")} Vom Gerät</button>
    </div>`;
  const noRemotes = !S.remotes.length ? `<div class="banner">Noch keine Cloud verbunden. <a href="#clouds" data-action="nav" data-view="clouds">Jetzt verbinden →</a></div>` : "";
  return seg + noRemotes + destCard("upload", "Hochladen nach") + (S.uploadMode === "server" ? viewLocal() : viewDevice());
}

function viewLocal() {
  const L = S.local;
  const parts = L.path ? L.path.split("/") : [];
  const crumbs = [`<button data-action="local-cd" data-path="">Server</button>`]
    .concat(parts.map((p, i) => `<span>/</span><button data-action="local-cd" data-path="${esc(parts.slice(0, i + 1).join("/"))}">${esc(p)}</button>`)).join("");
  const q = L.filter.toLowerCase();
  const entries = L.entries.filter((e) => !q || e.name.toLowerCase().includes(q));
  const rows = entries.map((e) => {
    const p = joinPath(L.path, e.name);
    const sel = L.sel.has(p);
    return `<li class="clickable ${sel ? "sel" : ""}" data-action="${e.dir ? "local-cd" : "local-toggle"}" data-path="${esc(p)}">
      <input type="checkbox" class="cb" ${sel ? "checked" : ""} data-action="local-toggle" data-path="${esc(p)}" aria-label="Auswählen">
      <div class="ico ${e.dir ? "folder" : ""}">${icon(e.dir ? "folder" : "file")}</div>
      <div class="grow"><div class="ellipsis">${esc(e.name)}</div><div class="meta">${e.dir ? "Ordner" : fmtBytes(e.size)}</div></div>
      ${e.dir ? icon("chevron") : ""}
    </li>`;
  }).join("");
  const n = L.sel.size;
  return `<div class="card flush">
      <div class="crumbs">${crumbs}</div>
      <div style="padding:10px 16px;border-bottom:1px solid var(--line)" class="row">
        <input type="search" placeholder="Filtern…" value="${esc(L.filter)}" data-input="local-filter">
        <button class="btn sm" data-action="local-all">${entries.length && entries.every((e) => L.sel.has(joinPath(L.path, e.name))) ? "Keine" : "Alle"}</button>
      </div>
      ${L.loading ? `<div class="empty">Lade…</div>` : rows ? `<ul class="list">${rows}</ul>` : `<div class="empty">${icon("folder")}<br>Ordner ist leer.<br><span class="small">Lege Dateien in das gemountete Datenverzeichnis (${esc(S.status.data_dir || "/data")}).</span></div>`}
    </div>
    <label class="check card" style="padding:12px 16px"><input type="checkbox" data-action="toggle-move" ${S.move ? "checked" : ""}> <span><b>Verschieben</b><br><span class="small muted">Dateien nach erfolgreichem Upload auf dem Server löschen</span></span></label>
    <div class="actionbar">
      <div class="grow small"><b>${n}</b> ausgewählt${n ? ` <button class="btn ghost sm" data-action="local-clear">zurücksetzen</button>` : ""}</div>
      <button class="btn primary" data-action="upload-server" ${n && S.dest.upload ? "" : "disabled"}>${icon("upload")} Hochladen</button>
    </div>`;
}

async function loadLocal() {
  S.local.loading = !S.local.entries.length;
  if (S.view === "upload") render();
  try {
    const r = await api(`/browse?path=${encodeURIComponent(S.local.path)}`);
    S.local.entries = r.entries;
  } catch (e) {
    if (S.local.path) { S.local.path = ""; return loadLocal(); }
    toast(e.message, "err");
  } finally {
    S.local.loading = false;
    store.set("localPath", S.local.path);
    if (S.view === "upload" && S.uploadMode === "server") render();
  }
}

async function uploadServer() {
  const d = S.dest.upload;
  try {
    const r = await api("/upload/server", { body: { items: [...S.local.sel], remote: d.remote, path: d.path, move: S.move } });
    toast(`${r.jobs.length} Auftrag/Aufträge gestartet`, "ok");
    S.local.sel.clear();
    pollJobs(true);
    render();
  } catch (e) { toast(e.message, "err"); }
}

// ---------------------------------------------- Upload vom Gerät (chunked, fortsetzbar)
const CHUNK = 16 * 1024 * 1024;

function viewDevice() {
  const Q = S.device.queue;
  const rows = Q.map((f, i) => {
    const pct = f.size ? Math.round((f.sent / f.size) * 100) : 0;
    const chip = f.state === "done" ? `<span class="chip ok">${icon("check")} übergeben</span>`
      : f.state === "error" ? `<span class="chip err">Fehler</span>`
      : f.state === "uploading" ? `<span class="chip run">${pct}%</span>` : `<span class="chip">wartet</span>`;
    return `<li><div class="ico">${icon("file")}</div>
      <div class="grow stack" style="gap:6px"><div class="row"><div class="grow ellipsis">${esc(f.file.name)}</div>${chip}</div>
      <div class="bar ${f.state === "done" ? "ok" : f.state === "error" ? "err" : ""}"><div style="width:${pct}%"></div></div>
      <div class="meta">${fmtBytes(f.sent)} / ${fmtBytes(f.size)}${f.speed ? ` · ${fmtBytes(f.speed)}/s` : ""}${f.error ? ` · ${esc(f.error)}` : ""}</div></div>
      ${f.state !== "uploading" ? `<button class="icon-btn" data-action="dev-remove" data-i="${i}" aria-label="Entfernen">${icon("x")}</button>` : ""}
    </li>`;
  }).join("");
  const pending = Q.filter((f) => f.state === "queued" || f.state === "error").length;
  return `<label class="drop" id="drop">${icon("upload")}<span>Dateien auswählen</span><span class="small muted">Fotos, Videos & Dateien – oder hierher ziehen</span>
      <input type="file" multiple hidden data-input="dev-files"></label>
    ${Q.length ? `<div class="card flush"><ul class="list">${rows}</ul></div>` : ""}
    <p class="small muted" style="margin:0">Tipp: Lass die App während der Übertragung geöffnet. Große Dateien werden in Abschnitten übertragen und können nach einem Abbruch fortgesetzt werden.</p>
    <div class="actionbar">
      <div class="grow small"><b>${pending}</b> bereit</div>
      ${Q.some((f) => f.state === "done") ? `<button class="btn ghost sm" data-action="dev-clear">Liste leeren</button>` : ""}
      <button class="btn primary" data-action="dev-start" ${pending && S.dest.upload && !S.device.busy ? "" : "disabled"}>${icon("upload")} ${S.device.busy ? "Läuft…" : "Hochladen"}</button>
    </div>`;
}

function addDeviceFiles(files) {
  for (const file of files) S.device.queue.push({ file, id: uid(), size: file.size, sent: 0, state: "queued", error: "" });
  render();
}

function putChunk(id, offset, blob, onProgress) {
  return new Promise((resolve, reject) => {
    const x = new XMLHttpRequest();
    x.open("PUT", `/api/upload/device/${id}?offset=${offset}`);
    x.upload.onprogress = (e) => onProgress(e.loaded);
    x.onload = () => {
      let data = {}; try { data = JSON.parse(x.responseText); } catch { /* leer */ }
      if (x.status === 200 || x.status === 409) resolve({ status: x.status, size: data.size ?? 0 });
      else if (x.status === 401) { showLogin(); reject(new Error("Nicht angemeldet")); }
      else reject(new Error(data.detail || `HTTP ${x.status}`));
    };
    x.onerror = () => reject(new Error("Netzwerkfehler"));
    x.send(blob);
  });
}

let wakeLock = null;
async function startDeviceUploads() {
  const d = S.dest.upload;
  if (!d || S.device.busy) return;
  S.device.busy = true;
  try { wakeLock = await navigator.wakeLock?.request("screen"); } catch { /* nicht unterstützt */ }
  render();
  for (const f of S.device.queue) {
    if (f.state !== "queued" && f.state !== "error") continue;
    f.state = "uploading"; f.error = "";
    try {
      // vorhandenen Stand abfragen (Fortsetzen)
      let offset = (await api(`/upload/device/${f.id}`)).size;
      let retries = 0;
      while (offset < f.size) {
        const end = Math.min(offset + CHUNK, f.size);
        const t0 = performance.now();
        try {
          const r = await putChunk(f.id, offset, f.file.slice(offset, end), (loaded) => {
            f.sent = offset + loaded;
            f.speed = loaded / Math.max(0.001, (performance.now() - t0) / 1000);
            if (S.view === "upload") scheduleRender();
          });
          offset = r.size; retries = 0;
        } catch (e) {
          if (++retries > 5) throw e;
          await new Promise((res) => setTimeout(res, 1500 * retries));
          offset = (await api(`/upload/device/${f.id}`)).size;
        }
        f.sent = offset;
      }
      await api(`/upload/device/${f.id}/complete`, { body: { name: f.file.name, size: f.size, remote: d.remote, path: d.path } });
      f.state = "done"; f.speed = 0;
      pollJobs(true);
    } catch (e) {
      f.state = "error"; f.error = e.message; f.speed = 0;
    }
    if (S.view === "upload") render();
  }
  S.device.busy = false;
  try { await wakeLock?.release(); } catch { /* egal */ }
  render();
  const failed = S.device.queue.filter((f) => f.state === "error").length;
  toast(failed ? `${failed} Datei(en) fehlgeschlagen` : "Alle Dateien übergeben – Upload in die Cloud läuft", failed ? "err" : "ok");
}

// ------------------------------------------------------------------ Ordner-Auswahl
const picker = { ctx: null, remote: "", path: "", entries: [], loading: false, error: "" };

function openPicker(ctx) {
  const cur = S.dest[ctx] || { remote: S.remotes[0]?.name || "", path: "" };
  Object.assign(picker, { ctx, remote: cur.remote, path: cur.path, entries: [], error: "" });
  openSheet("Zielordner wählen", "");
  loadPicker();
}

async function loadPicker() {
  picker.loading = true; picker.error = ""; renderPicker();
  try {
    const r = await api(`/browse?dirs_only=true&remote=${encodeURIComponent(picker.remote)}&path=${encodeURIComponent(picker.path)}`);
    picker.entries = r.entries;
  } catch (e) { picker.entries = []; picker.error = e.message; }
  picker.loading = false; renderPicker();
}

function renderPicker() {
  const remotes = [{ name: "", type: "local" }, ...S.remotes];
  const chips = remotes.map((r) => `<button class="chip ${r.name === picker.remote ? "active" : ""}" data-action="pk-remote" data-remote="${esc(r.name)}">${esc(r.name || "Server")}</button>`).join("");
  const recent = S.recent.filter((d) => !d.remote || S.remotes.some((r) => r.name === d.remote));
  const parts = picker.path ? picker.path.split("/") : [];
  const crumbs = [`<button data-action="pk-cd" data-path="">${esc(picker.remote || "Server")}:</button>`]
    .concat(parts.map((p, i) => `<span>/</span><button data-action="pk-cd" data-path="${esc(parts.slice(0, i + 1).join("/"))}">${esc(p)}</button>`)).join("");
  const rows = picker.entries.map((e) => `<li class="clickable" data-action="pk-cd" data-path="${esc(joinPath(picker.path, e.name))}">
      <div class="ico folder">${icon("folder")}</div><div class="grow ellipsis">${esc(e.name)}</div>${icon("chevron")}</li>`).join("");
  $("#sheetBody").innerHTML = `
    <div class="chips">${chips}</div>
    ${recent.length ? `<div class="small muted">Zuletzt verwendet</div><div class="chips">${recent.map((d, i) => `<button class="chip" data-action="pk-recent" data-i="${i}">${icon("folder")}${esc(destLabel(d))}</button>`).join("")}</div>` : ""}
    <div class="card flush">
      <div class="crumbs">${crumbs}</div>
      ${picker.loading ? `<div class="empty">Lade…</div>` : picker.error ? `<div class="empty error">${esc(picker.error)}</div>` : rows ? `<ul class="list">${rows}</ul>` : `<div class="empty">Keine Unterordner</div>`}
    </div>
    <div class="row">
      <input type="text" placeholder="Neuer Ordner…" id="pkNew" enterkeyhint="done">
      <button class="btn" data-action="pk-mkdir">${icon("folderPlus")}</button>
    </div>
    <button class="btn primary block" data-action="pk-choose">${icon("check")} Hier speichern: ${esc(destLabel({ remote: picker.remote, path: picker.path }))}</button>`;
}

function chooseDest(d) {
  S.dest[picker.ctx] = d;
  store.set("dest." + picker.ctx, d);
  S.recent = [d, ...S.recent.filter((x) => x.remote !== d.remote || x.path !== d.path)].slice(0, 6);
  store.set("recentDest", S.recent);
  closeSheet();
  render();
}

// ------------------------------------------------------------------ Ansicht: TorBox
function viewTorbox() {
  const T = S.torbox;
  if (!S.status.torbox) {
    return `<div class="card stack"><h3>TorBox verbinden</h3>
      <p class="muted" style="margin:0">Hinterlege deinen API-Key (TorBox → Einstellungen → API-Key).</p>
      <input type="password" id="tbKey" placeholder="TorBox API-Key">
      <button class="btn primary" data-action="tb-savekey">Speichern</button></div>`;
  }
  const seg = `<div class="seg">${[["torrents", "Torrents"], ["webdl", "Web"], ["usenet", "Usenet"]]
    .map(([k, l]) => `<button class="${T.kind === k ? "active" : ""}" data-action="tb-kind" data-kind="${k}">${l}</button>`).join("")}</div>`;
  const add = T.kind !== "usenet" ? `<div class="row"><input type="text" id="tbAdd" placeholder="${T.kind === "torrents" ? "Magnet-Link einfügen…" : "Download-Link einfügen…"}" enterkeyhint="go">
      <button class="btn" data-action="tb-add">${icon("plus")}</button></div>` : "";
  const q = T.filter.toLowerCase();
  const items = T.items.filter((i) => !q || i.name.toLowerCase().includes(q));
  const rows = items.map((it) => {
    const files = it.files || [];
    const selCount = files.filter((f) => T.sel.has(`${it.id}:${f.id}`)).length;
    const all = files.length && selCount === files.length;
    const open = T.open.has(it.id);
    const pct = Math.round(it.progress * 100);
    const chip = it.ready ? `<span class="chip ok">bereit</span>` : `<span class="chip warn">${esc(it.state)} ${pct}%</span>`;
    return `<li class="${selCount ? "sel" : ""}">
        <input type="checkbox" class="cb" ${all ? "checked" : ""} ${it.ready && files.length ? "" : "disabled"} data-action="tb-item" data-id="${it.id}" aria-label="Alle Dateien wählen">
        <div class="grow stack clickable" style="gap:5px" data-action="tb-open" data-id="${it.id}">
          <div class="ellipsis"><b>${esc(it.name)}</b></div>
          <div class="row wrap small muted">${chip}<span>${fmtBytes(it.size)}</span><span>${files.length} Datei(en)</span>${selCount ? `<span class="chip run">${selCount} gewählt</span>` : ""}</div>
          ${!it.ready ? `<div class="bar"><div style="width:${pct}%"></div></div>` : ""}
        </div>
        ${files.length ? `<button class="icon-btn" data-action="tb-open" data-id="${it.id}" aria-label="Dateien">${icon(open ? "chevronDown" : "chevron")}</button>` : ""}
      </li>
      ${open ? `<li class="tb-files" style="display:block;padding:0"><ul class="list">${files.map((f) => {
        const key = `${it.id}:${f.id}`;
        return `<li class="clickable ${T.sel.has(key) ? "sel" : ""}" data-action="tb-file" data-key="${key}">
          <input type="checkbox" class="cb" ${T.sel.has(key) ? "checked" : ""} ${it.ready ? "" : "disabled"} data-action="tb-file" data-key="${key}">
          <div class="grow"><div class="ellipsis small">${esc(f.short_name)}</div><div class="meta">${fmtBytes(f.size)}</div></div></li>`;
      }).join("")}</ul></li>` : ""}`;
  }).join("");
  const n = T.sel.size;
  return seg + add + destCard("torbox", "Speichern unter") + `
    <div class="card flush">
      <div style="padding:10px 16px;border-bottom:1px solid var(--line)"><input type="search" placeholder="Suchen…" value="${esc(T.filter)}" data-input="tb-filter"></div>
      ${T.error ? `<div class="empty error">${esc(T.error)}</div>` : T.loading && !T.items.length ? `<div class="empty">Lade…</div>` : rows ? `<ul class="list">${rows}</ul>` : `<div class="empty">Keine Einträge</div>`}
    </div>
    <div class="actionbar">
      <div class="grow small"><b>${n}</b> Datei(en) · ${fmtBytes(selectedTorboxSize())}${n ? ` <button class="btn ghost sm" data-action="tb-clear">zurücksetzen</button>` : ""}</div>
      <button class="btn primary" data-action="tb-download" ${n ? "" : "disabled"}>${icon("download")} Laden</button>
    </div>`;
}

function selectedTorboxSize() {
  let s = 0;
  for (const v of S.torbox.sel.values()) s += v.size || 0;
  return s;
}

let tbTimer = null;
async function loadTorbox() {
  clearTimeout(tbTimer);
  if (!S.status.torbox) return;
  const T = S.torbox;
  T.loading = true;
  if (S.view === "torbox") render();
  try {
    T.items = await api(`/torbox/${T.kind}`);
    T.error = "";
  } catch (e) { T.error = e.message; }
  T.loading = false;
  if (S.view === "torbox") {
    render();
    tbTimer = setTimeout(() => { if (S.view === "torbox" && !document.hidden) loadTorbox(); }, 20000);
  }
}

async function torboxDownload() {
  const T = S.torbox;
  const d = S.dest.torbox || { remote: "", path: "" };
  const files = [...T.sel.values()].map((v) => ({ item_id: v.item_id, file_id: v.file_id, name: v.name }));
  try {
    const r = await api("/torbox/download", { body: { kind: T.kind, files, remote: d.remote, path: d.path } });
    toast(`${r.jobs.length} Download(s) gestartet`, "ok");
    T.sel.clear();
    pollJobs(true);
    render();
  } catch (e) { toast(e.message, "err"); }
}

// ------------------------------------------------------------------ Ansicht: Aufträge
const STATUS = { queued: ["wartet", ""], running: ["läuft", "run"], done: ["fertig", "ok"], failed: ["Fehler", "err"], canceled: ["abgebrochen", "warn"] };
function viewJobs() {
  if (!S.jobs.length) return `<div class="card empty">${icon("list")}<br>Noch keine Aufträge.</div>`;
  return S.jobs.map((j) => {
    const [label, cls] = STATUS[j.status] || [j.status, ""];
    const pct = Math.round((j.progress || 0) * 100);
    const indet = j.status === "running" && !j.total;
    return `<div class="card job">
      <div class="top">
        <div class="ico" style="width:36px;height:36px;border-radius:10px;display:grid;place-items:center;background:var(--card-2);color:var(--muted)">${icon(j.kind === "torbox" ? "bolt" : "upload")}</div>
        <div class="grow"><div class="ellipsis"><b>${esc(j.title)}</b></div>
          <div class="route"><span>${esc(j.source_label)}</span>${icon("arrow")}<span class="ellipsis">${esc(j.dest_label)}</span></div></div>
        <span class="chip ${cls}">${label}${j.status === "running" && j.total ? ` ${pct}%` : ""}</span>
      </div>
      ${j.status === "running" || j.status === "queued" ? `<div class="bar ${indet ? "indet" : ""}"><div style="width:${pct}%"></div></div>` : ""}
      ${j.error ? `<div class="err">${esc(j.error)}</div>` : ""}
      <div class="nums" style="align-items:center">
        <span class="grow ellipsis">${j.total ? `${fmtBytes(j.bytes)} / ${fmtBytes(j.total)}` : j.bytes ? fmtBytes(j.bytes) : ""}${j.current && j.status === "running" ? ` · ${esc(j.current)}` : ""}</span>
        <span>${j.status === "running" && j.speed ? `${fmtBytes(j.speed)}/s${j.eta != null ? ` · ${fmtEta(j.eta)}` : ""}` : j.finished ? new Date(j.finished * 1000).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : ""}</span>
        ${j.status === "running" || j.status === "queued" ? `<button class="btn sm danger" data-action="job-cancel" data-id="${j.id}">${icon("x")} Abbrechen</button>` : ""}
        ${j.status === "failed" || j.status === "canceled" ? `<button class="btn sm" data-action="job-retry" data-id="${j.id}">${icon("retry")} Erneut</button>` : ""}
        ${j.status !== "running" && j.status !== "queued" ? `<button class="icon-btn" style="width:32px;height:32px" data-action="job-remove" data-id="${j.id}" aria-label="Entfernen">${icon("trash")}</button>` : ""}
      </div>
    </div>`;
  }).join("");
}

let jobTimer = null;
let lastActive = 0;
async function pollJobs(force = false) {
  clearTimeout(jobTimer);
  try {
    S.jobs = await api("/jobs");
    const active = S.jobs.filter((j) => j.status === "running" || j.status === "queued").length;
    const badge = $("#jobBadge");
    badge.hidden = !active;
    badge.textContent = active;
    if (lastActive && active < lastActive) {
      const done = S.jobs.filter((j) => j.finished && Date.now() / 1000 - j.finished < 4);
      done.forEach((j) => toast(`${j.status === "done" ? "Fertig" : "Fehlgeschlagen"}: ${j.title}`, j.status === "done" ? "ok" : "err"));
    }
    lastActive = active;
    if (S.view === "jobs") render();
    jobTimer = setTimeout(pollJobs, active ? 1500 : 8000);
  } catch {
    jobTimer = setTimeout(pollJobs, 10000);
  }
  if (force && S.view !== "jobs") { /* Badge reicht */ }
}

// ------------------------------------------------------------------ Ansicht: Clouds & Einstellungen
function viewClouds() {
  const cards = S.remotes.map((r) => {
    const a = S.about[r.name];
    let quota = "";
    if (a && a.total) {
      const pct = Math.min(100, Math.round(((a.used || 0) / a.total) * 100));
      quota = `<div class="quota"><div class="bar"><div style="width:${pct}%"></div></div><div class="small muted">${fmtBytes(a.used)} von ${fmtBytes(a.total)} belegt · ${fmtBytes(a.free)} frei</div></div>`;
    } else if (a && a.used != null) quota = `<div class="small muted" style="margin-top:8px">${fmtBytes(a.used)} belegt</div>`;
    else if (a && a.error) quota = `<div class="small error" style="margin-top:8px">${esc(a.error)}</div>`;
    return `<div class="card"><div class="dest">${logo(r.type)}
        <div class="grow"><div class="val">${esc(r.name)}</div><div class="small muted">${esc(typeInfo(r.type).label)}</div></div>
        <button class="icon-btn" data-action="remote-delete" data-name="${esc(r.name)}" aria-label="Entfernen">${icon("trash")}</button></div>${quota}</div>`;
  }).join("");
  return `${S.status.auth === false ? `<div class="banner">⚠️ Kein <code>APP_PASSWORD</code> gesetzt – jeder im Netzwerk kann die App bedienen.</div>` : ""}
    <button class="btn primary block" data-action="connect">${icon("plus")} Cloud verbinden</button>
    ${cards || `<div class="card empty">${icon("cloud")}<br>Noch keine Cloud verbunden.</div>`}
    <div class="card stack" id="settings"><h3>${icon("gear")} Einstellungen</h3><div class="muted small">Lade…</div></div>
    <p class="small muted" style="text-align:center">CloudUpper ${esc(S.status.version || "")} · rclone ${esc(S.status.rclone || "")}</p>`;
}

async function loadAbout() {
  renderSettings();
  for (const r of S.remotes) {
    if (S.about[r.name]) continue;
    api(`/remotes/${encodeURIComponent(r.name)}/about`).then((a) => { S.about[r.name] = a; if (S.view === "clouds") { render(); renderSettings(); } }).catch(() => {});
  }
}

let settingsCache = null;
let providersCache = null;
async function renderSettings() {
  try {
    [settingsCache, providersCache] = await Promise.all([api("/settings"), api("/providers")]);
  } catch (e) { return; }
  const el = $("#settings");
  if (!el) return;
  const s = settingsCache;
  el.innerHTML = `<h3>${icon("gear")} Einstellungen</h3>
    <label class="field">TorBox API-Key ${s.torbox_from_env ? "(aus Umgebungsvariable)" : ""}
      <input type="password" id="setTorbox" placeholder="nicht gesetzt" value="${esc(s.torbox_api_key)}" ${s.torbox_from_env ? "disabled" : ""}></label>
    <details><summary>Eigene OAuth-Apps (für „Mit … anmelden“)</summary><div class="stack">
      <p class="small muted" style="margin:0">Trage bei der App des Anbieters diese Weiterleitungs-URI ein:</p>
      <div class="row"><code class="grow mono">${esc(providersCache.redirect_uri)}</code><button class="icon-btn" data-action="copy" data-text="${esc(providersCache.redirect_uri)}">${icon("copy")}</button></div>
      ${providersCache.providers.map((p) => `<div class="stack" style="gap:6px"><b>${esc(p.label)}</b> <a class="small" href="${esc(p.console)}" target="_blank" rel="noopener">Entwicklerkonsole öffnen ↗</a>
        <input type="text" placeholder="Client-ID" data-oauth="${p.id}" data-field="client_id" value="${esc(s.oauth[p.id].client_id)}" ${s.oauth[p.id].from_env ? "disabled" : ""}>
        <input type="password" placeholder="Client-Secret" data-oauth="${p.id}" data-field="client_secret" value="${esc(s.oauth[p.id].client_secret)}" ${s.oauth[p.id].from_env ? "disabled" : ""}></div>`).join("")}
    </div></details>
    <button class="btn" data-action="settings-save">Speichern</button>`;
}

async function saveSettings() {
  const body = { oauth: {} };
  const tb = $("#setTorbox");
  if (tb && !tb.disabled) body.torbox_api_key = tb.value;
  document.querySelectorAll("[data-oauth]").forEach((inp) => {
    if (inp.disabled) return;
    (body.oauth[inp.dataset.oauth] ||= {})[inp.dataset.field] = inp.value;
  });
  try {
    await api("/settings", { method: "PUT", body });
    S.status = await api("/status");
    toast("Gespeichert", "ok");
    renderSettings();
  } catch (e) { toast(e.message, "err"); }
}

// ---------------------------------------------- Cloud verbinden
const GENERIC = {
  webdav: { label: "WebDAV / Nextcloud", fields: [["url", "URL (z.B. https://cloud.example.de/remote.php/dav/files/USER)"], ["vendor", "Anbieter (nextcloud, owncloud, sharepoint, other)", "nextcloud"], ["user", "Benutzer"], ["pass", "Passwort / App-Passwort", "", "password"]] },
  sftp: { label: "SFTP / NAS", fields: [["host", "Host"], ["port", "Port", "22"], ["user", "Benutzer"], ["pass", "Passwort", "", "password"]] },
  s3: { label: "S3-kompatibel", fields: [["provider", "Anbieter (AWS, Cloudflare, Wasabi, Minio, Other)", "Other"], ["access_key_id", "Access Key ID"], ["secret_access_key", "Secret Access Key", "", "password"], ["region", "Region", ""], ["endpoint", "Endpoint", ""]] },
};

async function openConnect() {
  const prov = providersCache || await api("/providers");
  providersCache = prov;
  openSheet("Cloud verbinden", `<div class="tiles">
    ${prov.providers.map((p) => `<button class="tile" data-action="connect-oauth" data-id="${p.id}">${logo(p.id)}${esc(p.label)}</button>`).join("")}
    ${Object.entries(GENERIC).map(([k, g]) => `<button class="tile" data-action="connect-generic" data-id="${k}">${logo(k)}${esc(g.label)}</button>`).join("")}
    <button class="tile" data-action="connect-generic" data-id="other">${logo("other")}Anderer rclone-Typ</button>
  </div>`);
}

function suggestName(base) {
  let n = base, i = 2;
  while (S.remotes.some((r) => r.name === n)) n = `${base}${i++}`;
  return n;
}

function connectOAuth(id) {
  const p = providersCache.providers.find((x) => x.id === id);
  openSheet(p.label, `
    <label class="field">Name der Verbindung<input type="text" id="cName" value="${esc(suggestName(id === "drive" ? "gdrive" : id))}" autocapitalize="off"></label>
    ${p.oauth_ready
      ? `<button class="btn primary block" data-action="oauth-start" data-id="${id}">${icon("link")} Mit ${esc(p.label)} anmelden</button>`
      : `<div class="banner small">Für die direkte Anmeldung wird eine eigene OAuth-App benötigt (Einstellungen → Eigene OAuth-Apps). Alternativ geht es ohne eigene App per Token:</div>`}
    <details ${p.oauth_ready ? "" : "open"}><summary>${icon("key")} Mit Token verbinden</summary><div class="stack">
      <ol class="small muted" style="margin:0;padding-left:18px">
        <li>Auf einem Rechner mit Browser <a href="https://rclone.org/downloads/" target="_blank" rel="noopener">rclone installieren</a>.</li>
        <li>Ausführen: <code>${esc(p.authorize_cmd)}</code> <button class="btn ghost sm" data-action="copy" data-text="${esc(p.authorize_cmd)}">${icon("copy")}</button></li>
        <li>Im Browser anmelden und die ausgegebene Zeile <code>{"access_token":…}</code> hier einfügen.</li>
      </ol>
      <textarea id="cToken" placeholder='{"access_token":"…","token_type":"Bearer","refresh_token":"…","expiry":"…"}'></textarea>
      <button class="btn block" data-action="token-save" data-id="${id}">Verbinden</button>
    </div></details>`);
}

function connectGeneric(id) {
  const g = GENERIC[id];
  const fields = g ? g.fields.map(([k, label, def = "", type = "text"]) =>
    `<label class="field">${esc(label)}<input type="${type}" data-gp="${k}" value="${esc(def)}" autocapitalize="off" autocorrect="off"></label>`).join("")
    : `<label class="field">rclone-Typ (z.B. pcloud, mega, box, ftp, smb)<input type="text" id="gType" autocapitalize="off"></label>
       <label class="field">Parameter (eine Zeile pro <code>schlüssel=wert</code>)<textarea id="gParams" placeholder="user=ich\npass=geheim"></textarea></label>
       <p class="small muted" style="margin:0">Alle Optionen: <a href="https://rclone.org/overview/" target="_blank" rel="noopener">rclone.org/overview</a></p>`;
  openSheet(g ? g.label : "Anderer rclone-Typ", `
    <label class="field">Name der Verbindung<input type="text" id="cName" value="${esc(suggestName(id === "other" ? "cloud" : id))}" autocapitalize="off"></label>
    ${fields}
    <button class="btn primary block" data-action="generic-save" data-id="${id}">Verbinden</button>`);
}

async function afterConnect(msg) {
  closeSheet();
  toast(msg, "ok");
  S.remotes = await api("/remotes");
  go("clouds");
}

// ------------------------------------------------------------------ Sheet
function openSheet(title, html) {
  $("#sheetTitle").textContent = title;
  $("#sheetBody").innerHTML = html;
  $("#sheet").hidden = false;
  document.body.style.overflow = "hidden";
}
function closeSheet() {
  $("#sheet").hidden = true;
  document.body.style.overflow = "";
}

// ------------------------------------------------------------------ Login
function showLogin() {
  $("#login").hidden = false;
  setTimeout(() => $("#loginForm input").focus(), 50);
}
$("#loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#loginError").textContent = "";
  try {
    await api("/login", { body: { password: e.target.password.value } });
    $("#login").hidden = true;
    e.target.reset();
    boot();
  } catch (err) { $("#loginError").textContent = err.message; }
});

// ------------------------------------------------------------------ Events
const actions = {
  "nav": (el) => go(el.dataset.view),
  "upload-mode": (el) => { S.uploadMode = el.dataset.mode; store.set("uploadMode", S.uploadMode); render(); if (S.uploadMode === "server") loadLocal(); },
  "local-cd": (el) => { S.local.path = el.dataset.path; S.local.filter = ""; loadLocal(); },
  "local-toggle": (el) => { const p = el.dataset.path; S.local.sel.has(p) ? S.local.sel.delete(p) : S.local.sel.add(p); render(); },
  "local-all": () => {
    const L = S.local; const q = L.filter.toLowerCase();
    const paths = L.entries.filter((e) => !q || e.name.toLowerCase().includes(q)).map((e) => joinPath(L.path, e.name));
    const all = paths.every((p) => L.sel.has(p));
    paths.forEach((p) => (all ? L.sel.delete(p) : L.sel.add(p)));
    render();
  },
  "local-clear": () => { S.local.sel.clear(); render(); },
  "local-refresh": () => loadLocal(),
  "toggle-move": (el) => { S.move = el.checked; },
  "upload-server": () => uploadServer(),
  "dev-remove": (el) => { S.device.queue.splice(+el.dataset.i, 1); render(); },
  "dev-clear": () => { S.device.queue = S.device.queue.filter((f) => f.state !== "done"); render(); },
  "dev-start": () => startDeviceUploads(),
  "pick-dest": (el) => openPicker(el.dataset.ctx),
  "pk-remote": (el) => { picker.remote = el.dataset.remote; picker.path = ""; loadPicker(); },
  "pk-cd": (el) => { picker.path = el.dataset.path; loadPicker(); },
  "pk-recent": (el) => chooseDest(S.recent.filter((d) => !d.remote || S.remotes.some((r) => r.name === d.remote))[+el.dataset.i]),
  "pk-choose": () => chooseDest({ remote: picker.remote, path: picker.path }),
  "pk-mkdir": async () => {
    const name = $("#pkNew").value.trim().replace(/\//g, "-");
    if (!name) return;
    try {
      await api("/mkdir", { body: { remote: picker.remote, path: joinPath(picker.path, name) } });
      picker.path = joinPath(picker.path, name);
      loadPicker();
    } catch (e) { toast(e.message, "err"); }
  },
  "sheet-close": () => closeSheet(),
  "tb-kind": (el) => { S.torbox.kind = el.dataset.kind; S.torbox.items = []; S.torbox.sel.clear(); S.torbox.open.clear(); loadTorbox(); },
  "tb-refresh": () => loadTorbox(),
  "tb-open": (el) => { const id = +el.dataset.id; S.torbox.open.has(id) ? S.torbox.open.delete(id) : S.torbox.open.add(id); render(); },
  "tb-item": (el) => {
    const it = S.torbox.items.find((i) => i.id === +el.dataset.id);
    if (!it) return;
    const keys = it.files.map((f) => `${it.id}:${f.id}`);
    const all = keys.every((k) => S.torbox.sel.has(k));
    it.files.forEach((f) => {
      const k = `${it.id}:${f.id}`;
      if (all) S.torbox.sel.delete(k);
      else S.torbox.sel.set(k, { item_id: it.id, file_id: f.id, name: f.name, size: f.size });
    });
    render();
  },
  "tb-file": (el) => {
    const k = el.dataset.key;
    if (S.torbox.sel.has(k)) { S.torbox.sel.delete(k); render(); return; }
    const [iid, fid] = k.split(":").map(Number);
    const it = S.torbox.items.find((i) => i.id === iid);
    const f = it?.files.find((x) => x.id === fid);
    if (!f || !it.ready) return;
    S.torbox.sel.set(k, { item_id: iid, file_id: fid, name: f.name, size: f.size });
    render();
  },
  "tb-clear": () => { S.torbox.sel.clear(); render(); },
  "tb-download": () => torboxDownload(),
  "tb-add": async () => {
    const v = $("#tbAdd").value.trim();
    if (!v) return;
    try {
      const r = await api("/torbox/add", { body: { type: S.torbox.kind === "torrents" ? "magnet" : "link", value: v } });
      toast(r.detail || "Hinzugefügt", "ok");
      loadTorbox();
    } catch (e) { toast(e.message, "err"); }
  },
  "tb-savekey": async () => {
    try {
      await api("/settings", { method: "PUT", body: { torbox_api_key: $("#tbKey").value } });
      S.status = await api("/status");
      loadTorbox();
      render();
    } catch (e) { toast(e.message, "err"); }
  },
  "job-cancel": async (el) => { await api(`/jobs/${el.dataset.id}/cancel`, { method: "POST" }).catch((e) => toast(e.message, "err")); pollJobs(); },
  "job-retry": async (el) => { await api(`/jobs/${el.dataset.id}/retry`, { method: "POST" }).catch((e) => toast(e.message, "err")); pollJobs(); },
  "job-remove": async (el) => { await api(`/jobs/${el.dataset.id}`, { method: "DELETE" }).catch((e) => toast(e.message, "err")); pollJobs(); },
  "jobs-clear": async () => { await api("/jobs/clear", { method: "POST" }); pollJobs(); },
  "connect": () => openConnect(),
  "connect-oauth": (el) => connectOAuth(el.dataset.id),
  "connect-generic": (el) => connectGeneric(el.dataset.id),
  "oauth-start": async (el) => {
    try {
      const r = await api(`/oauth/${el.dataset.id}/start?name=${encodeURIComponent($("#cName").value.trim())}`);
      location.href = r.url;
    } catch (e) { toast(e.message, "err"); }
  },
  "token-save": async (el) => {
    try {
      await api("/remotes/token", { body: { name: $("#cName").value.trim(), provider: el.dataset.id, token: $("#cToken").value } });
      afterConnect("Verbunden");
    } catch (e) { toast(e.message, "err"); }
  },
  "generic-save": async (el) => {
    const id = el.dataset.id;
    const params = {};
    let type = id;
    if (id === "other") {
      type = $("#gType").value.trim();
      $("#gParams").value.split("\n").forEach((line) => {
        const i = line.indexOf("=");
        if (i > 0) params[line.slice(0, i).trim()] = line.slice(i + 1).trim();
      });
    } else {
      document.querySelectorAll("[data-gp]").forEach((inp) => { if (inp.value.trim()) params[inp.dataset.gp] = inp.value.trim(); });
    }
    try {
      await api("/remotes/generic", { body: { name: $("#cName").value.trim(), type, params } });
      afterConnect("Verbunden");
    } catch (e) { toast(e.message, "err"); }
  },
  "remote-delete": async (el) => {
    if (!confirm(`Verbindung „${el.dataset.name}“ entfernen? (Dateien in der Cloud bleiben erhalten)`)) return;
    await api(`/remotes/${encodeURIComponent(el.dataset.name)}`, { method: "DELETE" }).catch((e) => toast(e.message, "err"));
    S.remotes = await api("/remotes");
    render(); renderSettings();
  },
  "settings-save": () => saveSettings(),
  "copy": async (el) => { try { await navigator.clipboard.writeText(el.dataset.text); toast("Kopiert"); } catch { toast(el.dataset.text); } },
  "logout": async () => { await api("/logout", { method: "POST" }); location.reload(); },
};

document.addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (tab) { go(tab.dataset.view); return; }
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const a = el.dataset.action;
  if (a === "toggle-move") { actions[a](el); return; }
  if (el.tagName === "A") e.preventDefault();
  // Checkbox in klickbarer Zeile: nur einmal auslösen
  if (el.classList.contains("cb")) e.stopPropagation();
  if (el.tagName === "INPUT" && el.type === "checkbox") e.preventDefault();
  if (actions[a]) actions[a](el, e);
});

document.addEventListener("input", (e) => {
  const k = e.target.dataset?.input;
  if (k === "local-filter" || k === "tb-filter") {
    const pos = e.target.selectionStart;
    if (k === "local-filter") S.local.filter = e.target.value; else S.torbox.filter = e.target.value;
    render();
    const inp = $(`[data-input="${k}"]`);
    inp.focus(); inp.setSelectionRange(pos, pos);
  }
});
document.addEventListener("change", (e) => {
  if (e.target.dataset?.input === "dev-files") { addDeviceFiles(e.target.files); e.target.value = ""; }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeSheet();
  if (e.key !== "Enter") return;
  if (e.target.id === "tbAdd") actions["tb-add"]();
  if (e.target.id === "pkNew") actions["pk-mkdir"]();
});
document.addEventListener("dragover", (e) => { const d = e.target.closest?.("#drop"); if (d) { e.preventDefault(); d.classList.add("over"); } });
document.addEventListener("dragleave", (e) => { e.target.closest?.("#drop")?.classList.remove("over"); });
document.addEventListener("drop", (e) => {
  const d = e.target.closest?.("#drop");
  if (!d) return;
  e.preventDefault();
  addDeviceFiles(e.dataTransfer.files);
});
document.addEventListener("visibilitychange", () => { if (!document.hidden) pollJobs(); });
window.addEventListener("hashchange", () => {
  const v = location.hash.slice(1).split("?")[0];
  if (TITLES[v] && v !== S.view) go(v);
});

// ------------------------------------------------------------------ Start
async function boot() {
  const sess = await api("/session").catch(() => ({ authenticated: true }));
  if (!sess.authenticated) { showLogin(); return; }
  [S.status, S.remotes] = await Promise.all([api("/status"), api("/remotes")]);
  if (!S.dest.upload && S.remotes.length) S.dest.upload = { remote: S.remotes[0].name, path: "" };
  // Rückmeldung aus OAuth-Callback (#clouds?ok=… / #clouds?error=…)
  const [view, query] = location.hash.slice(1).split("?");
  if (query) {
    const p = new URLSearchParams(query);
    if (p.get("ok")) toast(p.get("ok"), "ok");
    if (p.get("error")) toast(p.get("error"), "err");
  }
  go(TITLES[view] ? view : (S.remotes.length ? "upload" : "clouds"));
  pollJobs();
}

hydrateIcons();
boot();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
