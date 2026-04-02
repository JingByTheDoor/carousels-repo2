figma.showUI(__html__, { width: 440, height: 720, themeColors: true });

const DEFAULT_CANVAS = { width: 1080, height: 1350, slide_gap: 120 };
const DEFAULT_TOKENS = {
  light_background: "#F4F6F7",
  dark_background: "#020202",
  text_dark: "#111111",
  text_light: "#FFFFFF",
  accent_blue: "#55C3EE",
  accent_magenta: "#9E0E4C",
  accent_gold: "#B59868",
  accent_orange: "#FF9300",
  accent_purple: "#6B1FD1",
  accent_navy: "#07215B"
};
const DEFAULT_TYPOGRAPHY = {
  cover_family: "Inter",
  cover_style: "Black",
  body_heading_family: "Poppins",
  body_heading_style: "Bold",
  body_family: "Poppins",
  body_style: "Regular",
  cta_heading_family: "Inter",
  cta_heading_style: "Bold",
  cta_body_family: "Inter",
  cta_body_style: "Regular"
};
const FONT_FALLBACKS = {
  Inter: ["Black", "Bold", "Semi Bold", "Regular"],
  Poppins: ["Bold", "SemiBold", "Regular", "Medium"],
  Montserrat: ["Black", "Bold", "SemiBold", "Regular"]
};
const PREVIEW_EXPORT_WIDTH = 720;

figma.ui.onmessage = async (message) => {
  if (!message || !message.type) {
    return;
  }

  switch (message.type) {
    case "render-payload":
      await handleRenderPayload(message);
      return;
    case "bridge-poll-next-job":
      await handleBridgePoll(message);
      return;
    case "bridge-post-render-result":
      await handleBridgePostResult(message);
      return;
    case "bridge-post-render-error":
      await handleBridgePostError(message);
      return;
    default:
      return;
  }
};

async function handleRenderPayload(message) {
  try {
    const payload = normalizePayload(message.payload);
    figma.ui.postMessage({ type: "status", message: "Rendering carousel..." });
    const result = await renderCarousel(payload);
    figma.notify(`Rendered ${payload.job_id} into ${result.page_name}`);
    figma.ui.postMessage({ type: "render-complete", result });
  } catch (error) {
    const text = formatUnknownError(error);
    figma.notify(text, { error: true });
    figma.ui.postMessage({ type: "render-error", message: text });
  }
}

async function handleBridgePoll(message) {
  try {
    const serverUrl = normalizeServerUrl(message.serverUrl);
    const response = await fetch(`${serverUrl}/next-job`);
    if (response.status === 204) {
      figma.ui.postMessage({ type: "bridge-empty" });
      return;
    }

    const payload = await parseBridgeResponse(response);
    if (!payload || !payload.payload) {
      throw new Error("Render bridge returned an invalid job payload.");
    }

    figma.ui.postMessage({ type: "bridge-next-job", job: payload });
  } catch (error) {
    figma.ui.postMessage({
      type: "bridge-error",
      action: "poll",
      message: formatUnknownError(error),
      details: serializeUnknownError(error)
    });
  }
}

async function handleBridgePostResult(message) {
  try {
    const serverUrl = normalizeServerUrl(message.serverUrl);
    const response = await fetch(`${serverUrl}/render-result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message.result)
    });
    const payload = await parseBridgeResponse(response);
    figma.ui.postMessage({ type: "bridge-post-complete", payload });
  } catch (error) {
    figma.ui.postMessage({
      type: "bridge-error",
      action: "post-result",
      message: formatUnknownError(error),
      details: serializeUnknownError(error)
    });
  }
}

async function handleBridgePostError(message) {
  try {
    const serverUrl = normalizeServerUrl(message.serverUrl);
    const response = await fetch(`${serverUrl}/render-error`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: message.jobId,
        error: message.error
      })
    });
    const payload = await parseBridgeResponse(response);
    figma.ui.postMessage({ type: "bridge-post-error-complete", payload });
  } catch (error) {
    figma.ui.postMessage({
      type: "bridge-error",
      action: "post-error",
      message: formatUnknownError(error),
      details: serializeUnknownError(error)
    });
  }
}

async function parseBridgeResponse(response) {
  const raw = await response.text();
  let payload = {};
  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch (error) {
      throw new Error(`Render bridge returned invalid JSON (${response.status}).`);
    }
  }

  if (!response.ok) {
    const errorMessage = payload && typeof payload.error === "string"
      ? payload.error
      : `Render bridge returned ${response.status}.`;
    throw new Error(errorMessage);
  }

  return payload;
}

function normalizeServerUrl(serverUrl) {
  if (typeof serverUrl !== "string" || !serverUrl.trim()) {
    throw new Error("Render bridge URL is required.");
  }
  return serverUrl.trim().replace(/\/+$/, "");
}

function formatUnknownError(error) {
  if (error instanceof Error && typeof error.message === "string" && error.message.trim()) {
    return error.message;
  }

  if (error && typeof error === "object") {
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
    if (typeof error.error === "string" && error.error.trim()) {
      return error.error;
    }
    const serialized = serializeUnknownError(error);
    return serialized || "Unknown bridge error.";
  }

  if (typeof error === "string" && error.trim()) {
    return error;
  }

  return String(error);
}

function serializeUnknownError(error) {
  if (error === null || typeof error === "undefined") {
    return "";
  }
  if (typeof error === "string") {
    return error;
  }
  try {
    return JSON.stringify(error);
  } catch (serializationError) {
    return String(error);
  }
}

function normalizePayload(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Missing render payload.");
  }
  if (payload.schema_version !== "figma_plugin_payload_v1" && payload.schema_version !== "figma_plugin_payload_v2") {
    throw new Error("Unsupported payload schema version.");
  }
  if (!Array.isArray(payload.slides) || payload.slides.length !== 7) {
    throw new Error("Render payload must contain exactly 7 slides.");
  }
  if (!payload.job_id) {
    throw new Error("Render payload is missing job_id.");
  }

  return Object.assign({}, payload, {
    canvas: Object.assign({}, DEFAULT_CANVAS, payload.canvas || {}),
    image_strategy: Object.assign({ mode: "none", provider: null }, payload.image_strategy || {}),
    style_tokens: Object.assign({}, DEFAULT_TOKENS, payload.style_tokens || {}),
    typography: Object.assign({}, DEFAULT_TYPOGRAPHY, payload.typography || {}),
    slides: payload.slides.map(normalizeSlide)
  });
}

function normalizeSlide(slide) {
  const bodyText = typeof slide.body === "string" ? slide.body : null;
  return Object.assign({}, slide, {
    headline_short: cleanText(slide.headline_short),
    headline_display: cleanText(slide.headline_display) || cleanText(slide.headline),
    body: bodyText,
    body_short: cleanText(slide.body_short),
    body_display: cleanText(slide.body_display) || bodyText,
    supporting_text: cleanText(slide.supporting_text),
    button_label: cleanText(slide.button_label),
    image_slot: cleanText(slide.image_slot) || "none",
    image_required: Boolean(slide.image_required),
    image_treatment: cleanText(slide.image_treatment) || "none",
    image_asset: normalizeImageAsset(slide.image_asset),
    max_headline_lines: typeof slide.max_headline_lines === "number" ? slide.max_headline_lines : 4,
    max_body_lines: typeof slide.max_body_lines === "number" ? slide.max_body_lines : 6
  });
}

function normalizeImageAsset(asset) {
  if (!asset || typeof asset !== "object") {
    return null;
  }
  const url = cleanText(asset.url);
  const localPath = cleanText(asset.local_path);
  const credit = cleanText(asset.credit);
  const provider = cleanText(asset.provider);
  const dataBase64 = cleanText(asset.data_base64);
  if (!url && !localPath && !dataBase64) {
    return null;
  }
  return {
    provider,
    url,
    local_path: localPath,
    credit,
    data_base64: dataBase64
  };
}

async function renderCarousel(payload) {
  const page = figma.createPage();
  page.name = uniquePageName(payload.page_name || `${payload.job_id}-plugin-render`);
  await figma.setCurrentPageAsync(page);

  const frames = [];
  const nodeIds = [];

  for (let index = 0; index < payload.slides.length; index += 1) {
    const slide = payload.slides[index];
    const frame = figma.createFrame();
    frame.name = `${String(slide.slide_number).padStart(2, "0")} ${slide.slide_role}`;
    frame.resize(payload.canvas.width, payload.canvas.height);
    frame.x = index * (payload.canvas.width + payload.canvas.slide_gap);
    frame.y = 0;
    frame.clipsContent = true;
    page.appendChild(frame);

    await renderSlide(frame, slide, payload);
    frames.push(frame);
    nodeIds.push(frame.id);
  }

  figma.viewport.scrollAndZoomIntoView(frames);
  const previewImages = await exportSlidePreviews(frames, payload.slides);
  return {
    schema_version: "figma_plugin_result_v1",
    job_id: payload.job_id,
    page_name: page.name,
    page_id: page.id,
    file_key: typeof figma.fileKey === "string" ? figma.fileKey : null,
    file_url: typeof figma.fileKey === "string" ? `https://www.figma.com/design/${figma.fileKey}` : null,
    page_url: typeof figma.fileKey === "string" ? `https://www.figma.com/design/${figma.fileKey}?page-id=${encodeURIComponent(page.id)}` : null,
    slide_node_ids: nodeIds,
    preview_images: previewImages,
    rendered_at: new Date().toISOString()
  };
}

async function exportSlidePreviews(frames, slides) {
  const previews = [];
  for (let index = 0; index < frames.length; index += 1) {
    try {
      const bytes = await frames[index].exportAsync({
        format: "PNG",
        constraint: {
          type: "WIDTH",
          value: PREVIEW_EXPORT_WIDTH
        }
      });
      previews.push({
        slide_number: slides[index] ? slides[index].slide_number : index + 1,
        mime_type: "image/png",
        data_base64: encodeBase64(bytes)
      });
    } catch (error) {
      // Keep the render usable even if preview export fails.
    }
  }
  return previews;
}

async function renderSlide(frame, slide, payload) {
  switch (slide.layout_variant) {
    case "cover_black_hero":
      await renderCoverSlide(frame, slide, payload);
      return;
    case "cta_dark_glow":
      await renderCtaSlide(frame, slide, payload);
      return;
    case "body_mask_band_left":
      await renderMaskBandBodySlide(frame, slide, payload);
      return;
    case "body_spotlight_panel":
      await renderSpotlightBodySlide(frame, slide, payload);
      return;
    case "body_editorial_bullet":
    default:
      await renderEditorialBodySlide(frame, slide, payload);
      return;
  }
}

async function renderCoverSlide(frame, slide, payload) {
  if (isAlderSplitRight(payload) || isAlderSplitLeft(payload)) {
    await renderAlderMediaCoverSlide(frame, slide, payload);
    return;
  }

  if (isCreatorMonoMinimal(payload)) {
    await renderCreatorMonoCoverSlide(frame, slide, payload);
    return;
  }

  if (isLightGrainGlow(payload)) {
    await renderLightGrainCoverSlide(frame, slide, payload);
    return;
  }

  if (isRetroSwipeCreator(payload)) {
    await renderRetroSwipeCoverSlide(frame, slide, payload);
    return;
  }

  if (isTwitterCardSoft(payload)) {
    await renderTwitterCardCoverSlide(frame, slide, payload);
    return;
  }

  if (isSadekovBlackProfile(payload)) {
    await renderSadekovProfileCoverSlide(frame, slide, payload);
    return;
  }

  if (isSadekovWhiteProfile(payload)) {
    await renderSadekovProfileLightCoverSlide(frame, slide, payload);
    return;
  }

  if (isTypographyEditorialLight(payload)) {
    await renderTypographyEditorialLightCoverSlide(frame, slide, payload);
    return;
  }

  if (isCpGallery(payload)) {
    await renderCpGalleryCoverSlide(frame, slide, payload);
    return;
  }

  if (isTypographySignal(payload)) {
    await renderTypographySignalCoverSlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitCoverSlide(frame, slide, payload);
    return;
  }

  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);

  const cluster = figma.createFrame();
  cluster.name = "Geometric Cluster";
  cluster.resize(860, 330);
  cluster.x = 110;
  cluster.y = 950;
  cluster.fills = [];
  cluster.strokes = [];
  cluster.clipsContent = false;
  frame.appendChild(cluster);

  const triangle = figma.createPolygon();
  triangle.pointCount = 3;
  triangle.resize(250, 250);
  triangle.rotation = 180;
  triangle.x = 0;
  triangle.y = 58;
  triangle.fills = [solidPaint(tokens.accent_orange)];
  triangle.effects = [dropShadow("#000000", 0.18, 0, 14, 26)];
  cluster.appendChild(triangle);

  const nestedSquare = figma.createRectangle();
  nestedSquare.resize(286, 286);
  nestedSquare.cornerRadius = 30;
  nestedSquare.x = 238;
  nestedSquare.y = 54;
  nestedSquare.fills = [solidPaint(tokens.accent_purple)];
  cluster.appendChild(nestedSquare);
  appendNestedSquares(cluster, nestedSquare, tokens);

  const circle = figma.createEllipse();
  circle.resize(300, 300);
  circle.x = 500;
  circle.y = 46;
  circle.fills = [solidPaint(tokens.accent_blue)];
  circle.effects = [dropShadow("#000000", 0.16, 0, 12, 24)];
  cluster.appendChild(circle);
  appendOrbitRings(cluster, circle, tokens.text_light);
  appendTriangleSprinkle(cluster, tokens.text_light);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 56,
    y: 86,
    width: 950,
    maxHeight: 760,
    maxSize: 132,
    minSize: 44,
    lineHeight: 0.96,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderEditorialBodySlide(frame, slide, payload) {
  if (isCreatorMonoMinimal(payload)) {
    await renderCreatorMonoBodySlide(frame, slide, payload);
    return;
  }

  if (isLightGrainGlow(payload)) {
    await renderLightGrainBodySlide(frame, slide, payload);
    return;
  }

  if (isRetroSwipeCreator(payload)) {
    await renderRetroSwipeBodySlide(frame, slide, payload);
    return;
  }

  if (isTwitterCardSoft(payload)) {
    await renderTwitterCardBodySlide(frame, slide, payload);
    return;
  }

  if (isSadekovBlackProfile(payload)) {
    await renderSadekovProfileBodySlide(frame, slide, payload);
    return;
  }

  if (isSadekovWhiteProfile(payload)) {
    await renderSadekovProfileLightBodySlide(frame, slide, payload);
    return;
  }

  if (isTypographyEditorialLight(payload)) {
    await renderTypographyEditorialLightBodySlide(frame, slide, payload);
    return;
  }

  if (isAlderSplitRight(payload)) {
    await renderAlderSplitMediaBodySlide(frame, slide, payload, "right");
    return;
  }

  if (isAlderSplitLeft(payload)) {
    await renderAlderSplitMediaBodySlide(frame, slide, payload, "left");
    return;
  }

  if (isAlderTextOnly(payload)) {
    await renderAlderTextOnlyBodySlide(frame, slide, payload);
    return;
  }

  if (isTypographySignal(payload)) {
    await renderTypographyEditorialBodySlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitBodySlide(frame, slide, payload, "text-left");
    return;
  }

  if (isCpLongform(payload) || isCpGallery(payload)) {
    await renderCpLongformBodySlide(frame, slide, payload, "text-right");
    return;
  }

  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendTopAccentBar(frame, tokens);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  const dot = figma.createEllipse();
  dot.resize(22, 22);
  dot.x = 96;
  dot.y = 124;
  dot.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(dot);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 124,
    y: 84,
    width: 850,
    maxHeight: 190,
    maxSize: 64,
    minSize: 34,
    lineHeight: 1.06,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 96,
    y: 276,
    width: 888,
    maxHeight: 760,
    maxSize: 34,
    minSize: 20,
    lineHeight: 1.34,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderMaskBandBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);

  const band = figma.createRectangle();
  band.resize(250, 1350);
  band.x = 0;
  band.y = 0;
  band.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(band);

  for (let index = 0; index < 3; index += 1) {
    const slot = figma.createEllipse();
    slot.resize(70, 70);
    slot.x = 92;
    slot.y = 928 + index * 94;
    slot.strokes = [solidPaint(tokens.text_light, 0.65)];
    slot.strokeWeight = 6;
    slot.fills = [solidPaint(tokens.light_background)];
    frame.appendChild(slot);
  }

  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 310,
    y: 96,
    width: 690,
    maxHeight: 200,
    maxSize: 62,
    minSize: 34,
    lineHeight: 1.04,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 310,
    y: 290,
    width: 690,
    maxHeight: 830,
    maxSize: 34,
    minSize: 20,
    lineHeight: 1.34,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderSpotlightBodySlide(frame, slide, payload) {
  if (isSadekovBlackProfile(payload)) {
    await renderSadekovProfileBodySlide(frame, slide, payload);
    return;
  }

  if (isSadekovWhiteProfile(payload)) {
    await renderSadekovProfileLightBodySlide(frame, slide, payload);
    return;
  }

  if (isTypographyEditorialLight(payload)) {
    await renderTypographyEditorialLightBodySlide(frame, slide, payload);
    return;
  }

  if (isAlderSplitRight(payload)) {
    await renderAlderSplitMediaBodySlide(frame, slide, payload, "right-tight");
    return;
  }

  if (isAlderSplitLeft(payload)) {
    await renderAlderSplitMediaBodySlide(frame, slide, payload, "left-tight");
    return;
  }

  if (isAlderTextOnly(payload)) {
    await renderAlderTextOnlyBodySlide(frame, slide, payload);
    return;
  }

  if (isTypographySignal(payload)) {
    await renderTypographyPanelBodySlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitBodySlide(frame, slide, payload, "text-right");
    return;
  }

  if (isCpLongform(payload) || isCpGallery(payload)) {
    await renderCpLongformBodySlide(frame, slide, payload, "text-left");
    return;
  }

  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendTopAccentBar(frame, tokens);

  const panel = figma.createRectangle();
  panel.resize(920, 240);
  panel.x = 80;
  panel.y = 940;
  panel.cornerRadius = 34;
  panel.fills = [solidPaint(tokens.accent_navy)];
  panel.opacity = 0.96;
  frame.appendChild(panel);

  const orb = figma.createEllipse();
  orb.resize(300, 300);
  orb.x = 760;
  orb.y = -40;
  orb.fills = [solidPaint(tokens.accent_gold, 0.2)];
  orb.effects = [{ type: "LAYER_BLUR", radius: 56, visible: true }];
  frame.appendChild(orb);

  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 88,
    y: 96,
    width: 860,
    maxHeight: 220,
    maxSize: 62,
    minSize: 34,
    lineHeight: 1.04,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 88,
    y: 286,
    width: 860,
    maxHeight: 500,
    maxSize: 34,
    minSize: 20,
    lineHeight: 1.34,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: (slide.emphasis_words && slide.emphasis_words[0]) || "Key point",
    fontFamily: "Inter",
    fontStyle: "Semi Bold",
    fallbackStyle: "Bold",
    x: 126,
    y: 1016,
    width: 828,
    maxHeight: 74,
    maxSize: 28,
    minSize: 18,
    lineHeight: 1.1,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderCtaSlide(frame, slide, payload) {
  if (isCreatorMonoMinimal(payload)) {
    await renderCreatorMonoCtaSlide(frame, slide, payload);
    return;
  }

  if (isLightGrainGlow(payload)) {
    await renderLightGrainCtaSlide(frame, slide, payload);
    return;
  }

  if (isRetroSwipeCreator(payload)) {
    await renderRetroSwipeCtaSlide(frame, slide, payload);
    return;
  }

  if (isTwitterCardSoft(payload)) {
    await renderTwitterCardCtaSlide(frame, slide, payload);
    return;
  }

  if (isSadekovBlackProfile(payload)) {
    await renderSadekovProfileCtaSlide(frame, slide, payload);
    return;
  }

  if (isSadekovWhiteProfile(payload)) {
    await renderSadekovProfileLightCtaSlide(frame, slide, payload);
    return;
  }

  if (isTypographyEditorialLight(payload)) {
    await renderTypographyEditorialLightCtaSlide(frame, slide, payload);
    return;
  }

  if (isCpLongform(payload) || isCpGallery(payload)) {
    await renderCpSplitCtaSlide(frame, slide, payload);
    return;
  }

  if (isTypographySignal(payload)) {
    await renderTypographySignalCtaSlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitCtaSlide(frame, slide, payload);
    return;
  }

  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);

  appendGlow(frame, 70, 900, 360, tokens.accent_gold, 0.28);
  appendGlow(frame, 770, 140, 320, tokens.accent_magenta, 0.24);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 100,
    y: 228,
    width: 880,
    maxHeight: 300,
    maxSize: 84,
    minSize: 34,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 124,
      y: 540,
      width: 832,
      maxHeight: 180,
      maxSize: 34,
      minSize: 20,
      lineHeight: 1.22,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 180,
      y: 704,
      width: 720,
      maxHeight: 80,
      maxSize: 24,
      minSize: 16,
      lineHeight: 1.18,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  const pill = figma.createRectangle();
  pill.resize(360, 82);
  pill.x = 360;
  pill.y = 804;
  pill.cornerRadius = 999;
  pill.fills = [solidPaint(tokens.text_light)];
  frame.appendChild(pill);

  await createTextBlock(frame, {
    text: slide.button_label || "Open the next step",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 382,
    y: 827,
    width: 316,
    maxHeight: 38,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  await appendFooterSignal(frame, "Like", 86, 1110, "left");
  await appendFooterSignal(frame, "Comment", 248, 1210, "center");
  await appendFooterSignal(frame, "Save", 760, 1110, "right");
}

async function renderAlderSplitMediaBodySlide(frame, slide, payload, orientation) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendTopAccentBar(frame, tokens);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  const mediaOnLeft = orientation === "left" || orientation === "left-tight";
  const mediaWidth = orientation.endsWith("tight") ? 404 : 432;
  const mediaX = mediaOnLeft ? 44 : 1080 - mediaWidth - 44;
  const textX = mediaOnLeft ? 514 : 84;
  const textWidth = mediaOnLeft ? 478 : 508;

  const mediaRect = await appendRemoteImageRect(frame, slide, {
    x: mediaX,
    y: 92,
    width: mediaWidth,
    height: 1090,
    cornerRadius: 28,
    overlayHex: "#FFFFFF",
    overlayOpacity: 0.08
  });
  if (!mediaRect) {
    appendAlderMediaStack(frame, mediaX, 92, mediaWidth, 1090, tokens);
  } else {
    const stroke = figma.createRectangle();
    stroke.resize(mediaWidth, 1090);
    stroke.x = mediaX;
    stroke.y = 92;
    stroke.cornerRadius = 28;
    stroke.fills = [];
    stroke.strokes = [solidPaint(tokens.text_dark, 0.08)];
    stroke.strokeWeight = 2;
    frame.appendChild(stroke);
  }

  const dot = figma.createEllipse();
  dot.resize(22, 22);
  dot.x = textX;
  dot.y = 112;
  dot.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(dot);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: textX + 30,
    y: 82,
    width: textWidth - 30,
    maxHeight: 220,
    maxSize: 60,
    minSize: 30,
    lineHeight: 1.05,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: textX,
    y: 330,
    width: textWidth,
    maxHeight: 780,
    maxSize: 30,
    minSize: 18,
    lineHeight: 1.28,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderAlderTextOnlyBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendTopAccentBar(frame, tokens);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  const lead = figma.createRectangle();
  lead.resize(10, 260);
  lead.x = 84;
  lead.y = 120;
  lead.cornerRadius = 999;
  lead.fills = [solidPaint(tokens.accent_orange)];
  frame.appendChild(lead);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 126,
    y: 122,
    width: 840,
    maxHeight: 220,
    maxSize: 66,
    minSize: 30,
    lineHeight: 1.05,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 126,
    y: 398,
    width: 860,
    maxHeight: 720,
    maxSize: 34,
    minSize: 18,
    lineHeight: 1.38,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderCpLongformBodySlide(frame, slide, payload, orientation) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  const cardOnLeft = orientation === "text-left";
  const cardX = cardOnLeft ? 58 : 748;
  const textX = cardOnLeft ? 406 : 84;
  const textWidth = cardOnLeft ? 610 : 560;

  appendCpDeviceCard(frame, cardX, 248, 274, 804, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: textX,
    y: 160,
    width: textWidth,
    maxHeight: 220,
    maxSize: 60,
    minSize: 30,
    lineHeight: 1.08,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: textX,
    y: 420,
    width: textWidth,
    maxHeight: 620,
    maxSize: 28,
    minSize: 18,
    lineHeight: 1.34,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderCpGalleryCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendCpGalleryWall(frame, tokens);
  await appendRemoteImageRect(frame, slide, {
    x: 356,
    y: 94,
    width: 640,
    height: 594,
    cornerRadius: 30,
    overlayHex: tokens.dark_background,
    overlayOpacity: 0.1,
    effects: [dropShadow("#111111", 0.12, 0, 20, 42)]
  });

  const panel = figma.createRectangle();
  panel.resize(630, 470);
  panel.x = 58;
  panel.y = 734;
  panel.cornerRadius = 34;
  panel.fills = [solidPaint("#FFFFFF", 0.88)];
  panel.effects = [dropShadow("#111111", 0.08, 0, 16, 36)];
  frame.appendChild(panel);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 102,
    y: 788,
    width: 542,
    maxHeight: 360,
    maxSize: 80,
    minSize: 34,
    lineHeight: 1.06,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderTypographySignalCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  await appendRemoteImageRect(frame, slide, {
    x: 0,
    y: 0,
    width: 1080,
    height: 1350,
    opacity: 0.4,
    overlayHex: tokens.dark_background,
    overlayOpacity: 0.38,
    effects: [{ type: "LAYER_BLUR", radius: 10, visible: true }]
  });
  appendTypographyGlowBackdrop(frame, tokens);
  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 96,
    y: 224,
    width: 888,
    maxHeight: 520,
    maxSize: 114,
    minSize: 38,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  await createTextBlock(frame, {
    text: "Swipe through",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 360,
    y: 1110,
    width: 360,
    maxHeight: 40,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  await appendFooterSignal(frame, "Save", 820, 1120, "right");
  await appendFooterSignal(frame, "Read", 120, 1120, "left");
}

async function renderAlderMediaCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  const mediaOnLeft = isAlderSplitLeft(payload);
  setSolidFill(frame, tokens.dark_background);

  const mediaRect = await appendRemoteImageRect(frame, slide, {
    x: mediaOnLeft ? 54 : 580,
    y: 64,
    width: 446,
    height: 1222,
    cornerRadius: 36,
    overlayHex: tokens.dark_background,
    overlayOpacity: 0.18,
    effects: [dropShadow("#000000", 0.18, 0, 20, 44)]
  });

  if (!mediaRect) {
    appendAlderMediaStack(frame, mediaOnLeft ? 54 : 580, 92, 446, 1094, tokens);
  }

  const accent = figma.createRectangle();
  accent.resize(14, 276);
  accent.x = mediaOnLeft ? 540 : 76;
  accent.y = 126;
  accent.cornerRadius = 999;
  accent.fills = [solidPaint(tokens.accent_orange)];
  frame.appendChild(accent);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: mediaOnLeft ? 578 : 108,
    y: 122,
    width: 398,
    maxHeight: 760,
    maxSize: 96,
    minSize: 34,
    lineHeight: 0.98,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderTypographyEditorialBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  appendTypographyGlowBackdrop(frame, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 110,
    y: 108,
    width: 860,
    maxHeight: 200,
    maxSize: 66,
    minSize: 32,
    lineHeight: 1.04,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 124,
    y: 350,
    width: 832,
    maxHeight: 420,
    maxSize: 32,
    minSize: 18,
    lineHeight: 1.28,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  await appendSlideNumberChip(frame, slide.slide_number, tokens);
  await appendFooterSignal(frame, "Keep", 120, 1120, "left");
  await appendFooterSignal(frame, "Save", 820, 1120, "right");
}

async function renderTypographyPanelBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  appendTypographyGlowBackdrop(frame, tokens);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 92,
    y: 104,
    width: 896,
    maxHeight: 190,
    maxSize: 68,
    minSize: 32,
    lineHeight: 1.04,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  const panel = figma.createRectangle();
  panel.resize(930, 480);
  panel.x = 76;
  panel.y = 382;
  panel.cornerRadius = 42;
  panel.fills = [solidPaint("#FFFFFF", 0.08)];
  panel.strokes = [solidPaint(tokens.text_light, 0.16)];
  panel.strokeWeight = 2;
  frame.appendChild(panel);

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 128,
    y: 452,
    width: 826,
    maxHeight: 330,
    maxSize: 30,
    minSize: 18,
    lineHeight: 1.3,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  await appendFooterSignal(frame, "Note", 120, 1120, "left");
  await appendFooterSignal(frame, "Save", 820, 1120, "right");
}

async function renderTypographySignalCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  appendTypographyGlowBackdrop(frame, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 94,
    y: 228,
    width: 892,
    maxHeight: 260,
    maxSize: 96,
    minSize: 34,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 144,
      y: 528,
      width: 792,
      maxHeight: 140,
      maxSize: 34,
      minSize: 18,
      lineHeight: 1.18,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 196,
      y: 690,
      width: 688,
      maxHeight: 72,
      maxSize: 24,
      minSize: 14,
      lineHeight: 1.18,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  const pill = figma.createRectangle();
  pill.resize(330, 76);
  pill.x = 375;
  pill.y = 800;
  pill.cornerRadius = 999;
  pill.fills = [solidPaint(tokens.text_light)];
  frame.appendChild(pill);

  await createTextBlock(frame, {
    text: slide.button_label || "Get access",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 398,
    y: 820,
    width: 284,
    maxHeight: 34,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  await appendFooterSignal(frame, "Like", 86, 1110, "left");
  await appendFooterSignal(frame, "Comment", 248, 1210, "center");
  await appendFooterSignal(frame, "Save for later", 904, 1110, "right");
}

async function renderSadekovProfileCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  await appendSadekovProfileHeader(frame, 160, tokens, "dark");
  await appendSadekovFooter(frame, "dark");
  appendSadekovArrowCue(frame, tokens, "dark");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 117,
    y: 438,
    width: 866,
    maxHeight: 430,
    maxSize: 90,
    minSize: 34,
    lineHeight: 0.98,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderSadekovProfileBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  await appendSadekovProfileHeader(frame, 160, tokens, "dark");
  await appendSadekovFooter(frame, "dark");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Regular",
    x: 120,
    y: 417,
    width: 899,
    maxHeight: 140,
    maxSize: 56,
    minSize: 28,
    lineHeight: 1.02,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.body_family,
      fontStyle: payload.typography.body_style,
      fallbackStyle: "Regular",
      x: 120,
      y: 592,
      width: 860,
      maxHeight: 420,
      maxSize: 34,
      minSize: 18,
      lineHeight: 1.22,
      color: "#E6E6E6",
      alignHorizontal: "LEFT"
    });
  }
}

async function renderSadekovProfileCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  await appendSadekovProfileHeader(frame, 256, tokens, "dark");
  await appendSadekovFooter(frame, "dark");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Regular",
    x: 115,
    y: 486,
    width: 850,
    maxHeight: 160,
    maxSize: 68,
    minSize: 30,
    lineHeight: 1.04,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  const ctaBody = slide.body_display || slide.body;
  if (ctaBody) {
    await createTextBlock(frame, {
      text: ctaBody,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 236,
      y: 1070,
      width: 608,
      maxHeight: 90,
      maxSize: 32,
      minSize: 16,
      lineHeight: 1.14,
      color: "#E9E9E9",
      alignHorizontal: "CENTER"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 236,
      y: 1132,
      width: 608,
      maxHeight: 70,
      maxSize: 28,
      minSize: 14,
      lineHeight: 1.1,
      color: "#D2D2D2",
      alignHorizontal: "CENTER"
    });
  }
}

async function renderSadekovProfileLightCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  await appendSadekovProfileHeader(frame, 160, tokens, "light");
  await appendSadekovFooter(frame, "light");
  appendSadekovArrowCue(frame, tokens, "light");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 117,
    y: 438,
    width: 866,
    maxHeight: 430,
    maxSize: 90,
    minSize: 34,
    lineHeight: 0.98,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderSadekovProfileLightBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  await appendSadekovProfileHeader(frame, 160, tokens, "light");
  await appendSadekovFooter(frame, "light");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Regular",
    x: 120,
    y: 417,
    width: 899,
    maxHeight: 140,
    maxSize: 56,
    minSize: 28,
    lineHeight: 1.02,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.body_family,
      fontStyle: payload.typography.body_style,
      fallbackStyle: "Regular",
      x: 120,
      y: 592,
      width: 860,
      maxHeight: 420,
      maxSize: 34,
      minSize: 18,
      lineHeight: 1.22,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }
}

async function renderSadekovProfileLightCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  await appendSadekovProfileHeader(frame, 256, tokens, "light");
  await appendSadekovFooter(frame, "light");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Regular",
    x: 115,
    y: 486,
    width: 850,
    maxHeight: 160,
    maxSize: 68,
    minSize: 30,
    lineHeight: 1.04,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  const ctaBody = slide.body_display || slide.body;
  if (ctaBody) {
    await createTextBlock(frame, {
      text: ctaBody,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 236,
      y: 1070,
      width: 608,
      maxHeight: 90,
      maxSize: 32,
      minSize: 16,
      lineHeight: 1.14,
      color: "#222222",
      alignHorizontal: "CENTER"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 236,
      y: 1132,
      width: 608,
      maxHeight: 70,
      maxSize: 28,
      minSize: 14,
      lineHeight: 1.1,
      color: "#3F3F3F",
      alignHorizontal: "CENTER"
    });
  }
}

async function renderTypographyEditorialLightCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
  appendTypographyToolCards(frame, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 82,
    y: 126,
    width: 820,
    maxHeight: 420,
    maxSize: 104,
    minSize: 36,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createBulletText(frame, slide.body_display || slide.body, 92, 544, 842, 180, 28, 18, tokens.text_light);
  }
}

async function renderTypographyEditorialLightBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendTypographyEditorialCorners(frame, tokens);
  appendBottomBar(frame, "#020202");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 120,
    y: 164,
    width: 840,
    maxHeight: 240,
    maxSize: 86,
    minSize: 30,
    lineHeight: 1.02,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  const columnTexts = splitTextForTwoColumns(slide.body_display || slide.body || "", slide.emphasis_words || []);
  await createBulletText(frame, columnTexts[0], 108, 486, 340, 330, 28, 18, tokens.text_dark);
  await createBulletText(frame, columnTexts[1], 626, 486, 340, 330, 28, 18, tokens.text_dark);
}

async function renderTypographyEditorialLightCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendBottomBar(frame, "#020202");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 112,
    y: 436,
    width: 856,
    maxHeight: 190,
    maxSize: 90,
    minSize: 34,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 120,
      y: 628,
      width: 840,
      maxHeight: 130,
      maxSize: 32,
      minSize: 18,
      lineHeight: 1.18,
      color: tokens.text_dark,
      alignHorizontal: "CENTER"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 180,
      y: 768,
      width: 720,
      maxHeight: 72,
      maxSize: 24,
      minSize: 14,
      lineHeight: 1.16,
      color: "#2C2C2C",
      alignHorizontal: "CENTER"
    });
  }

  await appendFooterSignalTone(frame, "Like", 86, 1110, "left", "#111111");
  await appendFooterSignalTone(frame, "Comment", 248, 1210, "center", "#111111");
  await appendFooterSignalTone(frame, "Save for later", 904, 1110, "right", "#111111");
}

async function renderCpSplitCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendCpAccentDot(frame, 910, 156, 18, tokens.accent_blue, 0.88);
  appendCpAccentDot(frame, 942, 156, 10, tokens.text_dark, 0.64);
  appendCpDeviceCard(frame, 694, 262, 290, 720, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 74,
    y: 122,
    width: 590,
    maxHeight: 880,
    maxSize: 94,
    minSize: 38,
    lineHeight: 1.08,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderCpSplitBodySlide(frame, slide, payload, orientation) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  const cardX = orientation === "text-right" ? 76 : 724;
  const textX = orientation === "text-right" ? 446 : 86;
  const textWidth = orientation === "text-right" ? 548 : 560;

  appendCpDeviceCard(frame, cardX, 276, 282, 720, tokens);

  if (slide.emphasis_words && slide.emphasis_words[0]) {
    await createTextBlock(frame, {
      text: slide.emphasis_words[0].toUpperCase(),
      fontFamily: "Inter",
      fontStyle: "Bold",
      fallbackStyle: "Bold",
      x: textX,
      y: 126,
      width: 260,
      maxHeight: 40,
      maxSize: 20,
      minSize: 14,
      lineHeight: 1.0,
      color: tokens.accent_navy,
      alignHorizontal: "LEFT"
    });
  }

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: textX,
    y: 176,
    width: textWidth,
    maxHeight: 230,
    maxSize: 64,
    minSize: 30,
    lineHeight: 1.08,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: textX,
    y: 452,
    width: textWidth,
    maxHeight: 520,
    maxSize: 30,
    minSize: 18,
    lineHeight: 1.32,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderCpSplitCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendCpDeviceCard(frame, 744, 250, 250, 720, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 82,
    y: 168,
    width: 590,
    maxHeight: 320,
    maxSize: 88,
    minSize: 34,
    lineHeight: 1.02,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 86,
      y: 560,
      width: 560,
      maxHeight: 144,
      maxSize: 30,
      minSize: 18,
      lineHeight: 1.24,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 86,
      y: 720,
      width: 520,
      maxHeight: 72,
      maxSize: 22,
      minSize: 14,
      lineHeight: 1.18,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }

  const pill = figma.createRectangle();
  pill.resize(320, 76);
  pill.x = 86;
  pill.y = 846;
  pill.cornerRadius = 999;
  pill.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(pill);

  await createTextBlock(frame, {
    text: slide.button_label || "Get access",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 114,
    y: 866,
    width: 264,
    maxHeight: 34,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });
}

async function renderCreatorMonoCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 54,
    y: 286,
    width: 952,
    maxHeight: 650,
    maxSize: 138,
    minSize: 46,
    lineHeight: 0.98,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await appendMonoCreatorFooter(frame, tokens, "dark", false);
}

async function renderCreatorMonoBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  const useRose = slide.slide_number % 2 === 1;
  setSolidFill(frame, useRose ? tokens.accent_magenta : tokens.light_background);
  const headlineColor = useRose ? tokens.text_light : tokens.text_dark;
  const bodyColor = useRose ? tokens.text_light : tokens.text_dark;

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 54,
    y: 118,
    width: 948,
    maxHeight: 280,
    maxSize: 96,
    minSize: 34,
    lineHeight: 0.98,
    color: headlineColor,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 58,
    y: 390,
    width: 912,
    maxHeight: 520,
    maxSize: 64,
    minSize: 26,
    lineHeight: 1.14,
    color: bodyColor,
    alignHorizontal: "LEFT"
  });

  await appendMonoCreatorFooter(frame, tokens, useRose ? "light" : "dark", false);
}

async function renderCreatorMonoCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 54,
    y: 278,
    width: 956,
    maxHeight: 230,
    maxSize: 112,
    minSize: 40,
    lineHeight: 0.98,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 58,
      y: 560,
      width: 928,
      maxHeight: 260,
      maxSize: 46,
      minSize: 22,
      lineHeight: 1.1,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }

  await appendMonoCreatorFooter(frame, tokens, "dark", false);
}

async function renderLightGrainCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, "violet");
  await appendRemoteImageRect(frame, slide, {
    x: 0,
    y: 0,
    width: 1080,
    height: 1350,
    opacity: 0.3,
    overlayHex: "#FFFFFF",
    overlayOpacity: 0.05,
    effects: [{ type: "LAYER_BLUR", radius: 8, visible: true }]
  });

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 72,
    y: 278,
    width: 852,
    maxHeight: 520,
    maxSize: 118,
    minSize: 42,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderLightGrainBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, slide.slide_number % 2 === 0 ? "green" : "violet");
  await appendRemoteImageRect(frame, slide, {
    x: 0,
    y: 0,
    width: 1080,
    height: 1350,
    opacity: 0.2,
    overlayHex: "#FFFFFF",
    overlayOpacity: 0.1,
    effects: [{ type: "LAYER_BLUR", radius: 10, visible: true }]
  });

  const number = await createTextBlock(frame, {
    text: String(slide.slide_number - 1),
    fontFamily: "Inter",
    fontStyle: "Black",
    fallbackStyle: "Bold",
    x: 58,
    y: 142,
    width: 176,
    maxHeight: 300,
    maxSize: 196,
    minSize: 112,
    lineHeight: 0.9,
    color: tokens.accent_navy,
    alignHorizontal: "LEFT"
  });
  number.opacity = 0.06;

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 232,
    y: 172,
    width: 710,
    maxHeight: 260,
    maxSize: 78,
    minSize: 30,
    lineHeight: 1.02,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 232,
    y: 438,
    width: 694,
    maxHeight: 420,
    maxSize: 46,
    minSize: 22,
    lineHeight: 1.18,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await appendLightCreatorFooter(frame, tokens);
}

async function renderLightGrainCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, "violet");
  appendGenericCreatorAvatar(frame, 96, 232, 192, "#FFFFFF", "#161616", "#8086B5");

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 84,
    y: 516,
    width: 880,
    maxHeight: 190,
    maxSize: 88,
    minSize: 32,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 86,
      y: 740,
      width: 808,
      maxHeight: 140,
      maxSize: 34,
      minSize: 16,
      lineHeight: 1.14,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }

  if (slide.supporting_text) {
    await createTextBlock(frame, {
      text: slide.supporting_text,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 86,
      y: 902,
      width: 760,
      maxHeight: 78,
      maxSize: 24,
      minSize: 14,
      lineHeight: 1.14,
      color: "#40455E",
      alignHorizontal: "LEFT"
    });
  }
}

async function renderRetroSwipeCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendRetroTexture(frame, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 82,
    y: 216,
    width: 904,
    maxHeight: 600,
    maxSize: 124,
    minSize: 42,
    lineHeight: 0.98,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  await appendRetroCreatorFooter(frame, tokens, slide.button_label || "Swipe");
}

async function renderRetroSwipeBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendRetroTexture(frame, tokens);

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 82,
    y: 120,
    width: 900,
    maxHeight: 260,
    maxSize: 96,
    minSize: 34,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body_display || slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 82,
    y: 394,
    width: 830,
    maxHeight: 430,
    maxSize: 46,
    minSize: 22,
    lineHeight: 1.18,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  appendRetroArrow(frame, 812, 970, tokens);
  await appendRetroCreatorFooter(frame, tokens, "Next");
}

async function renderRetroSwipeCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);
  appendRetroTexture(frame, tokens);
  appendGenericCreatorAvatar(frame, 364, 224, 188, "#1B1B1B", "#F5F5F5", "#8C9871");

  const badge = figma.createRectangle();
  badge.resize(88, 88);
  badge.cornerRadius = 28;
  badge.x = 496;
  badge.y = 402;
  badge.fills = [solidPaint(tokens.dark_background, 0.72)];
  frame.appendChild(badge);

  await createTextBlock(frame, {
    text: "+",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 522,
    y: 424,
    width: 36,
    maxHeight: 42,
    maxSize: 44,
    minSize: 28,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  await createTextBlock(frame, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 138,
    y: 520,
    width: 804,
    maxHeight: 190,
    maxSize: 84,
    minSize: 32,
    lineHeight: 1.02,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(frame, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 180,
      y: 740,
      width: 720,
      maxHeight: 140,
      maxSize: 34,
      minSize: 16,
      lineHeight: 1.18,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  await appendRetroPillButton(frame, 302, 932, 476, 120, tokens, slide.button_label || "Follow for more");
}

async function renderTwitterCardCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, "peach");
  await appendRemoteImageRect(frame, slide, {
    x: 0,
    y: 0,
    width: 1080,
    height: 1350,
    opacity: 0.28,
    overlayHex: "#FFFFFF",
    overlayOpacity: 0.08,
    effects: [{ type: "LAYER_BLUR", radius: 6, visible: true }]
  });
  await appendTweetCard(frame, 36, 154, 1008, 820, slide, tokens, payload, true);
}

async function renderTwitterCardBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, slide.slide_number % 2 === 0 ? "sky" : "peach");
  await appendRemoteImageRect(frame, slide, {
    x: 0,
    y: 0,
    width: 1080,
    height: 1350,
    opacity: 0.2,
    overlayHex: "#FFFFFF",
    overlayOpacity: 0.08,
    effects: [{ type: "LAYER_BLUR", radius: 8, visible: true }]
  });
  await appendTweetCard(frame, 34, 140, 1012, 900, slide, tokens, payload, false);
}

async function renderTwitterCardCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  appendSoftGradientBackdrop(frame, tokens, "sky");
  await appendTweetCard(frame, 50, 148, 980, 836, slide, tokens, payload, false);

  await createTextBlock(frame, {
    text: slide.supporting_text || "Save or repost the main point.",
    fontFamily: payload.typography.cta_body_family,
    fontStyle: payload.typography.cta_body_style,
    fallbackStyle: "Regular",
    x: 126,
    y: 1030,
    width: 828,
    maxHeight: 72,
    maxSize: 24,
    minSize: 14,
    lineHeight: 1.16,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });
}

function appendNestedSquares(parent, baseNode, tokens) {
  const offsets = [
    { size: 238, x: 50, y: 50, color: tokens.accent_magenta, opacity: 0.76 },
    { size: 166, x: 86, y: 86, color: "#E5208B", opacity: 0.78 },
    { size: 96, x: 121, y: 121, color: "#FF2A99", opacity: 0.82 }
  ];
  for (const offset of offsets) {
    const rect = figma.createRectangle();
    rect.resize(offset.size, offset.size);
    rect.cornerRadius = 20;
    rect.x = baseNode.x + offset.x;
    rect.y = baseNode.y + offset.y;
    rect.fills = [solidPaint(offset.color, offset.opacity)];
    parent.appendChild(rect);
  }
}

function appendAlderMediaStack(frame, x, y, width, height, tokens) {
  const stack = figma.createFrame();
  stack.name = "Alder Media Stack";
  stack.resize(width, height);
  stack.x = x;
  stack.y = y;
  stack.clipsContent = false;
  stack.fills = [];
  stack.strokes = [];
  frame.appendChild(stack);

  const topCard = figma.createRectangle();
  topCard.resize(width, Math.round(height * 0.46));
  topCard.x = 0;
  topCard.y = 0;
  topCard.cornerRadius = 28;
  topCard.fills = [solidPaint(tokens.accent_gold, 0.24)];
  topCard.effects = [dropShadow("#111111", 0.1, 0, 14, 30)];
  stack.appendChild(topCard);

  const bottomCard = figma.createRectangle();
  bottomCard.resize(width, Math.round(height * 0.46));
  bottomCard.x = 0;
  bottomCard.y = Math.round(height * 0.54);
  bottomCard.cornerRadius = 28;
  bottomCard.fills = [solidPaint(tokens.accent_navy, 0.18)];
  bottomCard.effects = [dropShadow("#111111", 0.08, 0, 14, 28)];
  stack.appendChild(bottomCard);

  const topInner = figma.createRectangle();
  topInner.resize(Math.round(width * 0.62), Math.round(height * 0.34));
  topInner.x = Math.round(width * 0.2);
  topInner.y = 48;
  topInner.cornerRadius = 22;
  topInner.fills = [solidPaint(tokens.accent_magenta, 0.88)];
  stack.appendChild(topInner);

  const bottomInner = figma.createRectangle();
  bottomInner.resize(Math.round(width * 0.62), Math.round(height * 0.32));
  bottomInner.x = Math.round(width * 0.14);
  bottomInner.y = Math.round(height * 0.62);
  bottomInner.cornerRadius = 22;
  bottomInner.fills = [solidPaint(tokens.dark_background, 0.9)];
  stack.appendChild(bottomInner);

  const accentBand = figma.createRectangle();
  accentBand.resize(Math.round(width * 0.24), height);
  accentBand.x = width - accentBand.width;
  accentBand.y = 0;
  accentBand.fills = [solidPaint(tokens.accent_orange, 0.16)];
  stack.appendChild(accentBand);
}

function appendTypographyGlowBackdrop(frame, tokens) {
  appendGlow(frame, -40, 824, 460, tokens.accent_gold, 0.24);
  appendGlow(frame, 748, 48, 360, tokens.accent_magenta, 0.26);
  appendGlow(frame, 240, 120, 220, tokens.accent_navy, 0.2);
}

function appendCpDeviceCard(frame, x, y, width, height, tokens) {
  const card = figma.createFrame();
  card.name = "Device Card";
  card.resize(width, height);
  card.x = x;
  card.y = y;
  card.cornerRadius = 28;
  card.clipsContent = true;
  card.fills = [solidPaint("#FFFFFF")];
  card.strokes = [solidPaint("#E8EAEE")];
  card.strokeWeight = 2;
  card.effects = [dropShadow("#111111", 0.12, 0, 18, 40)];
  frame.appendChild(card);

  const rail = figma.createRectangle();
  rail.resize(Math.round(width * 0.24), height);
  rail.x = 0;
  rail.y = 0;
  rail.fills = [solidPaint("#FAFBFC")];
  card.appendChild(rail);

  for (let index = 0; index < 4; index += 1) {
    const marker = figma.createEllipse();
    marker.resize(28, 28);
    marker.x = 18;
    marker.y = 132 + index * 96;
    marker.fills = [solidPaint(index === 1 ? tokens.accent_blue : tokens.accent_gold, index === 1 ? 0.9 : 0.65)];
    card.appendChild(marker);
  }

  const devicePanel = figma.createRectangle();
  devicePanel.resize(Math.round(width * 0.5), 164);
  devicePanel.x = Math.round(width * 0.38);
  devicePanel.y = 108;
  devicePanel.cornerRadius = 18;
  devicePanel.fills = [solidPaint(tokens.text_dark)];
  devicePanel.effects = [dropShadow("#111111", 0.18, 0, 12, 28)];
  card.appendChild(devicePanel);

  const deviceImage = figma.createRectangle();
  deviceImage.resize(Math.round(width * 0.5), 124);
  deviceImage.x = Math.round(width * 0.38);
  deviceImage.y = 330;
  deviceImage.cornerRadius = 16;
  deviceImage.fills = [solidPaint(tokens.accent_navy, 0.95)];
  card.appendChild(deviceImage);

  const slider = figma.createRectangle();
  slider.resize(Math.round(width * 0.46), 4);
  slider.x = Math.round(width * 0.34);
  slider.y = height - 82;
  slider.cornerRadius = 999;
  slider.fills = [solidPaint("#D8DEE8")];
  card.appendChild(slider);

  const knob = figma.createEllipse();
  knob.resize(16, 16);
  knob.x = slider.x + Math.round(slider.width * 0.38);
  knob.y = slider.y - 6;
  knob.fills = [solidPaint(tokens.accent_blue)];
  card.appendChild(knob);

  const smallChip = figma.createRectangle();
  smallChip.resize(82, 18);
  smallChip.x = Math.round(width * 0.38);
  smallChip.y = 70;
  smallChip.cornerRadius = 999;
  smallChip.fills = [solidPaint("#F0F4F8")];
  card.appendChild(smallChip);
}

function appendCpAccentDot(frame, x, y, size, hex, opacity) {
  const dot = figma.createEllipse();
  dot.resize(size, size);
  dot.x = x;
  dot.y = y;
  dot.fills = [solidPaint(hex, opacity)];
  frame.appendChild(dot);
}

function appendCpGalleryWall(frame, tokens) {
  const cards = [
    { x: 72, y: 92, w: 248, h: 170, fill: "#FFFFFF" },
    { x: 380, y: 112, w: 260, h: 382, fill: "#FFFFFF" },
    { x: 780, y: 70, w: 230, h: 206, fill: "#FFFFFF" },
    { x: 84, y: 410, w: 246, h: 430, fill: "#FFFFFF" },
    { x: 430, y: 612, w: 236, h: 236, fill: "#FFFFFF" },
    { x: 774, y: 360, w: 248, h: 388, fill: "#FFFFFF" },
  ];

  cards.forEach((item, index) => {
    const card = figma.createRectangle();
    card.resize(item.w, item.h);
    card.x = item.x;
    card.y = item.y;
    card.cornerRadius = 26;
    card.fills = [solidPaint(item.fill)];
    card.effects = [dropShadow("#111111", 0.08, 0, 16, 34)];
    frame.appendChild(card);

    const accent = figma.createRectangle();
    accent.resize(Math.max(44, Math.round(item.w * 0.26)), Math.max(44, Math.round(item.h * 0.2)));
    accent.x = item.x + 24;
    accent.y = item.y + 24;
    accent.cornerRadius = 18;
    accent.fills = [solidPaint(index % 2 === 0 ? tokens.accent_blue : tokens.accent_gold, 0.68)];
    frame.appendChild(accent);
  });
}

async function appendSadekovProfileHeader(frame, topY, tokens, tone) {
  const isLight = tone === "light";
  const headlineColor = isLight ? tokens.text_dark : tokens.text_light;
  const subColor = isLight ? "#454545" : "#D4D4D4";
  const avatar = figma.createEllipse();
  avatar.resize(138, 138);
  avatar.x = 88;
  avatar.y = topY;
  avatar.fills = [solidPaint(isLight ? "#F4F4F4" : tokens.text_light)];
  frame.appendChild(avatar);

  const avatarInner = figma.createEllipse();
  avatarInner.resize(126, 126);
  avatarInner.x = 94;
  avatarInner.y = topY + 6;
  avatarInner.fills = [solidPaint(tokens.accent_blue, 0.28)];
  avatarInner.strokes = [solidPaint(tokens.text_light, 0.86)];
  avatarInner.strokeWeight = 2;
  frame.appendChild(avatarInner);

  const avatarCenter = figma.createEllipse();
  avatarCenter.resize(72, 72);
  avatarCenter.x = 121;
  avatarCenter.y = topY + 33;
  avatarCenter.fills = [solidPaint(tokens.dark_background)];
  frame.appendChild(avatarCenter);

  await createTextBlock(frame, {
    text: "Carousel Studio",
    fontFamily: "Montserrat",
    fontStyle: "Black",
    fallbackStyle: "Bold",
    x: 262,
    y: topY + 16,
    width: 472,
    maxHeight: 70,
    maxSize: 46,
    minSize: 24,
    lineHeight: 1.0,
    color: headlineColor,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: "AI carousel system",
    fontFamily: "Montserrat",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 262,
    y: topY + 74,
    width: 440,
    maxHeight: 46,
    maxSize: 34,
    minSize: 18,
    lineHeight: 1.0,
    color: subColor,
    alignHorizontal: "LEFT"
  });

  const badge = figma.createEllipse();
  badge.resize(56, 56);
  badge.x = 776;
  badge.y = topY + 18;
  badge.fills = [solidPaint(tokens.accent_blue)];
  frame.appendChild(badge);

  await createTextBlock(frame, {
    text: "✓",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 789,
    y: topY + 24,
    width: 30,
    maxHeight: 28,
    maxSize: 30,
    minSize: 18,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });
}

async function appendSadekovFooter(frame, tone) {
  const isLight = tone === "light";
  const line = figma.createRectangle();
  line.resize(959, 2);
  line.x = 60;
  line.y = 1284;
  line.fills = [solidPaint(isLight ? "#8A8A8A" : "#6E6E6E", 0.86)];
  frame.appendChild(line);

  await createTextBlock(frame, {
    text: "@your.handle",
    fontFamily: "Montserrat",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 350,
    y: 1299,
    width: 380,
    maxHeight: 34,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: isLight ? "#5E5E5E" : "#676767",
    alignHorizontal: "CENTER"
  });
}

function appendSadekovArrowCue(frame, tokens, tone) {
  const arrowColor = tone === "light" ? tokens.text_dark : tokens.text_light;
  const shaft = figma.createRectangle();
  shaft.resize(146, 10);
  shaft.x = 792;
  shaft.y = 1030;
  shaft.rotation = -8;
  shaft.cornerRadius = 999;
  shaft.fills = [solidPaint(arrowColor, 0.96)];
  frame.appendChild(shaft);

  const stem = figma.createRectangle();
  stem.resize(12, 92);
  stem.x = 790;
  stem.y = 960;
  stem.rotation = -8;
  stem.cornerRadius = 999;
  stem.fills = [solidPaint(arrowColor, 0.96)];
  frame.appendChild(stem);

  const head = figma.createPolygon();
  head.pointCount = 3;
  head.resize(86, 86);
  head.x = 904;
  head.y = 986;
  head.rotation = 90;
  head.fills = [solidPaint(arrowColor, 0.96)];
  frame.appendChild(head);
}

function appendTypographyToolCards(frame, tokens) {
  appendGlow(frame, 300, 722, 420, tokens.accent_magenta, 0.2);

  const leftCard = figma.createRectangle();
  leftCard.resize(262, 262);
  leftCard.x = 304;
  leftCard.y = 834;
  leftCard.rotation = -16;
  leftCard.cornerRadius = 40;
  leftCard.fills = [solidPaint("#22242A")];
  leftCard.effects = [dropShadow("#000000", 0.26, 0, 18, 38)];
  frame.appendChild(leftCard);

  const leftMark = figma.createRectangle();
  leftMark.resize(108, 108);
  leftMark.x = 384;
  leftMark.y = 904;
  leftMark.rotation = -16;
  leftMark.cornerRadius = 30;
  leftMark.fills = [solidPaint(tokens.accent_blue, 0.86)];
  frame.appendChild(leftMark);

  const rightCard = figma.createRectangle();
  rightCard.resize(300, 300);
  rightCard.x = 548;
  rightCard.y = 876;
  rightCard.rotation = 14;
  rightCard.cornerRadius = 42;
  rightCard.fills = [solidPaint("#1D1E23")];
  rightCard.effects = [dropShadow("#000000", 0.24, 0, 18, 38)];
  frame.appendChild(rightCard);

  const diamond = figma.createPolygon();
  diamond.pointCount = 4;
  diamond.resize(118, 118);
  diamond.x = 640;
  diamond.y = 974;
  diamond.rotation = 14;
  diamond.fills = [solidPaint(tokens.accent_orange)];
  frame.appendChild(diamond);
}

function appendTypographyEditorialCorners(frame, tokens) {
  const leftRibbon = figma.createPolygon();
  leftRibbon.pointCount = 6;
  leftRibbon.resize(240, 420);
  leftRibbon.x = -58;
  leftRibbon.y = 894;
  leftRibbon.rotation = -10;
  leftRibbon.fills = [solidPaint(tokens.accent_gold, 0.94)];
  frame.appendChild(leftRibbon);

  const leftCard = figma.createRectangle();
  leftCard.resize(164, 164);
  leftCard.x = 64;
  leftCard.y = 1032;
  leftCard.rotation = -12;
  leftCard.cornerRadius = 32;
  leftCard.fills = [solidPaint("#FFFFFF")];
  leftCard.effects = [dropShadow("#111111", 0.12, 0, 12, 28)];
  frame.appendChild(leftCard);

  const leftGem = figma.createPolygon();
  leftGem.pointCount = 4;
  leftGem.resize(86, 86);
  leftGem.x = 102;
  leftGem.y = 1072;
  leftGem.rotation = -12;
  leftGem.fills = [solidPaint(tokens.accent_orange)];
  frame.appendChild(leftGem);

  const rightRibbon = figma.createPolygon();
  rightRibbon.pointCount = 5;
  rightRibbon.resize(320, 470);
  rightRibbon.x = 848;
  rightRibbon.y = 860;
  rightRibbon.rotation = 16;
  rightRibbon.fills = [solidPaint(tokens.accent_blue, 0.86)];
  frame.appendChild(rightRibbon);

  const rightCard = figma.createRectangle();
  rightCard.resize(162, 162);
  rightCard.x = 828;
  rightCard.y = 1038;
  rightCard.rotation = 10;
  rightCard.cornerRadius = 34;
  rightCard.fills = [solidPaint("#21232B")];
  frame.appendChild(rightCard);

  const rightChip = figma.createEllipse();
  rightChip.resize(58, 58);
  rightChip.x = 888;
  rightChip.y = 1092;
  rightChip.fills = [solidPaint(tokens.accent_blue)];
  frame.appendChild(rightChip);
}

function appendBottomBar(frame, hex) {
  const bar = figma.createRectangle();
  bar.resize(1080, 20);
  bar.x = 0;
  bar.y = 1330;
  bar.fills = [solidPaint(hex)];
  frame.appendChild(bar);
}

async function createBulletText(frame, text, x, y, width, maxHeight, maxSize, minSize, color) {
  const bullet = figma.createEllipse();
  bullet.resize(16, 16);
  bullet.x = x;
  bullet.y = y + 18;
  bullet.fills = [solidPaint(color)];
  frame.appendChild(bullet);

  await createTextBlock(frame, {
    text,
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: x + 34,
    y,
    width: width - 34,
    maxHeight,
    maxSize,
    minSize,
    lineHeight: 1.22,
    color,
    alignHorizontal: "LEFT"
  });
}

function splitTextForTwoColumns(text, emphasisWords) {
  const cleaned = cleanText(text) || "";
  if (!cleaned) {
    return [
      emphasisWords && emphasisWords[0] ? emphasisWords[0] : "Key point",
      emphasisWords && emphasisWords[1] ? emphasisWords[1] : "Keep it simple"
    ];
  }

  const words = cleaned.split(" ");
  if (words.length < 10) {
    return [
      cleaned,
      emphasisWords && emphasisWords.length ? emphasisWords.slice(0, 2).join(" ") : "Use clear examples"
    ];
  }

  const pivot = Math.max(4, Math.floor(words.length / 2));
  return [
    words.slice(0, pivot).join(" "),
    words.slice(pivot).join(" ")
  ];
}

function appendOrbitRings(parent, circle, strokeHex) {
  [310, 226, 142].forEach((size) => {
    const ring = figma.createEllipse();
    ring.resize(size, size);
    ring.x = circle.x + (circle.width - size) / 2;
    ring.y = circle.y + (circle.height - size) / 2;
    ring.fills = [];
    ring.strokes = [solidPaint(strokeHex, 0.8)];
    ring.strokeWeight = 3;
    parent.appendChild(ring);
  });
}

function appendTriangleSprinkle(parent, colorHex) {
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 4; column += 1) {
      const glyph = figma.createPolygon();
      glyph.pointCount = 3;
      glyph.resize(14, 14);
      glyph.rotation = -90;
      glyph.x = 24 + column * 28;
      glyph.y = 100 + row * 28;
      glyph.fills = [solidPaint(colorHex, row === 0 && column === 0 ? 0.35 : 1)];
      parent.appendChild(glyph);
    }
  }
}

function appendTopAccentBar(frame, tokens) {
  const bar = figma.createRectangle();
  bar.resize(1080, 18);
  bar.x = 0;
  bar.y = 0;
  bar.fills = [solidPaint(tokens.accent_orange)];
  frame.appendChild(bar);

  const corner = figma.createRectangle();
  corner.resize(180, 18);
  corner.x = 900;
  corner.y = 0;
  corner.fills = [solidPaint(tokens.accent_purple)];
  frame.appendChild(corner);
}

async function appendSlideNumberChip(frame, slideNumber, tokens) {
  const chip = figma.createRectangle();
  chip.resize(110, 46);
  chip.cornerRadius = 999;
  chip.x = 84;
  chip.y = 1244;
  chip.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(chip);

  await createTextBlock(frame, {
    text: `0${slideNumber}`,
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 109,
    y: 1252,
    width: 60,
    maxHeight: 28,
    maxSize: 22,
    minSize: 18,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });
}

function appendGlow(frame, x, y, size, hex, opacity) {
  const glow = figma.createEllipse();
  glow.resize(size, size);
  glow.x = x;
  glow.y = y;
  glow.fills = [solidPaint(hex, opacity)];
  glow.effects = [{ type: "LAYER_BLUR", radius: 110, visible: true }];
  frame.appendChild(glow);
}

async function appendRemoteImageRect(frame, slide, options) {
  if (!slide || !slide.image_asset) {
    return null;
  }

  try {
    let image = null;
    if (slide.image_asset.data_base64) {
      image = figma.createImage(decodeBase64(slide.image_asset.data_base64));
    } else if (slide.image_asset.url) {
      image = await figma.createImageAsync(slide.image_asset.url);
    }
    if (!image) {
      return null;
    }
    const rect = figma.createRectangle();
    rect.name = "Slide Image";
    rect.resize(options.width, options.height);
    rect.x = options.x;
    rect.y = options.y;
    rect.cornerRadius = options.cornerRadius || 0;
    rect.fills = [
      {
        type: "IMAGE",
        scaleMode: "FILL",
        imageHash: image.hash
      }
    ];
    if (typeof options.opacity === "number") {
      rect.opacity = options.opacity;
    }
    if (Array.isArray(options.effects)) {
      rect.effects = options.effects;
    }
    frame.appendChild(rect);

    if (options.overlayHex) {
      const overlay = figma.createRectangle();
      overlay.name = "Slide Image Overlay";
      overlay.resize(options.width, options.height);
      overlay.x = options.x;
      overlay.y = options.y;
      overlay.cornerRadius = options.cornerRadius || 0;
      overlay.fills = [solidPaint(options.overlayHex, options.overlayOpacity || 0.12)];
      frame.appendChild(overlay);
    }

    return rect;
  } catch (error) {
    return null;
  }
}

function appendSoftGradientBackdrop(frame, tokens, mode) {
  const base = figma.createRectangle();
  base.resize(1080, 1350);
  base.x = 0;
  base.y = 0;
  base.fills = [solidPaint("#F7F8FD")];
  frame.appendChild(base);

  if (mode === "peach") {
    appendGlow(frame, -60, -20, 620, tokens.accent_gold, 0.42);
    appendGlow(frame, 640, 80, 560, tokens.accent_magenta, 0.28);
    appendGlow(frame, 120, 920, 420, tokens.accent_orange, 0.22);
  } else if (mode === "green") {
    appendGlow(frame, 734, -20, 430, tokens.accent_orange, 0.28);
    appendGlow(frame, 760, -40, 360, "#7CFF8E", 0.32);
    appendGlow(frame, 680, 980, 360, tokens.accent_blue, 0.18);
  } else if (mode === "sky") {
    appendGlow(frame, -110, 90, 520, tokens.accent_purple, 0.18);
    appendGlow(frame, 720, 840, 500, tokens.accent_blue, 0.26);
    appendGlow(frame, 0, 1040, 340, tokens.accent_gold, 0.16);
  } else {
    appendGlow(frame, -120, 80, 560, tokens.accent_gold, 0.14);
    appendGlow(frame, 734, -40, 420, tokens.accent_magenta, 0.3);
    appendGlow(frame, 670, 940, 420, tokens.accent_blue, 0.22);
  }
}

function appendGenericCreatorAvatar(frame, x, y, size, outerHex, innerHex, rimHex) {
  const outer = figma.createEllipse();
  outer.resize(size, size);
  outer.x = x;
  outer.y = y;
  outer.fills = [solidPaint(outerHex)];
  frame.appendChild(outer);

  const rim = figma.createEllipse();
  rim.resize(size - 10, size - 10);
  rim.x = x + 5;
  rim.y = y + 5;
  rim.strokes = [solidPaint(rimHex || "#D9D9D9")];
  rim.strokeWeight = 2;
  rim.fills = [solidPaint(outerHex)];
  frame.appendChild(rim);

  const inner = figma.createEllipse();
  inner.resize(Math.round(size * 0.68), Math.round(size * 0.68));
  inner.x = x + Math.round(size * 0.16);
  inner.y = y + Math.round(size * 0.16);
  inner.fills = [solidPaint(innerHex)];
  frame.appendChild(inner);
}

async function appendMonoCreatorFooter(frame, tokens, tone, withDivider) {
  const isLight = tone === "light";
  if (withDivider) {
    const divider = figma.createRectangle();
    divider.resize(940, 3);
    divider.x = 70;
    divider.y = 1150;
    divider.fills = [solidPaint(isLight ? tokens.text_light : "#D8D8D8", isLight ? 0.38 : 0.82)];
    frame.appendChild(divider);
  }

  appendGenericCreatorAvatar(frame, 52, 1200, 82, isLight ? "#FAFAFA" : "#0F0F0F", isLight ? "#1F1F1F" : "#EFEFEF", isLight ? "#E8E8E8" : "#666666");

  await createTextBlock(frame, {
    text: "Your Brand",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 150,
    y: 1208,
    width: 260,
    maxHeight: 30,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: isLight ? tokens.text_light : tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: "@your_handle",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 150,
    y: 1242,
    width: 260,
    maxHeight: 26,
    maxSize: 18,
    minSize: 12,
    lineHeight: 1.0,
    color: isLight ? "#F4F4F4" : "#555555",
    alignHorizontal: "LEFT"
  });
}

async function appendLightCreatorFooter(frame, tokens) {
  appendGenericCreatorAvatar(frame, 54, 1186, 88, "#0F0F10", "#F4F4F4", "#8B91C2");

  await createTextBlock(frame, {
    text: "Written by",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 160,
    y: 1202,
    width: 210,
    maxHeight: 22,
    maxSize: 18,
    minSize: 12,
    lineHeight: 1.0,
    color: "#636475",
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: "Your Brand",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 160,
    y: 1232,
    width: 280,
    maxHeight: 28,
    maxSize: 22,
    minSize: 14,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  const chip = figma.createEllipse();
  chip.resize(88, 88);
  chip.x = 930;
  chip.y = 1186;
  chip.fills = [solidPaint(tokens.accent_navy)];
  frame.appendChild(chip);

  await createTextBlock(frame, {
    text: "›",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 953,
    y: 1198,
    width: 42,
    maxHeight: 44,
    maxSize: 44,
    minSize: 22,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });
}

function appendRetroTexture(frame, tokens) {
  appendGlow(frame, 760, 1030, 420, tokens.accent_blue, 0.12);
  appendGlow(frame, -120, 980, 420, tokens.accent_magenta, 0.08);

  for (let index = 0; index < 12; index += 1) {
    const speck = figma.createEllipse();
    const size = 6 + (index % 3) * 4;
    speck.resize(size, size);
    speck.x = 80 + index * 78;
    speck.y = 60 + (index % 4) * 74;
    speck.fills = [solidPaint(tokens.text_light, 0.08)];
    frame.appendChild(speck);
  }
}

async function appendRetroCreatorFooter(frame, tokens, buttonLabel) {
  const divider = figma.createRectangle();
  divider.resize(928, 3);
  divider.x = 76;
  divider.y = 1132;
  divider.fills = [solidPaint(tokens.text_light, 0.26)];
  frame.appendChild(divider);

  appendGenericCreatorAvatar(frame, 76, 1176, 82, "#121212", "#F2F2F2", "#A3AF8F");

  await createTextBlock(frame, {
    text: "Your Brand",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 178,
    y: 1188,
    width: 280,
    maxHeight: 28,
    maxSize: 22,
    minSize: 14,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: "@your_handle",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 178,
    y: 1222,
    width: 220,
    maxHeight: 24,
    maxSize: 16,
    minSize: 12,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });

  await appendRetroPillButton(frame, 744, 1174, 256, 88, tokens, buttonLabel);
}

async function appendRetroPillButton(frame, x, y, width, height, tokens, label) {
  const pill = figma.createRectangle();
  pill.resize(width, height);
  pill.x = x;
  pill.y = y;
  pill.cornerRadius = 24;
  pill.fills = [solidPaint(tokens.accent_gold)];
  frame.appendChild(pill);

  await createTextBlock(frame, {
    text: label,
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: x + 24,
    y: y + 24,
    width: width - 48,
    maxHeight: 36,
    maxSize: 28,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });
}

function appendRetroArrow(frame, x, y, tokens) {
  const shaft = figma.createRectangle();
  shaft.resize(110, 10);
  shaft.x = x;
  shaft.y = y;
  shaft.rotation = -6;
  shaft.cornerRadius = 999;
  shaft.fills = [solidPaint(tokens.text_light, 0.92)];
  frame.appendChild(shaft);

  const head = figma.createPolygon();
  head.pointCount = 3;
  head.resize(74, 74);
  head.x = x + 88;
  head.y = y - 32;
  head.rotation = 88;
  head.fills = [solidPaint(tokens.text_light, 0.92)];
  frame.appendChild(head);
}

async function appendTweetCard(frame, x, y, width, height, slide, tokens, payload, isCover) {
  const card = figma.createFrame();
  card.name = "Tweet Card";
  card.resize(width, height);
  card.x = x;
  card.y = y;
  card.cornerRadius = 28;
  card.fills = [solidPaint("#FFFFFF")];
  card.strokes = [solidPaint("#E7EDF3")];
  card.strokeWeight = 2;
  card.effects = [dropShadow("#111111", 0.12, 0, 20, 44)];
  frame.appendChild(card);

  appendGenericCreatorAvatar(card, 34, 34, 72, "#111111", "#F5F5F5", "#D8E7F9");

  await createTextBlock(card, {
    text: "Your Brand",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 126,
    y: 46,
    width: 320,
    maxHeight: 26,
    maxSize: 24,
    minSize: 16,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(card, {
    text: "@your_handle",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 126,
    y: 78,
    width: 220,
    maxHeight: 22,
    maxSize: 18,
    minSize: 12,
    lineHeight: 1.0,
    color: "#7A7F88",
    alignHorizontal: "LEFT"
  });

  const verify = figma.createEllipse();
  verify.resize(18, 18);
  verify.x = 332;
  verify.y = 50;
  verify.fills = [solidPaint(tokens.accent_blue)];
  card.appendChild(verify);

  const icon = figma.createEllipse();
  icon.resize(30, 30);
  icon.x = width - 68;
  icon.y = 48;
  icon.fills = [solidPaint(tokens.accent_blue)];
  icon.opacity = 0.2;
  card.appendChild(icon);

  await createTextBlock(card, {
    text: slide.headline_display || slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 42,
    y: 142,
    width: width - 84,
    maxHeight: isCover ? 270 : 240,
    maxSize: isCover ? 60 : 54,
    minSize: 24,
    lineHeight: 1.12,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  if (slide.body_display || slide.body) {
    await createTextBlock(card, {
      text: slide.body_display || slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 42,
      y: isCover ? Math.round(height * 0.45) : Math.round(height * 0.48),
      width: width - 84,
      maxHeight: Math.round(height * 0.18),
      maxSize: 40,
      minSize: 18,
      lineHeight: 1.18,
      color: tokens.text_dark,
      alignHorizontal: "LEFT"
    });
  }

  await createTextBlock(card, {
    text: "12:30 PM · Apr 21, 2021 · Web App",
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: 42,
    y: height - 148,
    width: width - 84,
    maxHeight: 26,
    maxSize: 18,
    minSize: 12,
    lineHeight: 1.0,
    color: "#8A9099",
    alignHorizontal: "LEFT"
  });

  const dividerTop = figma.createRectangle();
  dividerTop.resize(width - 84, 2);
  dividerTop.x = 42;
  dividerTop.y = height - 102;
  dividerTop.fills = [solidPaint("#EAECEF")];
  card.appendChild(dividerTop);

  const dividerBottom = figma.createRectangle();
  dividerBottom.resize(width - 84, 2);
  dividerBottom.x = 42;
  dividerBottom.y = height - 28;
  dividerBottom.fills = [solidPaint("#EAECEF")];
  card.appendChild(dividerBottom);

  for (let index = 0; index < 4; index += 1) {
    const action = figma.createEllipse();
    action.resize(26, 26);
    action.x = 122 + index * Math.round((width - 244) / 3);
    action.y = height - 72;
    action.strokes = [solidPaint("#7F8791")];
    action.strokeWeight = 2;
    action.fills = [];
    card.appendChild(action);
  }
}

function isTypographySignal(payload) {
  return payload && payload.style_recipe === "typography_signal_glow_v1";
}

function isCpSplit(payload) {
  return payload && payload.style_recipe === "cp_split_minimal_statement_v1";
}

function isAlderSplitRight(payload) {
  return payload && payload.style_recipe === "alder_split_media_right_v1";
}

function isAlderSplitLeft(payload) {
  return payload && payload.style_recipe === "alder_split_media_left_v1";
}

function isAlderTextOnly(payload) {
  return payload && payload.style_recipe === "alder_text_only_air_v1";
}

function isCpLongform(payload) {
  return payload && payload.style_recipe === "cp_split_longform_v1";
}

function isCpGallery(payload) {
  return payload && payload.style_recipe === "cp_gallery_wall_v1";
}

function isSadekovBlackProfile(payload) {
  return payload && payload.style_recipe === "sadekov_black_profile_minimal_v1";
}

function isSadekovWhiteProfile(payload) {
  return payload && payload.style_recipe === "sadekov_white_profile_minimal_v1";
}

function isTypographyEditorialLight(payload) {
  return payload && payload.style_recipe === "typography_editorial_light_v1";
}

function isCreatorMonoMinimal(payload) {
  return payload && payload.style_recipe === "creator_mono_minimal_v1";
}

function isLightGrainGlow(payload) {
  return payload && [
    "light_grain_glow_v1",
    "pastel_arrow_editorial_v1",
    "placeholder_media_glow_v1"
  ].includes(payload.style_recipe);
}

function isRetroSwipeCreator(payload) {
  return payload && [
    "retro_swipe_creator_v1",
    "social_proof_linkedin_v1",
    "profile_circle_pop_v1"
  ].includes(payload.style_recipe);
}

function isTwitterCardSoft(payload) {
  return payload && [
    "twitter_card_soft_v1",
    "device_mockup_gradient_v1"
  ].includes(payload.style_recipe);
}

function cleanText(value) {
  if (typeof value !== "string") {
    return null;
  }
  var trimmed = value.trim().replace(/\s+/g, " ");
  return trimmed ? trimmed : null;
}

async function appendFooterSignal(frame, label, x, y, align) {
  await appendFooterSignalTone(frame, label, x, y, align, "#FFFFFF");
}

async function appendFooterSignalTone(frame, label, x, y, align, colorHex) {
  const vertical = figma.createRectangle();
  vertical.resize(4, 110);
  vertical.x = x;
  vertical.y = y - 32;
  vertical.fills = [solidPaint(colorHex, 0.96)];
  frame.appendChild(vertical);

  const dot = figma.createEllipse();
  dot.resize(22, 22);
  dot.x = x - 11;
  dot.y = y + 70;
  dot.fills = [solidPaint(colorHex)];
  frame.appendChild(dot);

  const elbow = figma.createRectangle();
  elbow.resize(36, 4);
  elbow.x = align === "right" ? x - 36 : x;
  elbow.y = y - 32;
  elbow.fills = [solidPaint(colorHex, 0.96)];
  frame.appendChild(elbow);

  await createTextBlock(frame, {
    text: label,
    fontFamily: "Inter",
    fontStyle: "Regular",
    fallbackStyle: "Regular",
    x: align === "center" ? x + 20 : align === "right" ? x - 230 : x + 20,
    y: y - 70,
    width: 220,
    maxHeight: 50,
    maxSize: 28,
    minSize: 20,
    lineHeight: 1.0,
    color: colorHex,
    alignHorizontal: align === "right" ? "RIGHT" : "LEFT"
  });
}

async function createTextBlock(parent, options) {
  const node = figma.createText();
  parent.appendChild(node);

  const font = await loadPreferredFont(options.fontFamily, options.fontStyle, options.fallbackStyle);
  const align = options.alignHorizontal || "LEFT";
  let fontSize = options.maxSize;
  const minSize = options.minSize || 18;
  const lineHeight = options.lineHeight || 1.2;

  node.fontName = font;
  node.characters = options.text || "";
  node.textAlignHorizontal = align;
  node.textAlignVertical = "TOP";
  node.fills = [solidPaint(options.color)];
  node.textAutoResize = "HEIGHT";
  node.resize(options.width, 100);

  while (fontSize >= minSize) {
    node.fontSize = fontSize;
    node.lineHeight = { unit: "PIXELS", value: Math.round(fontSize * lineHeight) };
    node.resize(options.width, 100);
    if (node.height <= options.maxHeight) {
      break;
    }
    fontSize -= 2;
  }

  while (node.height > options.maxHeight && fontSize > 14) {
    fontSize -= 2;
    node.fontSize = fontSize;
    node.lineHeight = { unit: "PIXELS", value: Math.round(fontSize * lineHeight) };
    node.resize(options.width, 100);
  }

  node.x = options.x;
  node.y = options.y;
  return node;
}

async function loadPreferredFont(family, style, fallbackStyle) {
  const attempts = [];
  if (family && style) {
    attempts.push({ family, style });
  }
  const fallbacks = FONT_FALLBACKS[family] || [];
  for (const fallback of fallbacks) {
    attempts.push({ family, style: fallback });
  }
  if (family && fallbackStyle) {
    attempts.push({ family, style: fallbackStyle });
  }
  attempts.push({ family: "Inter", style: "Bold" });
  attempts.push({ family: "Inter", style: "Regular" });

  for (const candidate of attempts) {
    try {
      await figma.loadFontAsync(candidate);
      return candidate;
    } catch (error) {
      // Try the next font candidate.
    }
  }

  throw new Error(`Unable to load a usable font for ${family || "unknown family"}.`);
}

function encodeBase64(bytes) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let result = "";
  for (let index = 0; index < bytes.length; index += 3) {
    const a = bytes[index];
    const b = index + 1 < bytes.length ? bytes[index + 1] : 0;
    const c = index + 2 < bytes.length ? bytes[index + 2] : 0;
    const triple = (a << 16) | (b << 8) | c;

    result += alphabet[(triple >> 18) & 63];
    result += alphabet[(triple >> 12) & 63];
    result += index + 1 < bytes.length ? alphabet[(triple >> 6) & 63] : "=";
    result += index + 2 < bytes.length ? alphabet[triple & 63] : "=";
  }
  return result;
}

function decodeBase64(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function uniquePageName(baseName) {
  const existing = new Set(figma.root.children.map((page) => page.name));
  if (!existing.has(baseName)) {
    return baseName;
  }
  let counter = 2;
  while (existing.has(`${baseName} (${counter})`)) {
    counter += 1;
  }
  return `${baseName} (${counter})`;
}

function setSolidFill(node, hex) {
  node.fills = [solidPaint(hex)];
}

function solidPaint(hex, opacity) {
  const { r, g, b } = hexToRgb(hex);
  const paint = {
    type: "SOLID",
    color: { r: r / 255, g: g / 255, b: b / 255 }
  };
  if (typeof opacity === "number") {
    paint.opacity = opacity;
  }
  return paint;
}

function dropShadow(hex, opacity, x, y, blur) {
  const { r, g, b } = hexToRgb(hex);
  return {
    type: "DROP_SHADOW",
    color: { r: r / 255, g: g / 255, b: b / 255, a: opacity },
    offset: { x, y },
    radius: blur,
    spread: 0,
    visible: true,
    blendMode: "NORMAL"
  };
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((character) => character + character).join("")
    : normalized;
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16)
  };
}
