# Image Pipeline SOP

## Goal
Add images to the carousel system without making the planner, style engine, or renderer brittle.

## Recommendation
- Default strategy: `stock_first`
- Fallback strategy: `ai_fallback`
- Default provider pair:
  - stock: `pexels`
  - ai generation: `openai_gpt_image`

## Why This Fits The Current Repo
- The current system is strong at text-led layouts, not photo-heavy templates.
- Many approved style families only need one image-heavy slide, usually the hook.
- Stock photography is safer for educational, business, and creator topics because it avoids surreal artifacts and fake-looking faces.
- AI image generation is still useful for abstract hooks, impossible metaphors, and concept visuals where stock search is weak.
- Unsplash is not the best default backend for this repo because its API guidelines require hotlinking the returned image URLs and attribution, which is awkward when the renderer needs to import and restyle images inside Figma.
- Pexels is the cleaner default first pass for downloadable stock search in this workflow.

## Decision Rules

### Image Modes
- `none`
  - no external image is used
  - best for typography-only families and dense educational carousels
- `stock`
  - use stock search only
  - best for real-world topics: people, devices, work, teaching, business, lifestyle
- `ai`
  - use generated images only
  - best for abstract metaphors or impossible scenes
- `hybrid`
  - try stock first, fall back to AI if no candidate passes the relevance threshold
  - recommended default user-facing mode

### Slide Placement Rules
- Hook slide:
  - may use an image if the selected style family supports a media slot
- Info slides:
  - at most one info slide should use a photo by default
  - only use an image on info slides when the family has a true image-plus-text layout
- CTA slide:
  - default to no photo
  - use decorative or abstract imagery only if the family expects it

### Style Compatibility Rules
- These families are image-friendly and may request images:
  - `reference_alder_split_media`
  - `reference_cp_gallery_wall`
  - `reference_twitter_card_soft`
  - `reference_light_grain_glow`
  - `reference_typography_signal`
- These families should usually remain text-led unless explicitly forced:
  - `reference_creator_mono_minimal`
  - `reference_retro_swipe_creator`
  - `reference_alder_text_only`
  - `reference_typography_editorial_light`

## Asset Selection Pipeline
1. Planner produces the 7-slide content plan.
2. Style engine chooses the style family and recipe.
3. Image selector determines:
   - whether images are needed
   - which slides may receive them
   - which source mode to use: `none`, `stock`, `ai`, or `hybrid`
4. Asset search/generation produces one or more candidates per image slot.
5. Candidate scorer chooses the best asset using:
   - topical relevance
   - subject clarity
   - portrait crop viability
   - compatibility with the selected style family
   - safety and professionalism
6. Renderer consumes the chosen image assets and applies style-family-specific treatment:
   - crop
   - mask
   - tint/duotone
   - blur/grain
   - overlay
   - card/embed framing

## Stock Strategy

### Primary Provider
- `pexels`

### Why
- Simpler fit for importing images into Figma for local rendering
- Strong enough search for business, education, work, and lifestyle topics
- Easier default than Unsplash for this app shape

### Query Strategy
- Build queries from:
  - topic
  - hook angle
  - slide role
  - audience hints
- Prefer:
  - portrait orientation when available
  - one clear subject
  - negative space for text overlays
  - clean lighting and non-meme aesthetics

### Rejection Rules
- Reject stock images when:
  - results are generic and visually dead
  - image does not crop well to portrait
  - text overlay area is too busy
  - subject clashes with topic tone
  - multiple people/faces create ambiguity

## AI Generation Strategy

### Primary Provider
- `openai_gpt_image`

### Why
- Already aligned with the current OpenAI-based planning layer
- Official image API supports text-to-image generation and editing
- Official docs support portrait-friendly sizes such as `1024x1536`
- Generated output returns in base64 for GPT image models, which fits local asset persistence

### When To Use AI
- No acceptable stock candidate exists
- The concept is abstract:
  - growth loop
  - information overload
  - hidden friction
  - invisible systems
- The slide needs a conceptual hero visual, not a literal photo

### Prompt Rules
- Never prompt for text inside the image
- Never ask for UI screenshots or interfaces unless the slide is intentionally mockup-driven
- Prompt for composition first:
  - subject
  - mood
  - lighting
  - negative space
  - camera distance
  - palette compatibility
- Add explicit exclusions:
  - no text
  - no watermark
  - no logo
  - no extra hands/fingers
  - no collage unless required by the family

## Storage Rules
- Downloaded/generated image assets belong in `.tmp/image-assets/<job_id>/`
- Keep a metadata JSON per chosen asset:
  - source mode
  - provider
  - query or generation prompt
  - original URL if stock
  - local cached path
  - attribution fields if required
- The canonical job artifact must log which images were selected and why

## Renderer Rules
- The renderer should not place raw images directly without treatment.
- Every image-enabled family must define:
  - placement slot
  - crop behavior
  - overlay/tint behavior
  - fallback if no image is available
- If image acquisition fails, the renderer must degrade to a text-only variant instead of failing the whole job.

## Recommended Implementation Order
1. Add image metadata fields to the job artifact and render payload.
2. Add `pexels` stock search and local asset caching.
3. Add style-family image-slot rules.
4. Add AI fallback with `openai_gpt_image`.
5. Add studio controls:
   - `image_mode`
   - `image_source_preference`
   - `allow_ai_fallback`
6. Add image candidate previews in the studio.

## Current Limitations
- Not implemented yet.
- No provider credentials are configured yet for stock search.
- No image slot definitions exist yet in the current plugin renderer.
