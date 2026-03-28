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
  if (!message || message.type !== "render-payload") {
    return;
  }

  try {
    const payload = normalizePayload(message.payload);
    figma.ui.postMessage({ type: "status", message: "Rendering carousel..." });
    const result = await renderCarousel(payload);
    figma.notify(`Rendered ${payload.job_id} into ${result.page_name}`);
    figma.ui.postMessage({ type: "render-complete", result });
  } catch (error) {
    const text = error instanceof Error ? error.message : String(error);
    figma.notify(text, { error: true });
    figma.ui.postMessage({ type: "render-error", message: text });
  }
};

function normalizePayload(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Missing render payload.");
  }
  if (payload.schema_version !== "figma_plugin_payload_v1") {
    throw new Error("Unsupported payload schema version.");
  }
  if (!Array.isArray(payload.slides) || payload.slides.length !== 7) {
    throw new Error("Render payload must contain exactly 7 slides.");
  }
  if (!payload.job_id) {
    throw new Error("Render payload is missing job_id.");
  }

  return {
    ...payload,
    canvas: { ...DEFAULT_CANVAS, ...(payload.canvas || {}) },
    style_tokens: { ...DEFAULT_TOKENS, ...(payload.style_tokens || {}) },
    typography: { ...DEFAULT_TYPOGRAPHY, ...(payload.typography || {}) }
  };
}

async function renderCarousel(payload) {
  const page = figma.createPage();
  page.name = uniquePageName(payload.page_name || `${payload.job_id}-plugin-render`);
  figma.currentPage = page;

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
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);

  const cluster = figma.createFrame();
  cluster.name = "Geometric Cluster";
  cluster.resize(980, 420);
  cluster.x = 70;
  cluster.y = 790;
  cluster.fills = [];
  cluster.strokes = [];
  cluster.clipsContent = false;
  frame.appendChild(cluster);

  const triangle = figma.createPolygon();
  triangle.pointCount = 3;
  triangle.resize(310, 310);
  triangle.rotation = 180;
  triangle.x = 0;
  triangle.y = 80;
  triangle.fills = [solidPaint(tokens.accent_orange)];
  triangle.effects = [dropShadow("#000000", 0.18, 0, 14, 26)];
  cluster.appendChild(triangle);

  const nestedSquare = figma.createRectangle();
  nestedSquare.resize(338, 338);
  nestedSquare.cornerRadius = 30;
  nestedSquare.x = 310;
  nestedSquare.y = 80;
  nestedSquare.fills = [solidPaint(tokens.accent_purple)];
  cluster.appendChild(nestedSquare);
  appendNestedSquares(cluster, nestedSquare, tokens);

  const circle = figma.createEllipse();
  circle.resize(360, 360);
  circle.x = 610;
  circle.y = 78;
  circle.fills = [solidPaint(tokens.accent_blue)];
  circle.effects = [dropShadow("#000000", 0.16, 0, 12, 24)];
  cluster.appendChild(circle);
  appendOrbitRings(cluster, circle, tokens.text_light);
  appendTriangleSprinkle(cluster, tokens.text_light);

  await createTextBlock(frame, {
    text: slide.headline,
    fontFamily: payload.typography.cover_family,
    fontStyle: payload.typography.cover_style,
    fallbackStyle: "Bold",
    x: 68,
    y: 150,
    width: 930,
    maxHeight: 520,
    maxSize: 154,
    minSize: 86,
    lineHeight: 1.0,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderEditorialBodySlide(frame, slide, payload) {
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
    text: slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 138,
    y: 92,
    width: 820,
    maxHeight: 190,
    maxSize: 74,
    minSize: 48,
    lineHeight: 1.1,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 108,
    y: 320,
    width: 870,
    maxHeight: 670,
    maxSize: 42,
    minSize: 28,
    lineHeight: 1.45,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderMaskBandBodySlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.light_background);

  const band = figma.createRectangle();
  band.resize(320, 1350);
  band.x = 0;
  band.y = 0;
  band.fills = [solidPaint(tokens.text_dark)];
  frame.appendChild(band);

  for (let index = 0; index < 3; index += 1) {
    const slot = figma.createEllipse();
    slot.resize(96, 96);
    slot.x = 88;
    slot.y = 850 + index * 120;
    slot.strokes = [solidPaint(tokens.text_light, 0.65)];
    slot.strokeWeight = 8;
    slot.fills = [solidPaint(tokens.light_background)];
    frame.appendChild(slot);
  }

  await appendSlideNumberChip(frame, slide.slide_number, tokens);

  await createTextBlock(frame, {
    text: slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 382,
    y: 120,
    width: 600,
    maxHeight: 230,
    maxSize: 72,
    minSize: 48,
    lineHeight: 1.08,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 382,
    y: 390,
    width: 600,
    maxHeight: 760,
    maxSize: 40,
    minSize: 27,
    lineHeight: 1.42,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });
}

async function renderSpotlightBodySlide(frame, slide, payload) {
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
    text: slide.headline,
    fontFamily: payload.typography.body_heading_family,
    fontStyle: payload.typography.body_heading_style,
    fallbackStyle: "Bold",
    x: 88,
    y: 118,
    width: 860,
    maxHeight: 220,
    maxSize: 72,
    minSize: 48,
    lineHeight: 1.08,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: slide.body || "",
    fontFamily: payload.typography.body_family,
    fontStyle: payload.typography.body_style,
    fallbackStyle: "Regular",
    x: 88,
    y: 372,
    width: 860,
    maxHeight: 450,
    maxSize: 40,
    minSize: 28,
    lineHeight: 1.4,
    color: tokens.text_dark,
    alignHorizontal: "LEFT"
  });

  await createTextBlock(frame, {
    text: "Keep this point in rotation",
    fontFamily: "Inter",
    fontStyle: "Semi Bold",
    fallbackStyle: "Bold",
    x: 126,
    y: 1008,
    width: 828,
    maxHeight: 74,
    maxSize: 34,
    minSize: 24,
    lineHeight: 1.1,
    color: tokens.text_light,
    alignHorizontal: "LEFT"
  });
}

async function renderCtaSlide(frame, slide, payload) {
  const tokens = payload.style_tokens;
  setSolidFill(frame, tokens.dark_background);

  appendGlow(frame, 70, 900, 360, tokens.accent_gold, 0.28);
  appendGlow(frame, 770, 140, 320, tokens.accent_magenta, 0.24);

  await createTextBlock(frame, {
    text: slide.headline,
    fontFamily: payload.typography.cta_heading_family,
    fontStyle: payload.typography.cta_heading_style,
    fallbackStyle: "Bold",
    x: 110,
    y: 320,
    width: 860,
    maxHeight: 210,
    maxSize: 98,
    minSize: 58,
    lineHeight: 1.02,
    color: tokens.text_light,
    alignHorizontal: "CENTER"
  });

  if (slide.body) {
    await createTextBlock(frame, {
      text: slide.body,
      fontFamily: payload.typography.cta_body_family,
      fontStyle: payload.typography.cta_body_style,
      fallbackStyle: "Regular",
      x: 110,
      y: 560,
      width: 860,
      maxHeight: 160,
      maxSize: 42,
      minSize: 28,
      lineHeight: 1.3,
      color: tokens.text_light,
      alignHorizontal: "CENTER"
    });
  }

  const pill = figma.createRectangle();
  pill.resize(420, 94);
  pill.x = 330;
  pill.y = 770;
  pill.cornerRadius = 999;
  pill.fills = [solidPaint(tokens.text_light)];
  frame.appendChild(pill);

  await createTextBlock(frame, {
    text: "Open the next step",
    fontFamily: "Inter",
    fontStyle: "Bold",
    fallbackStyle: "Bold",
    x: 350,
    y: 795,
    width: 380,
    maxHeight: 48,
    maxSize: 30,
    minSize: 22,
    lineHeight: 1.0,
    color: tokens.text_dark,
    alignHorizontal: "CENTER"
  });

  await appendFooterSignal(frame, "Like", 86, 1110, "left");
  await appendFooterSignal(frame, "Comment", 248, 1210, "center");
  await appendFooterSignal(frame, "Save", 760, 1110, "right");
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
