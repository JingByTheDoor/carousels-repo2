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
    max_headline_lines: typeof slide.max_headline_lines === "number" ? slide.max_headline_lines : 4,
    max_body_lines: typeof slide.max_body_lines === "number" ? slide.max_body_lines : 6
  });
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
  return {
    schema_version: "figma_plugin_result_v1",
    job_id: payload.job_id,
    page_name: page.name,
    page_id: page.id,
    file_key: typeof figma.fileKey === "string" ? figma.fileKey : null,
    file_url: typeof figma.fileKey === "string" ? `https://www.figma.com/design/${figma.fileKey}` : null,
    slide_node_ids: nodeIds,
    rendered_at: new Date().toISOString()
  };
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
  if (isTypographySignal(payload)) {
    await renderTypographyEditorialBodySlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitBodySlide(frame, slide, payload, "text-left");
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
  if (isTypographySignal(payload)) {
    await renderTypographyPanelBodySlide(frame, slide, payload);
    return;
  }

  if (isCpSplit(payload)) {
    await renderCpSplitBodySlide(frame, slide, payload, "text-right");
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

async function renderTypographySignalCoverSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);
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

function isTypographySignal(payload) {
  return payload && payload.style_recipe === "typography_signal_glow_v1";
}

function isCpSplit(payload) {
  return payload && payload.style_recipe === "cp_split_minimal_statement_v1";
}

function cleanText(value) {
  if (typeof value !== "string") {
    return null;
  }
  var trimmed = value.trim().replace(/\s+/g, " ");
  return trimmed ? trimmed : null;
}

async function appendFooterSignal(frame, label, x, y, align) {
  const vertical = figma.createRectangle();
  vertical.resize(4, 110);
  vertical.x = x;
  vertical.y = y - 32;
  vertical.fills = [solidPaint("#FFFFFF", 0.96)];
  frame.appendChild(vertical);

  const dot = figma.createEllipse();
  dot.resize(22, 22);
  dot.x = x - 11;
  dot.y = y + 70;
  dot.fills = [solidPaint("#FFFFFF")];
  frame.appendChild(dot);

  const elbow = figma.createRectangle();
  elbow.resize(36, 4);
  elbow.x = align === "right" ? x - 36 : x;
  elbow.y = y - 32;
  elbow.fills = [solidPaint("#FFFFFF", 0.96)];
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
    color: "#FFFFFF",
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
