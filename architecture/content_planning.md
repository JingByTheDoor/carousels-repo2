# Content Planning SOP

## Goal
Convert a topic or script into a validated 7-slide carousel plan.

## Fixed structure
- Slide 1: hook
- Slides 2-6: informational
- Slide 7: call to action

## Planning rules
- If the user provides only a topic, generate the full carousel copy.
- If the user provides a script, preserve its substance and restructure it into the fixed 7-slide format.
- Keep the output in the same language as the input unless an explicit language override is provided.
- Copy must stay concise enough for Instagram slide layouts.
- Prefer strong hooks over neutral headings.
- Avoid generic filler phrasing.
- Use a direct, educational tone by default.
- Do not add hashtags, markdown, or emojis.
- CTA should ask for one clear action.
- After planning, the render-payload builder must derive display-safe variants for the renderer instead of passing only raw headline/body text.

## Validation
- There must be exactly 7 slides.
- Slide numbers must be 1 through 7 in order.
- Roles must match the fixed structure.
- Hook and CTA slides may omit body text; informational slides must include body text.

## Failure policy
- If the AI response does not parse into the schema, treat it as a hard failure.
- Record the raw failure message and move the job to `error`.
