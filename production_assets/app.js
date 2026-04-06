const STORAGE_KEY = "perfectLibraryCurrentJobId";

const state = {
  library: null,
  currentJob: null,
  pollTimer: null,
  busy: false,
};

const elements = {
  generateButton: document.getElementById("generate-button"),
  statusText: document.getElementById("status-text"),
  libraryItem: document.getElementById("library_item_id"),
  language: document.getElementById("language"),
  topic: document.getElementById("topic"),
  ctaText: document.getElementById("cta_text"),
  script: document.getElementById("script"),
  notes: document.getElementById("notes"),
  jobTitle: document.getElementById("job-title"),
  jobMeta: document.getElementById("job-meta"),
  jobCopy: document.getElementById("job-copy"),
  linkRow: document.getElementById("link-row"),
  visualStatus: document.getElementById("visual-status"),
  warningsPanel: document.getElementById("warnings-panel"),
  downloadsPanel: document.getElementById("downloads-panel"),
  imageQueriesPanel: document.getElementById("image-queries-panel"),
  copyScriptButton: document.getElementById("copy-script-button"),
  downloadScriptButton: document.getElementById("download-script-button"),
  usedScriptOutput: document.getElementById("used-script-output"),
};

init();

async function init() {
  bindEvents();
  try {
    const library = await requestJson("/api/perfect-library");
    state.library = library;
    populateLibrary(library.entries || []);
    setStatus("Perfect library loaded. Generate one production carousel when ready.");

    const savedJobId = window.localStorage.getItem(STORAGE_KEY);
    if (savedJobId) {
      try {
        const job = await requestJson(`/api/production-jobs/${encodeURIComponent(savedJobId)}`);
        applyJob(job);
      } catch (error) {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    } else {
      renderEmptyJob();
    }
  } catch (error) {
    renderEmptyJob();
    setStatus(error.message || String(error), true);
  }
}

function bindEvents() {
  elements.generateButton.addEventListener("click", onGenerateJob);
  elements.copyScriptButton.addEventListener("click", onCopyScript);
  elements.downloadScriptButton.addEventListener("click", onDownloadScript);
}

function populateLibrary(entries) {
  elements.libraryItem.innerHTML = "";
  entries.forEach((entry, index) => {
    const option = document.createElement("option");
    option.value = entry.library_item_id;
    option.textContent = entry.label;
    elements.libraryItem.appendChild(option);
    if (index === 0) {
      elements.libraryItem.value = entry.library_item_id;
    }
  });
}

async function onGenerateJob() {
  const payload = buildJobPayload();
  if (!payload.topic && !payload.script) {
    setStatus("Add a topic or a script before generating the final carousel.", true);
    return;
  }
  try {
    toggleBusy(true);
    setStatus("Planning copy, resolving visuals, and queuing the production render…");
    const job = await requestJson("/api/production-jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    applyJob(job);
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

function buildJobPayload() {
  return compactObject({
    library_item_id: elements.libraryItem.value,
    topic: cleanInlineValue(elements.topic.value),
    script: cleanMultilineValue(elements.script.value),
    cta_text: cleanInlineValue(elements.ctaText.value),
    language: cleanInlineValue(elements.language.value),
    notes: cleanMultilineValue(elements.notes.value),
  });
}

function applyJob(job) {
  state.currentJob = job;
  window.localStorage.setItem(STORAGE_KEY, job.job_id);
  renderJob(job);
  managePolling(job);
}

function renderEmptyJob() {
  elements.jobTitle.textContent = "No production job yet";
  elements.jobMeta.innerHTML = "";
  elements.jobCopy.textContent = "Choose a perfect-library template and generate one final carousel.";
  elements.linkRow.innerHTML = "";
  elements.visualStatus.textContent = "pending";
  elements.warningsPanel.innerHTML = emptyPanel("No warnings yet.");
  elements.downloadsPanel.innerHTML = emptyPanel("Downloads will appear after the render finishes.");
  elements.imageQueriesPanel.innerHTML = emptyPanel("Resolved image queries will appear here after the visual plan runs.");
  renderUsedScript(null);
}

function renderJob(job) {
  elements.jobTitle.textContent = `${job.library_label}`;
  elements.jobMeta.innerHTML = "";
  elements.jobMeta.appendChild(metaChip(`Status: ${formatStatus(job.status)}`));
  elements.jobMeta.appendChild(metaChip(job.library_item_id));
  if (job.style_recipe) {
    elements.jobMeta.appendChild(metaChip(job.style_recipe));
  }

  const copyParts = [
    job.request?.topic,
    job.request?.script ? "Custom script provided." : null,
    job.request?.language ? `Language: ${job.request.language}` : null,
  ].filter(Boolean);
  elements.jobCopy.textContent = copyParts.join(" ") || "Production job created.";

  elements.linkRow.innerHTML = "";
  if (job.figma_file_url) {
    elements.linkRow.appendChild(linkChip("Open Figma File", job.figma_file_url));
  }
  if (job.figma_page_url) {
    elements.linkRow.appendChild(linkChip("Open Figma Page", job.figma_page_url));
  }

  elements.visualStatus.textContent = job.visual_status || "pending";
  renderWarnings(job);
  renderDownloads(job);
  renderImageQueries(job);
  renderUsedScript(job);
  setStatus(jobStatusMessage(job), job.status === "error");
}

function renderWarnings(job) {
  const warnings = job.warnings || [];
  if (!warnings.length) {
    elements.warningsPanel.innerHTML = emptyPanel("No current warnings. The selected template resolved its visual plan cleanly.");
    return;
  }

  elements.warningsPanel.innerHTML = warnings
    .map((warning) => {
      const slideLabel = warning.slide_number ? `Slide ${warning.slide_number} · ` : "";
      return `
        <article class="warning-card ${warning.severity}">
          <p class="warning-code">${escapeHtml(warning.code)}</p>
          <p class="warning-copy">${escapeHtml(`${slideLabel}${warning.message}`)}</p>
        </article>
      `;
    })
    .join("");
}

function renderDownloads(job) {
  const links = [];
  (job.export_urls || []).forEach((url, index) => {
    links.push(`<a class="download-link" href="${escapeAttribute(url)}" target="_blank" rel="noreferrer">Slide ${index + 1} PNG</a>`);
  });
  if (job.pdf_export_url) {
    links.push(`<a class="download-link" href="${escapeAttribute(job.pdf_export_url)}" target="_blank" rel="noreferrer">Combined PDF</a>`);
  }

  if (!links.length) {
    const copy =
      job.status === "error"
        ? "This job failed before exports were written."
        : "Waiting for the plugin render to finish before showing real downloads.";
    elements.downloadsPanel.innerHTML = emptyPanel(copy);
    return;
  }

  elements.downloadsPanel.innerHTML = `<div class="download-grid">${links.join("")}</div>`;
}

function renderImageQueries(job) {
  const assets = Array.isArray(job.image_assets) ? [...job.image_assets] : [];
  if (!assets.length) {
    const copy =
      job.status === "error"
        ? "No image-query data is available because this job failed before visual resolution finished."
        : "Waiting for visual resolution to capture the image queries used for this carousel.";
    elements.imageQueriesPanel.innerHTML = emptyPanel(copy);
    return;
  }

  assets.sort((left, right) => {
    const slideDelta = Number(left.slide_number || 0) - Number(right.slide_number || 0);
    if (slideDelta !== 0) {
      return slideDelta;
    }
    return String(left.role || "").localeCompare(String(right.role || ""));
  });

  elements.imageQueriesPanel.innerHTML = assets
    .map((asset) => {
      const metaParts = [
        asset.slide_number ? `Slide ${asset.slide_number}` : null,
        asset.role || null,
        asset.provider || null,
      ].filter(Boolean);
      const credit = asset.credit ? `<p class="query-credit">${escapeHtml(asset.credit)}</p>` : "";
      return `
        <article class="query-card">
          <p class="query-meta">${escapeHtml(metaParts.join(" · "))}</p>
          <p class="query-copy">${escapeHtml(asset.query_or_prompt || "No query recorded.")}</p>
          ${credit}
        </article>
      `;
    })
    .join("");
}

function renderUsedScript(job) {
  const scriptText = job?.used_script || "";
  elements.usedScriptOutput.value = scriptText;
  elements.copyScriptButton.disabled = !scriptText;
  elements.downloadScriptButton.disabled = !scriptText;
}

function managePolling(job) {
  stopPolling();
  if (!job || !["planned", "rendering", "planning", "queued"].includes(job.status)) {
    return;
  }
  state.pollTimer = window.setInterval(async () => {
    try {
      const refreshed = await requestJson(`/api/production-jobs/${encodeURIComponent(job.job_id)}`);
      applyJob(refreshed);
      if (!["planned", "rendering", "planning", "queued"].includes(refreshed.status)) {
        stopPolling();
      }
    } catch (error) {
      stopPolling();
      setStatus(error.message || String(error), true);
    }
  }, 2500);
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function toggleBusy(isBusy) {
  state.busy = isBusy;
  elements.generateButton.disabled = isBusy;
}

async function onCopyScript() {
  const scriptText = elements.usedScriptOutput.value;
  if (!scriptText) {
    setStatus("No generated script is available for this job yet.", true);
    return;
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(scriptText);
    } else {
      elements.usedScriptOutput.focus();
      elements.usedScriptOutput.select();
      document.execCommand("copy");
      elements.usedScriptOutput.setSelectionRange(0, 0);
      elements.usedScriptOutput.blur();
    }
    setStatus("Script copied to clipboard.");
  } catch (error) {
    setStatus(error.message || "Could not copy the script.", true);
  }
}

function onDownloadScript() {
  const job = state.currentJob;
  const scriptText = job?.used_script;
  if (!scriptText) {
    setStatus("No generated script is available for this job yet.", true);
    return;
  }

  const blob = new Blob([scriptText], { type: "text/plain;charset=utf-8" });
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = `${job.job_id || "production-job"}-script.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
}

function setStatus(message, isError = false) {
  elements.statusText.textContent = message;
  elements.statusText.parentElement.classList.toggle("error", Boolean(isError));
}

function jobStatusMessage(job) {
  if (!job) {
    return "Ready.";
  }
  if (job.status === "planned" || job.status === "queued" || job.status === "planning") {
    return "Production job created. Waiting for the Figma/plugin render to start.";
  }
  if (job.status === "rendering") {
    return "Render in progress. Downloads will appear as soon as the real exports land.";
  }
  if (job.status === "complete") {
    return "Production render complete. Real downloads are ready.";
  }
  if (job.status === "error") {
    return job.error || "Production render failed.";
  }
  return "Production job updated.";
}

function metaChip(text) {
  const span = document.createElement("span");
  span.className = "meta-chip";
  span.textContent = text;
  return span;
}

function linkChip(label, href) {
  const link = document.createElement("a");
  link.className = "meta-chip link-chip";
  link.href = href;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = label;
  return link;
}

function emptyPanel(copy) {
  return `<p class="empty-copy">${escapeHtml(copy)}</p>`;
}

function cleanInlineValue(value) {
  if (!value) {
    return null;
  }
  const cleaned = String(value).trim().replace(/\s+/g, " ");
  return cleaned || null;
}

function cleanMultilineValue(value) {
  if (!value) {
    return null;
  }
  const cleaned = String(value)
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .trim();
  return cleaned || null;
}

function compactObject(payload) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== null && value !== undefined && value !== ""));
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = describeApiError(payload);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return payload;
}

function describeApiError(payload) {
  if (payload === null || payload === undefined) {
    return "";
  }
  if (typeof payload === "string") {
    return payload;
  }
  if (Array.isArray(payload)) {
    return payload.map((item) => describeApiError(item)).filter(Boolean).join("; ");
  }
  if (typeof payload === "object") {
    if (payload.detail !== undefined) {
      return describeApiError(payload.detail);
    }
    if (payload.error !== undefined) {
      return describeApiError(payload.error);
    }
    if (payload.msg) {
      const location = Array.isArray(payload.loc) ? payload.loc.join(" -> ") : "";
      return location ? `${location}: ${payload.msg}` : String(payload.msg);
    }
    try {
      return JSON.stringify(payload);
    } catch (_error) {
      return String(payload);
    }
  }
  return String(payload);
}

function formatStatus(value) {
  return String(value || "unknown")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}
