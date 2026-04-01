const state = {
  bootstrap: null,
  currentRound: null,
  selectedWinnerId: null,
  feedbackByVariant: {},
  pollTimer: null,
  isBusy: false,
};

const elements = {
  generateButton: document.getElementById("generate-button"),
  nextRoundButton: document.getElementById("next-round-button"),
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
    await requestJson(`/api/review-rounds/${round.round_id}/winner`, {
      method: "POST",
      body: JSON.stringify({
        winner_variant_id: winnerId,
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
  state.feedbackByVariant = {};
  round.variants.forEach((variant) => {
    state.feedbackByVariant[variant.variant_id] = variant.rejection_note || variant.rating_note || "";
  });

  renderRoundSummary(round);
  renderVariantGrid(round);
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
    const feedbackDisabled = !state.selectedWinnerId || isWinner || !isRoundReadyForReview(round) || state.isBusy;

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

      <label class="feedback-block ${isWinner ? "hidden" : ""}">
        <span>What is wrong with this one?</span>
        <textarea
          class="feedback-input"
          data-variant-id="${escapeHtml(variant.variant_id)}"
          rows="3"
          placeholder="Example: too much text, weaker cover, image feels generic"
          ${feedbackDisabled ? "disabled" : ""}
        >${escapeHtml(feedbackValue)}</textarea>
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

    elements.reviewGrid.appendChild(card);
  });
}

function buildPreviewMarkup(variant) {
  if (variant.preview_image_urls && variant.preview_image_urls.length) {
    const thumbMarkup = variant.preview_image_urls
      .slice(1, 7)
      .map((url, index) => {
        const alt = `Variant ${variant.ordinal} slide ${index + 2}`;
        return `<img class="preview-thumb" src="${escapeAttribute(cacheBust(url))}" alt="${escapeAttribute(alt)}" />`;
      })
      .join("");

    return `
      <div class="preview-stack">
        <img class="preview-primary" src="${escapeAttribute(cacheBust(variant.preview_image_urls[0]))}" alt="Variant ${variant.ordinal} cover" />
        ${
          thumbMarkup
            ? `<div class="preview-strip">${thumbMarkup}</div>`
            : '<div class="preview-placeholder small">Rendered. Open the Figma page for the full 7-slide set.</div>'
        }
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

function updateNextButtonState() {
  const round = state.currentRound;
  if (!round || state.isBusy || !isRoundReadyForReview(round) || !state.selectedWinnerId) {
    elements.nextRoundButton.disabled = true;
    return;
  }

  const hasAllLoserNotes = round.variants
    .filter((variant) => variant.variant_id !== state.selectedWinnerId)
    .every((variant) => cleanValue(state.feedbackByVariant[variant.variant_id]));

  elements.nextRoundButton.disabled = !hasAllLoserNotes;
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

  return fetch(url, requestOptions).then(async (response) => {
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
