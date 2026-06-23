"use strict";

// Vanilla, no build step. Talks to the FastAPI server on the same origin.

const state = {
  meta: null,
  sel: { task: "ideas", scope: "import", artifacts: new Set(["hub"]) },
  open: new Set(), // expanded job ids
};

const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.status === 204 ? null : res.json();
}

// --- core elicitation (rendered from /api/meta) ---------------------------

function renderCore() {
  const host = $("coreQuestions");
  host.innerHTML = "";
  for (const q of state.meta.core_questions) {
    const group = document.createElement("div");
    group.className = "qgroup";
    group.innerHTML = `<p class="qtext">${q.text}</p>`;
    const chips = document.createElement("div");
    chips.className = "chips";
    for (const opt of q.options) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.innerHTML = opt.note
        ? `${opt.label}<span class="chip-note">${opt.note}</span>`
        : opt.label;
      chip.setAttribute("aria-pressed", String(isSelected(q.id, opt.value)));
      chip.onclick = () => toggle(q.id, opt.value, q.kind);
      chips.appendChild(chip);
    }
    group.appendChild(chips);
    host.appendChild(group);
  }
}

function isSelected(qid, value) {
  if (qid === "artifacts") return state.sel.artifacts.has(value);
  return state.sel[qid] === value;
}

function toggle(qid, value, kind) {
  if (qid === "artifacts") {
    const set = state.sel.artifacts;
    if (set.has(value)) { if (value !== "hub") set.delete(value); }
    else set.add(value);
  } else {
    state.sel[qid] = value;
  }
  renderCore();
  renderPrivacy();
}

// --- privacy banner: honest about when content leaves the device ----------

function renderPrivacy() {
  const el = $("privacy");
  const { scope } = state.sel;
  const { routing, claude_available } = state.meta;
  const claudeActive = routing === "force_claude" || (routing === "auto" && claude_available);
  let cls = "on-device", msg = "Stays on this device — local model only.";
  if (scope === "import_web") {
    cls = "leaves"; msg = "Web scope — content leaves the device.";
  } else if (routing === "force_claude") {
    cls = "leaves"; msg = "Forced Claude — content is sent to Anthropic.";
  } else if (scope === "import_model" && claudeActive) {
    cls = "leaves"; msg = "Model knowledge via Claude — content may leave the device.";
  } else if (scope === "import" && claudeActive) {
    cls = "on-device"; msg = "On-device by default; Claude only as a low-confidence fallback.";
  }
  el.className = `privacy ${cls}`;
  el.textContent = (cls === "leaves" ? "⚠ " : "● ") + msg;
}

// --- submit ----------------------------------------------------------------

async function submit() {
  const btn = $("submit");
  const err = $("composeError");
  err.hidden = true;
  const text = $("content").value.trim();
  const sourcePath = $("sourcePath").value.trim();
  if (!text && !sourcePath) {
    err.textContent = "Paste some content or give a file path.";
    err.hidden = false;
    return;
  }
  const countVal = $("count").value;
  const body = {
    raw_request: $("request").value.trim(),
    task: state.sel.task,
    scope: state.sel.scope,
    artifacts: [...state.sel.artifacts],
    count: countVal ? Number(countVal) : null,
    audience: $("audience").value.trim() || null,
    text: text || null,
    source_path: sourcePath || null,
  };
  btn.disabled = true; btn.textContent = "Queuing…";
  try {
    await api("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    $("content").value = "";
    $("sourcePath").value = "";
    await refreshJobs();
  } catch (e) {
    err.textContent = e.message; err.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = "Run pipeline";
  }
}

// --- runs list -------------------------------------------------------------

function artifactLink(path) {
  const name = path.split("/").pop();
  return `<a href="/api/jobs/_/artifact?path=${encodeURIComponent(path)}" target="_blank">${name}</a>`;
}

function renderDetail(job) {
  if (job.status === "needs_input") {
    const qs = (job.followups || []).map((q) => {
      const opts = (q.options || []).map((o) =>
        `<button type="button" class="chip" data-q="${q.id}" data-v="${o}">${o}</button>`
      ).join("");
      const input = q.kind === "text"
        ? `<input data-q="${q.id}" placeholder="Your answer" />`
        : `<div class="chips">${opts}</div>`;
      return `<div class="followup"><p class="qtext">${q.text}</p>${input}</div>`;
    }).join("");
    return `${qs}<button class="primary" data-answer="${job.id}">Submit answers</button>`;
  }
  const r = job.result || {};
  if (r.error) return `<span class="error">${r.error}</span>`;
  const links = [r.hub_note_path, ...(r.artifact_paths || [])]
    .filter((p, i, a) => p && a.indexOf(p) === i)
    .map((p) => `<li>${artifactLink(p)}</li>`).join("");
  const caveat = r.shipped_with_caveat ? `<p class="muted">shipped with a caveat</p>` : "";
  const trace = r.trace_path ? `<li>${artifactLink(r.trace_path)}</li>` : "";
  return links || trace
    ? `${caveat}<ul>${links}${trace}</ul>`
    : `<span class="muted">no artifacts</span>`;
}

function wireDetail(li, job) {
  const picks = {};
  li.querySelectorAll(".chip[data-q]").forEach((chip) => {
    chip.onclick = () => {
      const q = chip.dataset.q;
      li.querySelectorAll(`.chip[data-q="${q}"]`).forEach((c) =>
        c.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      picks[q] = chip.dataset.v;
    };
  });
  const ansBtn = li.querySelector("[data-answer]");
  if (ansBtn) {
    ansBtn.onclick = async () => {
      li.querySelectorAll("input[data-q]").forEach((inp) => {
        if (inp.value.trim()) picks[inp.dataset.q] = inp.value.trim();
      });
      ansBtn.disabled = true;
      try {
        await api(`/api/jobs/${job.id}/answers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers: picks }),
        });
        await refreshJobs();
      } finally { ansBtn.disabled = false; }
    };
  }
}

function renderJobs(jobs) {
  const ul = $("jobs");
  $("jobsEmpty").hidden = jobs.length > 0;
  ul.innerHTML = "";
  for (const job of jobs) {
    const li = document.createElement("li");
    li.className = "job";
    const expanded = state.open.has(job.id);
    li.innerHTML = `
      <div class="job-head">
        <div>
          <div class="job-req">${job.raw_request || "(untitled run)"}</div>
          <div class="job-meta">${job.task || ""} · ${job.scope || ""} · ${job.id}</div>
        </div>
        <span class="badge ${job.status}">${job.status.replace("_", " ")}</span>
      </div>`;
    li.querySelector(".job-head").onclick = () => {
      if (state.open.has(job.id)) state.open.delete(job.id);
      else state.open.add(job.id);
      refreshJobs();
    };
    if (expanded) {
      const detail = document.createElement("div");
      detail.className = "job-detail";
      detail.innerHTML = renderDetail(job);
      li.appendChild(detail);
      wireDetail(li, job);
    }
    ul.appendChild(li);
  }
}

async function refreshJobs() {
  try {
    renderJobs(await api("/api/jobs"));
  } catch (e) { /* transient; next poll retries */ }
}

// --- boot ------------------------------------------------------------------

async function boot() {
  state.meta = await api("/api/meta");
  $("llmState").textContent = `${state.meta.llm_name} · ${state.meta.routing}`;
  renderCore();
  renderPrivacy();
  $("submit").onclick = submit;
  await refreshJobs();
  setInterval(refreshJobs, 1500);
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

boot();
