from __future__ import annotations

from openai import OpenAI

from carousel_system.config import Settings
from carousel_system.models import CarouselInput, CarouselPlanResponse


PROMPT_VERSION = "baseline_v6"

AUTOMATION_CONTRACT = """Automation constraints:
- Produce exactly 7 slides that validate against the schema.
- Slide 1 is the hook.
- Slides 2 through 6 are the only substantive informational slides.
- Slide 7 is a lightweight CTA placeholder only; the renderer replaces the final CTA copy later.
- Slide 6 must land the final substantive point so the argument feels complete before slide 7.
- Keep slides 2 through 6 mutually distinct; do not repeat the same idea in different words.
- If cta_text is provided, treat it as audience/action context only, not as final slide-7 copy.
- Treat the notes field as high-priority planner guidance. It may contain copy-length instructions, audience constraints, review feedback, or style direction.
- generation_mode may be standard, review, or production. It changes the planning constraints, not the core voice.
- niche_preset and library_item_id, when present, narrow the audience and use case. Align examples, terminology, and specificity to that context.
- Do not mention slide numbers inside headlines or body text.
- Output plain text only inside the JSON fields.
"""

SCRIPT_WRITER_STYLE_GUIDE = """Writing style:
- Keep the original custom-prompt style intact. Only the output container changes.
- The original human-readable format was slide number + TITLE + TEXT. In this automation, map TITLE -> headline and TEXT -> body.
- Treat each slide as a standalone idea block that feels repostable.
- Make each slide polarizing, curiosity-driven, surprising, or provocative without becoming clickbait.
- Prefer non-obvious framing over generic questions or safe consensus takes.
- Avoid banal rhetorical prompts such as "are you with us or against us?"
- Every claim should feel like a complete thought with maximum information density.
- Use concrete details, recognizable situations, examples, insights, or credible facts whenever possible.
- Remove any word that does not carry meaning.
- Do not accuse or shame the reader; instead, introduce a new perspective or break a stereotype.
- If there is a shared enemy such as a system, myth, or stereotype, make it explicit.
- If you mention a solution, keep it realistic, not magical.
- Keep the tone punchy, swipe-friendly, and close to the original custom prompt. Do not recast it into a softer educational explainer voice unless the notes explicitly require that.
- Headlines should be vivid, hooky, and ideally 40 characters or fewer.
- For informational slides, prefer 1 crisp sentence. Use 2 only when needed. Use 3 only if the notes explicitly call for more room. Stay within 160 characters whenever possible.
- The hook should feel bold and debate-worthy, not merely descriptive.
"""

SYSTEM_PROMPT = f"""You are planning Instagram carousel copy.

Return a JSON object that matches the supplied schema.

Rules:
- Produce exactly 7 slides.
- Slide 1 must be a strong hook, not a neutral title.
- Slides 2 through 6 must each communicate one distinct informational point.
- Slide 7 is a CTA placeholder only. The final CTA is injected later by the renderer.
- If a script is provided, preserve its substance while restructuring it.
- If only a topic is provided, infer the full carousel content.
- Preserve the input language unless the user explicitly asked for another language.
- Keep copy concise, specific, and visually usable on slides.
- Avoid bland filler, vague advice, and repeated points.
- Do not use hashtags.
- Do not use markdown.
- Do not use emojis.
- Informational slides must include body text.
- Hook and CTA slides may omit body text.
- For slide 7, leave the body empty.
- For slide 7, do not write a detailed CTA sentence because the renderer replaces it automatically.

{AUTOMATION_CONTRACT}

{SCRIPT_WRITER_STYLE_GUIDE}
"""


def build_user_prompt(job: CarouselInput) -> str:
    library_item_id = job.library_item_id or ""
    niche_preset = job.niche_preset or ""
    topic = job.topic or ""
    script = job.script or ""
    cta_text = job.cta_text or ""
    notes = job.notes or ""
    language = job.language or "infer_from_input"
    return f"""Create a carousel plan using this input:

job_id: {job.job_id}
source: {job.source}
generation_mode: {job.generation_mode}
library_item_id: {library_item_id}
niche_preset: {niche_preset}
aspect_ratio: {job.aspect_ratio}
reference_style: {job.reference_style}
language: {language}
topic: {topic}
script: {script}
cta_text: {cta_text}
notes: {notes}

Return slides with these exact roles and design roles:
1. hook / cover
2. info / body
3. info / body
4. info / body
5. info / body
6. info / body
7. cta / cta

Important:
- Keep the original custom-prompt style and per-slide writing pattern. Only the response shape changes from TITLE/TEXT blocks to headline/body fields.
- Slides 1 through 6 do the real content work.
- Slide 6 should complete the argument before the CTA placeholder.
- Slide 7 is a placeholder only.
- Leave slide 7 body empty.
- Keep slide 7 headline short because the final CTA is injected later.
- Follow notes as planner instructions unless they conflict with the hard slide structure above.
"""


def generate_carousel_plan(settings: Settings, job: CarouselInput) -> CarouselPlanResponse:
    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(job)},
        ],
        response_format=CarouselPlanResponse,
    )
    message = completion.choices[0].message
    if getattr(message, "parsed", None):
        return message.parsed

    refusal = getattr(message, "refusal", None) or "Planner response could not be parsed."
    raise RuntimeError(refusal)
