from __future__ import annotations

from openai import OpenAI

from carousel_system.config import Settings
from carousel_system.models import CarouselInput, CarouselPlanResponse


SYSTEM_PROMPT = """You are planning Instagram carousel copy.

Return a JSON object that matches the supplied schema.

Rules:
- Produce exactly 7 slides.
- Slide 1 is a hook with a strong headline.
- Slides 2 through 6 are informational.
- Slide 7 is a CTA.
- If a script is provided, preserve its substance while restructuring it.
- If only a topic is provided, infer the full carousel content.
- Keep copy concise, useful, and clean enough for a visual carousel.
- Do not use hashtags.
- Do not use markdown.
- Do not use emojis.
- Informational slides must include body text.
- Hook and CTA slides may omit body text.
"""


def build_user_prompt(job: CarouselInput) -> str:
    topic = job.topic or ""
    script = job.script or ""
    cta_text = job.cta_text or ""
    notes = job.notes or ""
    return f"""Create a carousel plan using this input:

job_id: {job.job_id}
aspect_ratio: {job.aspect_ratio}
reference_style: {job.reference_style}
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
