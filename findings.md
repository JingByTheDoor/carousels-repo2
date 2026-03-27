# Findings

## Initial Discoveries
- Repository state at bootstrap: effectively empty except for `.git/`.
- No existing B.L.A.S.T. memory files were present.
- No implementation files, SOPs, or tools were found.
- Bootstrap scaffold now exists and contains only memory files plus empty `architecture/`, `tools/`, and `.tmp/` directories.

## Discovery Answers
- Desired outcome: automate creation of Instagram carousels.
- Target format: 7 slides total.
- Slide structure:
  - Slide 1: attractive hook
  - Slides 2-6: informational content
  - Slide 7: call to action
- Workflow direction: simple input model of `topic/script in -> carousel out`.
- Integration named so far: Figma MCP.
- Design guidance: use template carousels as examples/reference.

## Constraints
- Do not write scripts in `tools/` until discovery is complete, the data schema is defined, and the blueprint is approved.
- Business logic must be deterministic and encoded in SOPs plus atomic tools.
- Intermediate artifacts belong in `.tmp/`.

## Open Questions
- What is the exact input shape: only a topic, or topic plus a full script, audience, brand, and CTA?
- Where do template carousels live: local files, Figma files, or public URLs?
- What is the final delivery destination: a Figma file, exported images, or both?
- Are there any brand rules for tone, colors, fonts, logos, or prohibited claims?
- Will any other external services be used besides Figma MCP?

## Notes
- The user prompt references both `claude.md` and `gemini.md` for project law. This bootstrap treats `claude.md` as the constitution for rules and invariants, and `gemini.md` as the canonical schema and maintenance log.
