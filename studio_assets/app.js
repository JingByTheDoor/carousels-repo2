const state = {
  bootstrap: null,
  currentRound: null,
  selectedWinnerId: null,
  feedbackByVariant: {},
  slideIndexByVariant: {},
  fullscreenVariantId: null,
  pollTimer: null,
  isBusy: false,
};

const elements = {
  generateButton: document.getElementById("generate-button"),
  nextRoundButton: document.getElementById("next-round-button"),
  submitButton: document.getElementById("submit-button"),
  statusText: document.getElementById("status-text"),
  topic: document.getElementById("topic"),
  script: document.getElementById("script"),
  ctaText: document.getElementById("cta_text"),
  notes: document.getElementById("notes"),
  preferredStyle: document.getElementById("preferred_style"),
  baseCopyLength: document.getElementById("base_copy_length"),
  imageMode: document.getElementById("image_mode"),
  language: document.getElementById("language"),
  roundTitle: document.getElementById("round-title"),
  roundFigmaLink: document.getElementById("round-figma-link"),
  roundMeta: document.getElementById("round-meta"),
  roundBrief: document.getElementById("round-brief"),
  reviewGrid: document.getElementById("review-grid"),
};

init();

async function init() {
  bindEvents();
  try {
    const bootstrap = await requestJson("/api/bootstrap");
    state.bootstrap = bootstrap;
    populateSelect(elements.preferredStyle, bootstrap.style_options, "auto");
    populateSelect(elements.baseCopyLength, bootstrap.copy_length_options, bootstrap.review_defaults.base_copy_length);
    populateSelect(elements.imageMode, bootstrap.image_mode_options, bootstrap.review_defaults.image_mode);

    const latestRound =
      bootstrap.latest_review_round ||
      (bootstrap.latest_round && bootstrap.latest_round.round_mode === "review" ? bootstrap.latest_round : null);

    if (latestRound) {
      applyRound(latestRound);
      setStatus(roundStatusMessage(latestRound));
    } else {
      renderEmptyState();
      setStatus("Ready. Click Generate 3 to create a new review round.");
    }
  } catch (error) {
    renderEmptyState();
    setStatus(error.message || String(error), true);
  }
}

function bindEvents() {
  elements.generateButton.addEventListener("click", onGenerateRound);
  elements.nextRoundButton.addEventListener("click", onGenerateNextRound);
  elements.submitButton.addEventListener("click", onSubmitReview);
  window.addEventListener("keydown", onGlobalKeydown);
}

async function onGenerateRound() {
  try {
    toggleBusy(true);
    setStatus("Generating three new variants...");
    const payload = buildReviewRequestPayload();
    const round = await requestJson("/api/review-rounds", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    applyRound(round);
    setStatus("Round created. Waiting for real Figma renders...");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

async function onGenerateNextRound() {
  const round = state.currentRound;
  if (!round) {
    return;
  }

  const winnerId = state.selectedWinnerId;
  if (!winnerId) {
    setStatus("Pick the strongest variant first.", true);
    return;
  }

  const loserFeedback = {};
  for (const variant of round.variants) {
    if (variant.variant_id === winnerId) {
      continue;
    }
    const note = cleanValue(state.feedbackByVariant[variant.variant_id]);
    if (!note) {
      setStatus("Add one short note for each rejected variant before generating the next round.", true);
      return;
    }
    loserFeedback[variant.variant_id] = note;
  }

  try {
    toggleBusy(true);
    setStatus("Saving your winner and generating the next three...");
    const winnerFeedback = cleanValue(state.feedbackByVariant[winnerId]);
    await requestJson(`/api/review-rounds/${round.round_id}/winner`, {
      method: "POST",
      body: JSON.stringify({
        winner_variant_id: winnerId,
        winner_feedback: winnerFeedback,
        loser_feedback: loserFeedback,
      }),
    });
    const nextRound = await requestJson(`/api/review-rounds/${round.round_id}/next`, {
      method: "POST",
    });
    applyRound(nextRound);
    setStatus("Next round created. Waiting for fresh Figma renders...");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

async function onSubmitReview() {
  const round = state.currentRound;
  if (!round) {
    return;
  }

  const winnerId = state.selectedWinnerId;
  if (!winnerId) {
    setStatus("Pick the strongest variant first.", true);
    return;
  }

  const loserFeedback = {};
  for (const variant of round.variants) {
    if (variant.variant_id === winnerId) {
      continue;
    }
    const note = cleanValue(state.feedbackByVariant[variant.variant_id]);
    if (!note) {
      setStatus("Add one short note for each rejected variant before submitting.", true);
      return;
    }
    loserFeedback[variant.variant_id] = note;
  }

  try {
    toggleBusy(true);
    setStatus("Submitting review files and clearing the current round...");
    const response = await requestJson(`/api/review-rounds/${round.round_id}/submit`, {
      method: "POST",
      body: JSON.stringify({
        winner_variant_id: winnerId,
        winner_feedback: cleanValue(state.feedbackByVariant[winnerId]),
        loser_feedback: loserFeedback,
      }),
    });
    clearCurrentRound();
    const notePath = response.review_note_markdown_path || response.review_note_json_path || "notes/review_feedback/";
    setStatus(`Review submitted. Files saved to ${notePath}`, "success");
  } catch (error) {
    setStatus(error.message || String(error), true);
  } finally {
    toggleBusy(false);
  }
}

function buildReviewRequestPayload() {
  return compactObject({
    topic: cleanValue(elements.topic.value),
    script: cleanValue(elements.script.value),
    cta_text: cleanValue(elements.ctaText.value),
    notes: cleanValue(elements.notes.value),
    preferred_style: elements.preferredStyle.value || state.bootstrap.review_defaults.preferred_style,
    base_copy_length: elements.baseCopyLength.value || state.bootstrap.review_defaults.base_copy_length,
    image_mode: elements.imageMode.value || state.bootstrap.review_defaults.image_mode,
    language: cleanValue(elements.language.value),
  });
}

function applyRound(round) {
  state.currentRound = round;
  state.selectedWinnerId = round.winner_variant_id || null;
  const nextFeedbackByVariant = {};
  const nextSlideIndexByVariant = { ...state.slideIndexByVariant };
  round.variants.forEach((variant) => {
    nextFeedbackByVariant[variant.variant_id] =
      state.feedbackByVariant[variant.variant_id] ?? variant.winner_feedback ?? variant.rejection_note ?? variant.rating_note ?? "";
    const maxIndex = Math.max((variant.preview_image_urls || []).length - 1, 0);
    const currentIndex = nextSlideIndexByVariant[variant.variant_id] ?? 0;
    nextSlideIndexByVariant[variant.variant_id] = Math.min(currentIndex, maxIndex);
  });
  state.feedbackByVariant = nextFeedbackByVariant;
  state.slideIndexByVariant = nextSlideIndexByVariant;

  renderRoundSummary(round);
  renderVariantGrid(round);
  renderFullscreenViewer();
  updateNextButtonState();
  managePolling(round);
}

function renderEmptyState() {
  elements.roundTitle.textContent = "No review round yet";
  elements.roundBrief.textContent = "Click Generate 3 to create three real Figma-ready options.";
  elements.roundMeta.innerHTML = "";
  elements.roundFigmaLink.classList.add("hidden");
  elements.roundFigmaLink.href = "#";
  elements.reviewGrid.innerHTML = `
    <article class="empty-card">
      <p class="empty-title">Nothing generated yet</p>
      <p class="empty-copy">This app only shows real rendered review variants. Generate a round and let the Figma plugin finish the renders.</p>
    </article>
  `;
  updateNextButtonState();
}

function clearCurrentRound() {
  stopPolling();
  state.currentRound = null;
  state.selectedWinnerId = null;
  state.feedbackByVariant = {};
  state.slideIndexByVariant = {};
  state.fullscreenVariantId = null;
  renderFullscreenViewer();
  renderEmptyState();
}

function renderRoundSummary(round) {
  elements.roundTitle.textContent = `Round ${round.round_number}`;
  elements.roundBrief.textContent =
    round.generated_brief || "Materials helpful to English teachers";

  elements.roundMeta.innerHTML = "";
  elements.roundMeta.appendChild(metaChip("Review Mode"));
  elements.roundMeta.appendChild(metaChip("3 Variants"));
  elements.roundMeta.appendChild(metaChip(`Status: ${formatStatus(round.review_status)}`));
  elements.roundMeta.appendChild(metaChip(`Niche: ${state.bootstrap.review_defaults.niche_label}`));

  if (round.figma_file_url) {
    elements.roundFigmaLink.classList.remove("hidden");
    elements.roundFigmaLink.href = round.figma_file_url;
  } else {
    elements.roundFigmaLink.classList.add("hidden");
    elements.roundFigmaLink.href = "#";
  }
}

function renderVariantGrid(round) {
  elements.reviewGrid.innerHTML = "";
  round.variants.forEach((variant) => {
    const card = document.createElement("article");
    card.className = `variant-card ${variant.variant_id === state.selectedWinnerId ? "winner-selected" : ""}`;

    const isWinner = variant.variant_id === state.selectedWinnerId;
    const previewMarkup = buildPreviewMarkup(variant);
    const pageHref = variant.figma_page_url || variant.figma_url || "#";
    const feedbackValue = state.feedbackByVariant[variant.variant_id] || "";
    const feedbackDisabled = !isRoundReadyForReview(round) || state.isBusy;
    const feedbackLabel = isWinner ? "What is good here or still not perfect?" : "What is wrong with this one?";
    const feedbackPlaceholder = isWinner
      ? "Example: strong cover, better image choice, but CTA could be clearer. Use /slide_7 if needed."
      : "Example: too much text, weaker cover, image feels generic. Use /slide_4 if needed.";
    const exportMarkup = buildExportLinksMarkup(variant);

    card.innerHTML = `
      <div class="variant-header">
        <div>
          <p class="variant-kicker">Variant ${variant.ordinal}</p>
          <h3>${escapeHtml(variant.requested_style_label)}</h3>
        </div>
        <label class="winner-toggle ${isWinner ? "active" : ""}">
          <input type="radio" name="winner-variant" value="${escapeHtml(variant.variant_id)}" ${
            isWinner ? "checked" : ""
          } ${!isRoundReadyForReview(round) || state.isBusy ? "disabled" : ""} />
          <span>Pick Winner</span>
        </label>
      </div>

      <div class="preview-panel">
        ${previewMarkup}
      </div>

      <div class="variant-meta">
        ${chipMarkup(`Copy: ${escapeHtml(variant.copy_length_label)}`)}
        ${chipMarkup(`Layout: ${escapeHtml(variant.layout_density_label)}`)}
        ${chipMarkup(`Images: ${variant.image_count}`)}
        ${chipMarkup(`Render: ${escapeHtml(formatStatus(variant.render_status))}`)}
      </div>

      <div class="variant-links">
        ${
          variant.figma_url
            ? `<a class="chip-link" href="${escapeAttribute(variant.figma_url)}" target="_blank" rel="noreferrer">Open File</a>`
            : ""
        }
        ${
          pageHref !== "#"
            ? `<a class="chip-link" href="${escapeAttribute(pageHref)}" target="_blank" rel="noreferrer">Open Variant Page</a>`
            : ""
        }
      </div>

      ${exportMarkup}

      <label class="feedback-block ${isWinner ? "winner-note" : ""}">
        <span>${escapeHtml(feedbackLabel)}</span>
        <textarea
          class="feedback-input"
          data-variant-id="${escapeHtml(variant.variant_id)}"
          rows="3"
          placeholder="${escapeHtml(feedbackPlaceholder)}"
          ${feedbackDisabled ? "disabled" : ""}
        >${escapeHtml(feedbackValue)}</textarea>
        <small class="feedback-hint">Tip: use <code>/slide_4</code> to attach a specific slide reference to this note.</small>
      </label>
    `;

    const radio = card.querySelector('input[type="radio"]');
    if (radio) {
      radio.addEventListener("change", () => {
        state.selectedWinnerId = variant.variant_id;
        renderVariantGrid(state.currentRound);
        updateNextButtonState();
      });
    }

    const textarea = card.querySelector(".feedback-input");
    if (textarea) {
      textarea.addEventListener("input", (event) => {
        state.feedbackByVariant[variant.variant_id] = event.target.value;
        updateNextButtonState();
      });
    }

    bindPreviewControls(card, variant);

    elements.reviewGrid.appendChild(card);
  });
}

function buildExportLinksMarkup(variant) {
  const hasPngExports = Array.isArray(variant.export_urls) && variant.export_urls.length > 0;
  const hasPdfExport = Boolean(variant.pdf_export_url);
  if (!hasPngExports && !hasPdfExport) {
    return "";
  }

  const pngLinks = (variant.export_urls || [])
    .map((url, index) => {
      const slideLabel = `Slide ${index + 1}`;
      return `<a class="chip-link export-link" href="${escapeAttribute(url)}" download target="_blank" rel="noreferrer">${escapeHtml(slideLabel)}</a>`;
    })
    .join("");

  const pdfLink = hasPdfExport
    ? `<a class="chip-link export-link" href="${escapeAttribute(variant.pdf_export_url)}" download target="_blank" rel="noreferrer">PDF</a>`
    : "";

  return `
    <div class="variant-exports">
      <span class="exports-label">Exports</span>
      <div class="export-links">
        ${pdfLink}
        ${pngLinks}
      </div>
    </div>
  `;
}

function buildPreviewMarkup(variant) {
  if (variant.preview_image_urls && variant.preview_image_urls.length) {
    const slideCount = variant.preview_image_urls.length;
    const activeIndex = activePreviewIndex(variant);
    const activeSlide = variant.payload?.slides?.[activeIndex];
    const thumbMarkup = variant.preview_image_urls
      .map((url, index) => {
        const slide = variant.payload?.slides?.[index];
        const alt = `Variant ${variant.ordinal} slide ${index + 1}`;
        return `
          <button
            type="button"
            class="preview-thumb-button ${index === activeIndex ? "active" : ""}"
            data-preview-index="${index}"
            aria-label="Show slide ${index + 1}"
          >
            <img class="preview-thumb" src="${escapeAttribute(cacheBust(url))}" alt="${escapeAttribute(alt)}" />
            <span class="preview-thumb-label">${escapeHtml(slide?.slide_number || index + 1)}</span>
          </button>
        `;
      })
      .join("");

    return `
      <div class="preview-stack">
        <div class="preview-stage">
          <img
            class="preview-primary"
            src="${escapeAttribute(cacheBust(variant.preview_image_urls[activeIndex]))}"
            alt="Variant ${variant.ordinal} slide ${activeIndex + 1}"
          />
          <button
            type="button"
            class="preview-fullscreen"
            data-preview-fullscreen="${escapeHtml(variant.variant_id)}"
            aria-label="Open fullscreen preview"
          >
            Full Screen
          </button>
          <button
            type="button"
            class="preview-nav preview-nav-prev"
            data-preview-nav="prev"
            ${activeIndex === 0 ? "disabled" : ""}
            aria-label="Previous slide"
          >
            ‹
          </button>
          <button
            type="button"
            class="preview-nav preview-nav-next"
            data-preview-nav="next"
            ${activeIndex === slideCount - 1 ? "disabled" : ""}
            aria-label="Next slide"
          >
            ›
          </button>
          <div class="preview-stage-meta">
            <span>Slide ${activeIndex + 1}/${slideCount}</span>
            <span>${escapeHtml(formatStatus(activeSlide?.slide_role || "slide"))}</span>
          </div>
        </div>
        <div class="preview-strip" data-preview-strip>
          ${thumbMarkup}
        </div>
      </div>
    `;
  }

  if (variant.render_status === "complete") {
    return `
      <div class="preview-placeholder">
        <strong>Rendered in Figma</strong>
        <span>Open the variant page to inspect the actual slides.</span>
      </div>
    `;
  }

  if (variant.render_status === "error") {
    return `
      <div class="preview-placeholder error">
        <strong>Render failed</strong>
        <span>${escapeHtml(variant.error || "Unknown render error")}</span>
      </div>
    `;
  }

  return `
    <div class="preview-placeholder">
      <strong>Waiting for Figma render</strong>
      <span>The app will replace this placeholder with real rendered previews as soon as the plugin finishes.</span>
    </div>
  `;
}

function bindPreviewControls(card, variant) {
  const fullscreenButton = card.querySelector("[data-preview-fullscreen]");
  if (fullscreenButton) {
    fullscreenButton.addEventListener("click", () => {
      openFullscreenViewer(variant.variant_id);
    });
  }

  card.querySelectorAll("[data-preview-index]").forEach((button) => {
    button.addEventListener("click", () => {
      setPreviewIndex(variant.variant_id, Number(button.dataset.previewIndex || 0));
    });
  });

  card.querySelectorAll("[data-preview-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      const delta = button.dataset.previewNav === "next" ? 1 : -1;
      setPreviewIndex(variant.variant_id, activePreviewIndex(variant) + delta);
    });
  });

  const strip = card.querySelector("[data-preview-strip]");
  if (strip) {
    strip.addEventListener(
      "wheel",
      (event) => {
        if (Math.abs(event.deltaY) > Math.abs(event.deltaX)) {
          event.preventDefault();
          strip.scrollLeft += event.deltaY;
        }
      },
      { passive: false },
    );

    const activeThumb = strip.querySelector(".preview-thumb-button.active");
    if (activeThumb) {
      requestAnimationFrame(() => {
        activeThumb.scrollIntoView({ block: "nearest", inline: "center" });
      });
    }
  }
}

function setPreviewIndex(variantId, nextIndex) {
  const variant = state.currentRound?.variants?.find((item) => item.variant_id === variantId);
  if (!variant || !variant.preview_image_urls?.length) {
    return;
  }
  const maxIndex = variant.preview_image_urls.length - 1;
  state.slideIndexByVariant[variantId] = Math.max(0, Math.min(nextIndex, maxIndex));
  renderVariantGrid(state.currentRound);
  renderFullscreenViewer();
}

function activePreviewIndex(variant) {
  const maxIndex = Math.max((variant.preview_image_urls || []).length - 1, 0);
  const currentIndex = state.slideIndexByVariant[variant.variant_id] ?? 0;
  return Math.max(0, Math.min(currentIndex, maxIndex));
}

function openFullscreenViewer(variantId) {
  state.fullscreenVariantId = variantId;
  renderFullscreenViewer();
}

function closeFullscreenViewer() {
  state.fullscreenVariantId = null;
  renderFullscreenViewer();
}

function renderFullscreenViewer() {
  const existing = document.getElementById("fullscreen-viewer");
  if (existing) {
    existing.remove();
  }

  const variant = state.currentRound?.variants?.find((item) => item.variant_id === state.fullscreenVariantId);
  if (!variant || !variant.preview_image_urls?.length) {
    document.body.classList.remove("viewer-open");
    return;
  }

  const activeIndex = activePreviewIndex(variant);
  const activeSlide = variant.payload?.slides?.[activeIndex];
  const overlay = document.createElement("div");
  overlay.id = "fullscreen-viewer";
  overlay.className = "viewer-overlay";
  overlay.innerHTML = `
    <div class="viewer-backdrop" data-viewer-close="true"></div>
    <div class="viewer-dialog" role="dialog" aria-modal="true" aria-label="Fullscreen carousel preview">
      <div class="viewer-header">
        <div>
          <p class="variant-kicker">Variant ${variant.ordinal}</p>
          <h3>${escapeHtml(variant.requested_style_label)}</h3>
        </div>
        <div class="viewer-actions">
          <span class="meta-chip">Slide ${activeIndex + 1}/${variant.preview_image_urls.length}</span>
          <button type="button" class="viewer-close" data-viewer-close="true" aria-label="Close fullscreen preview">Close</button>
        </div>
      </div>
      <div class="viewer-stage">
        <img
          class="viewer-image"
          src="${escapeAttribute(cacheBust(variant.preview_image_urls[activeIndex]))}"
          alt="Variant ${variant.ordinal} slide ${activeIndex + 1}"
        />
        <button
          type="button"
          class="preview-nav preview-nav-prev"
          data-viewer-nav="prev"
          ${activeIndex === 0 ? "disabled" : ""}
          aria-label="Previous slide"
        >
          ‹
        </button>
        <button
          type="button"
          class="preview-nav preview-nav-next"
          data-viewer-nav="next"
          ${activeIndex === variant.preview_image_urls.length - 1 ? "disabled" : ""}
          aria-label="Next slide"
        >
          ›
        </button>
        <div class="preview-stage-meta viewer-stage-meta">
          <span>${escapeHtml(formatStatus(activeSlide?.slide_role || "slide"))}</span>
          <span>${escapeHtml(activeSlide?.headline_display || activeSlide?.headline || "")}</span>
        </div>
      </div>
      <div class="viewer-strip" data-viewer-strip>
        ${variant.preview_image_urls
          .map((url, index) => {
            const slide = variant.payload?.slides?.[index];
            return `
              <button
                type="button"
                class="preview-thumb-button ${index === activeIndex ? "active" : ""}"
                data-viewer-index="${index}"
                aria-label="Show slide ${index + 1}"
              >
                <img class="preview-thumb" src="${escapeAttribute(cacheBust(url))}" alt="Variant ${variant.ordinal} slide ${index + 1}" />
                <span class="preview-thumb-label">${escapeHtml(slide?.slide_number || index + 1)}</span>
              </button>
            `;
          })
          .join("")}
      </div>
    </div>
  `;

  overlay.querySelectorAll("[data-viewer-close]").forEach((button) => {
    button.addEventListener("click", closeFullscreenViewer);
  });
  overlay.querySelectorAll("[data-viewer-nav]").forEach((button) => {
    button.addEventListener("click", () => {
      const delta = button.dataset.viewerNav === "next" ? 1 : -1;
      setPreviewIndex(variant.variant_id, activeIndex + delta);
    });
  });
  overlay.querySelectorAll("[data-viewer-index]").forEach((button) => {
    button.addEventListener("click", () => {
      setPreviewIndex(variant.variant_id, Number(button.dataset.viewerIndex || 0));
    });
  });

  const strip = overlay.querySelector("[data-viewer-strip]");
  if (strip) {
    strip.addEventListener(
      "wheel",
      (event) => {
        if (Math.abs(event.deltaY) > Math.abs(event.deltaX)) {
          event.preventDefault();
          strip.scrollLeft += event.deltaY;
        }
      },
      { passive: false },
    );
    const activeThumb = strip.querySelector(".preview-thumb-button.active");
    if (activeThumb) {
      requestAnimationFrame(() => {
        activeThumb.scrollIntoView({ block: "nearest", inline: "center" });
      });
    }
  }

  document.body.appendChild(overlay);
  document.body.classList.add("viewer-open");
}

function onGlobalKeydown(event) {
  if (!state.fullscreenVariantId) {
    return;
  }

  if (event.key === "Escape") {
    closeFullscreenViewer();
    return;
  }

  const variant = state.currentRound?.variants?.find((item) => item.variant_id === state.fullscreenVariantId);
  if (!variant) {
    return;
  }

  if (event.key === "ArrowRight") {
    event.preventDefault();
    setPreviewIndex(variant.variant_id, activePreviewIndex(variant) + 1);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    setPreviewIndex(variant.variant_id, activePreviewIndex(variant) - 1);
  }
}

function updateNextButtonState() {
  const round = state.currentRound;
  if (!round || state.isBusy || !isRoundReadyForReview(round) || !state.selectedWinnerId) {
    elements.nextRoundButton.disabled = true;
    elements.submitButton.disabled = true;
    return;
  }

  const hasAllLoserNotes = round.variants
    .filter((variant) => variant.variant_id !== state.selectedWinnerId)
    .every((variant) => cleanValue(state.feedbackByVariant[variant.variant_id]));

  elements.nextRoundButton.disabled = !hasAllLoserNotes;
  elements.submitButton.disabled = !hasAllLoserNotes;
}

function isRoundReadyForReview(round) {
  return round.review_status === "ready_for_review" || round.review_status === "winner_selected";
}

function managePolling(round) {
  stopPolling();
  if (!shouldPoll(round)) {
    return;
  }

  state.pollTimer = window.setInterval(async () => {
    try {
      const refreshed = await requestJson(`/api/review-rounds/${round.round_id}`);
      applyRound(refreshed);
      setStatus(roundStatusMessage(refreshed));
    } catch (error) {
      stopPolling();
      setStatus(error.message || String(error), true);
    }
  }, 3000);
}

function shouldPoll(round) {
  if (!round) {
    return false;
  }
  if (round.review_status === "rendering" || round.review_status === "drafting") {
    return true;
  }
  return round.variants.some((variant) => variant.render_status === "planned" || variant.render_status === "rendering");
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function toggleBusy(isBusy) {
  state.isBusy = isBusy;
  elements.generateButton.disabled = isBusy;
  elements.nextRoundButton.disabled = true;
  elements.submitButton.disabled = true;
  [
    elements.topic,
    elements.script,
    elements.ctaText,
    elements.notes,
    elements.preferredStyle,
    elements.baseCopyLength,
    elements.imageMode,
    elements.language,
  ].forEach((field) => {
    field.disabled = isBusy;
  });

  if (state.currentRound) {
    renderVariantGrid(state.currentRound);
    updateNextButtonState();
  }
}

function setStatus(message, isError = false) {
  elements.statusText.textContent = message;
  const strip = elements.statusText.parentElement;
  if (strip) {
    strip.classList.toggle("error", isError);
  }
}

function roundStatusMessage(round) {
  const base = {
    drafting: "Drafting the round...",
    rendering: "Rendering real Figma variants...",
    ready_for_review: "All three variants are ready for review.",
    winner_selected: "Winner saved. Generate the next three when ready.",
    error: "A render error occurred. Check the variant cards.",
  }[round.review_status] || "Studio ready.";
  return base;
}

function formatStatus(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function requestJson(url, options = {}) {
  const requestOptions = {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  };

  return fetch(url, requestOptions)
    .catch((error) => {
      if (error instanceof TypeError) {
        throw new Error(
          `Studio backend is unreachable at ${window.location.origin}. Start the app with .\\.venv\\Scripts\\python.exe tools\\start_studio.py and refresh.`,
        );
      }
      throw error;
    })
    .then(async (response) => {
      const raw = await response.text();
      let payload = null;
      if (raw) {
        try {
          payload = JSON.parse(raw);
        } catch (_error) {
          payload = raw;
        }
      }

      if (!response.ok) {
        if (payload && typeof payload === "object" && payload.detail) {
          throw new Error(payload.detail);
        }
        throw new Error(typeof payload === "string" ? payload : `Request failed with status ${response.status}`);
      }
      return payload;
    });
}

function populateSelect(select, options, defaultValue) {
  select.innerHTML = "";
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option.value;
    node.textContent = option.label;
    if (option.value === defaultValue) {
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

function chipMarkup(label) {
  return `<span class="meta-chip">${label}</span>`;
}

function compactObject(value) {
  return Object.fromEntries(Object.entries(value).filter((entry) => entry[1] !== null && entry[1] !== ""));
}

function cleanValue(value) {
  if (!value) {
    return null;
  }
  const cleaned = String(value).trim().replace(/\s+/g, " ");
  return cleaned || null;
}

function cacheBust(url) {
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}t=${Date.now()}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}
