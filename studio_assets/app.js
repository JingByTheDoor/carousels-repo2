const state = {
  currentRound: null,
  currentIndex: 0,
};

let refreshTimer = null;

const elements = {
  form: document.getElementById("generate-form"),
  topic: document.getElementById("topic"),
  script: document.getElementById("script"),
  ctaText: document.getElementById("cta_text"),
  notes: document.getElementById("notes"),
  batchMode: document.getElementById("batch_mode"),
  variantCount: document.getElementById("variant_count"),
  preferredStyle: document.getElementById("preferred_style"),
  stylePool: document.getElementById("style_pool"),
  baseCopyLength: document.getElementById("base_copy_length"),
  language: document.getElementById("language"),
  statusText: document.getElementById("status-text"),
  nextRoundButton: document.getElementById("next-round-button"),
  ratingNote: document.getElementById("rating-note"),
  ratingButtons: Array.from(document.querySelectorAll(".rating-button")),
  roundTitle: document.getElementById("round-title"),
  roundMeta: document.getElementById("round-meta"),
  variantTabs: document.getElementById("variant-tabs"),
  variantTitle: document.getElementById("variant-title"),
  variantMeta: document.getElementById("variant-meta"),
  previewGrid: document.getElementById("preview-grid"),
  styleSwatches: document.getElementById("style-swatches"),
  variantPaths: document.getElementById("variant-paths"),
};

async function init() {
  bindEvents();
  try {
    const bootstrap = await requestJson("/api/bootstrap");
    populateSelect(elements.batchMode, bootstrap.batch_modes, "value", "label", "vary_both");
    populateSelect(elements.preferredStyle, bootstrap.style_options, "value", "label", "auto");
    populateSelect(elements.stylePool, bootstrap.style_pools, "value", "label", "all");
    populateSelect(elements.baseCopyLength, bootstrap.copy_length_options, "value", "label", "balanced");

    if (bootstrap.latest_round) {
      applyRound(bootstrap.latest_round);
      setStatus("Loaded the latest review round.");
    } else {
      setStatus("Studio ready. Generate a review round to begin.");
    }
  } catch (error) {
    setStatus(error.message || String(error), true);
  }
}

function bindEvents() {
  elements.form.addEventListener("submit", onGenerateRound);
  elements.nextRoundButton.addEventListener("click", onGenerateNextRound);
  elements.ratingButtons.forEach((button) => {
    button.addEventListener("click", () => onRateVariant(button.dataset.rating));
  });
}

async function onGenerateRound(event) {
  event.preventDefault();
  try {
    setStatus("Generating review round...");
    toggleBusy(true);
    const payload = {
      topic: cleanValue(elements.topic.value),
      script: cleanValue(elements.script.value),
      cta_text: cleanValue(elements.ctaText.value),
      notes: cleanValue(elements.notes.value),
      language: cleanValue(elements.language.value),
      batch_mode: elements.batchMode.value,
      variant_count: Number(elements.variantCount.value || 4),
      preferred_style: elements.preferredStyle.value,
      style_pool: elements.stylePool.value,
      base_copy_length: elements.baseCopyLength.value,
    };
    const round = await requestJson("/api/rounds", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    applyRound(round);
    setStatus("Generated a new review round.");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

async function onGenerateNextRound() {
  if (!state.currentRound) {
    return;
  }
  try {
    setStatus("Generating the next round from your ratings...");
    toggleBusy(true);
    const round = await requestJson(`/api/rounds/${state.currentRound.round_id}/next`, {
      method: "POST",
    });
    applyRound(round);
    setStatus("Generated the next round.");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

async function onRateVariant(rating) {
  const variant = getCurrentVariant();
  if (!variant || !state.currentRound) {
    return;
  }
  try {
    setStatus(`Saving rating: ${rating}...`);
    const round = await requestJson(
      `/api/rounds/${state.currentRound.round_id}/variants/${variant.variant_id}/rating`,
      {
        method: "POST",
        body: JSON.stringify({
          rating,
          note: cleanValue(elements.ratingNote.value),
        }),
      },
    );
    applyRound(round, variant.variant_id);
    setStatus(`Saved rating: ${rating}.`);
  } catch (error) {
    setStatus(error.message || String(error), true);
  }
}

function applyRound(round, preferredVariantId) {
  state.currentRound = round;
  const preferredIndex = round.variants.findIndex((variant) => variant.variant_id === preferredVariantId);
  state.currentIndex = preferredIndex >= 0 ? preferredIndex : 0;

  elements.roundTitle.textContent = `Round ${round.round_number}`;
  elements.roundMeta.innerHTML = "";
  elements.roundMeta.appendChild(metaChip(round.request.batch_mode.replaceAll("_", " ")));
  elements.roundMeta.appendChild(metaChip(`${round.variants.length} variants`));
  elements.roundMeta.appendChild(metaChip(round.request.style_pool));

  renderVariantTabs();
  renderCurrentVariant();
  elements.nextRoundButton.disabled = false;
  startRoundRefresh();
}

function renderVariantTabs() {
  const round = state.currentRound;
  elements.variantTabs.innerHTML = "";
  if (!round) {
    return;
  }
  round.variants.forEach((variant, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `variant-tab ${index === state.currentIndex ? "active" : ""}`;
    button.innerHTML = `
      <strong>Variant ${variant.ordinal}</strong>
      <span class="meta">${variant.requested_style_label} · ${capitalize(variant.copy_length)}</span>
      <span class="meta">Rating: ${capitalize(variant.rating)} · Render: ${capitalize(variant.render_status)}</span>
    `;
    button.addEventListener("click", () => {
      state.currentIndex = index;
      renderVariantTabs();
      renderCurrentVariant();
    });
    elements.variantTabs.appendChild(button);
  });
}

function renderCurrentVariant() {
  const variant = getCurrentVariant();
  elements.previewGrid.innerHTML = "";
  elements.styleSwatches.innerHTML = "";
  elements.variantMeta.innerHTML = "";
  elements.variantPaths.innerHTML = "";

  if (!variant) {
    elements.variantTitle.textContent = "Generate a round to begin";
    toggleRatingButtons(false);
    return;
  }

  elements.variantTitle.textContent = `Variant ${variant.ordinal} · ${variant.requested_style_label}`;
  elements.variantMeta.appendChild(metaChip(`Copy: ${capitalize(variant.copy_length)}`));
  elements.variantMeta.appendChild(metaChip(variant.style_family));
  elements.variantMeta.appendChild(metaChip(variant.style_recipe));
  elements.variantMeta.appendChild(metaChip(`Rating: ${capitalize(variant.rating)}`));
  elements.variantMeta.appendChild(metaChip(`Render: ${capitalize(variant.render_status)}`));
  if (variant.figma_url) {
    const link = document.createElement("a");
    link.className = "meta-chip";
    link.href = variant.figma_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "Open in Figma";
    elements.variantMeta.appendChild(link);
  }

  renderStyleSwatches(variant.payload.style_tokens);
  renderPreviewSlides(variant);
  renderVariantPaths(variant);

  elements.ratingNote.value = variant.rating_note || "";
  toggleRatingButtons(true);
}

function renderStyleSwatches(tokens) {
  const swatchKeys = [
    ["Light", tokens.light_background],
    ["Dark", tokens.dark_background],
    ["Blue", tokens.accent_blue],
    ["Magenta", tokens.accent_magenta],
    ["Gold", tokens.accent_gold],
    ["Orange", tokens.accent_orange],
  ];

  swatchKeys.forEach(([label, color]) => {
    const chip = document.createElement("div");
    chip.className = "swatch";
    chip.innerHTML = `<span class="swatch-dot" style="background:${color}"></span><span>${label}</span>`;
    elements.styleSwatches.appendChild(chip);
  });
}

function renderPreviewSlides(variant) {
  if (variant.preview_image_urls && variant.preview_image_urls.length) {
    renderImagePreviews(variant);
    return;
  }

  const tokens = variant.payload.style_tokens;
  const darkMode = isDark(tokens.dark_background);
  variant.payload.slides.forEach((slide) => {
    const card = document.createElement("article");
    const useDark = slide.slide_role !== "info" ? darkMode : false;
    const background = slide.slide_role !== "info" ? tokens.dark_background : tokens.light_background;
    const textColor =
      slide.slide_role !== "info"
        ? contrastText(tokens.dark_background)
        : contrastText(tokens.light_background);
    const bodyText = slide.body_display || slide.body || "";
    const footerText = slide.button_label || slide.accent_motif || slide.layout_variant;

    card.className = `slide-card ${useDark ? "dark" : "light"}`;
    card.style.background = background;
    card.style.color = textColor;
    card.style.boxShadow = `inset 0 0 0 1px ${withOpacity(tokens.accent_blue, 0.18)}`;
    card.innerHTML = `
      <div>
        <div class="slide-label">${slide.slide_number.toString().padStart(2, "0")} ${slide.slide_role}</div>
      </div>
      <div>
        <div class="slide-headline">${escapeHtml(slide.headline_display || slide.headline)}</div>
        ${bodyText ? `<div class="slide-body">${escapeHtml(bodyText)}</div>` : ""}
      </div>
      <div class="slide-footer">${escapeHtml(footerText)}</div>
    `;
    elements.previewGrid.appendChild(card);
  });
}

function renderImagePreviews(variant) {
  variant.preview_image_urls.forEach((url, index) => {
    const wrapper = document.createElement("article");
    wrapper.className = "slide-card image-card";
    const label = variant.payload.slides[index]
      ? `${String(variant.payload.slides[index].slide_number).padStart(2, "0")} ${variant.payload.slides[index].slide_role}`
      : `Slide ${index + 1}`;
    wrapper.innerHTML = `
      <div class="slide-label">${label}</div>
      <img class="slide-image" src="${url}?t=${Date.now()}" alt="${label}" />
    `;
    elements.previewGrid.appendChild(wrapper);
  });
}

function renderVariantPaths(variant) {
  elements.variantPaths.appendChild(pathChip(`Job: ${variant.job_artifact_path}`));
  elements.variantPaths.appendChild(pathChip(`Render Payload: ${variant.render_payload_path}`));
  if (variant.render_result_path) {
    elements.variantPaths.appendChild(pathChip(`Render Result: ${variant.render_result_path}`));
  }
}

function getCurrentVariant() {
  if (!state.currentRound || !state.currentRound.variants.length) {
    return null;
  }
  return state.currentRound.variants[state.currentIndex] || null;
}

function toggleBusy(isBusy) {
  elements.form.querySelectorAll("button, input, textarea, select").forEach((node) => {
    node.disabled = isBusy;
  });
  elements.nextRoundButton.disabled = isBusy || !state.currentRound;
  toggleRatingButtons(!isBusy && Boolean(getCurrentVariant()));
}

function toggleRatingButtons(enabled) {
  elements.ratingButtons.forEach((button) => {
    button.disabled = !enabled;
  });
}

function setStatus(message, isError = false) {
  elements.statusText.textContent = message;
  elements.statusText.style.color = isError ? "#ff9b9b" : "";
}

function startRoundRefresh() {
  stopRoundRefresh();
  if (!state.currentRound) {
    return;
  }
  refreshTimer = window.setInterval(() => {
    void refreshRound();
  }, 5000);
}

function stopRoundRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

async function refreshRound() {
  if (!state.currentRound) {
    return;
  }
  try {
    const round = await requestJson(`/api/rounds/${state.currentRound.round_id}`);
    const previousVariantId = getCurrentVariant() ? getCurrentVariant().variant_id : null;
    applyRound(round, previousVariantId);
  } catch (error) {
    console.error(error);
  }
}

function populateSelect(select, options, valueKey, labelKey, defaultValue) {
  select.innerHTML = "";
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option[valueKey];
    node.textContent = option[labelKey];
    if (option[valueKey] === defaultValue) {
      node.selected = true;
    }
    select.appendChild(node);
  });
}

function metaChip(label) {
  const chip = document.createElement("span");
  chip.className = "meta-chip";
  chip.textContent = label;
  return chip;
}

function pathChip(label) {
  const chip = document.createElement("div");
  chip.className = "path-chip";
  chip.textContent = label;
  return chip;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function cleanValue(value) {
  const cleaned = value.trim();
  return cleaned ? cleaned : null;
}

function capitalize(value) {
  if (!value) {
    return "";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function isDark(hex) {
  const rgb = hexToRgb(hex);
  const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
  return brightness < 145;
}

function contrastText(hex) {
  return isDark(hex) ? "#FFFFFF" : "#111111";
}

function withOpacity(hex, opacity) {
  const rgb = hexToRgb(hex);
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((character) => character + character).join("")
    : normalized;
  return {
    r: Number.parseInt(value.slice(0, 2), 16),
    g: Number.parseInt(value.slice(2, 4), 16),
    b: Number.parseInt(value.slice(4, 6), 16),
  };
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

init();
