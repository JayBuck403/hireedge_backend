import json
from app.core.config import claude, MODEL
from app.models.schemas import CVProfile

EXTRACTION_PROMPT = """
You are a CV data extraction specialist. Extract all information from the raw CV text below and return it as a single valid JSON object matching the exact schema provided.

RULES:
- Return ONLY the JSON object. No preamble, no explanation, no markdown backticks.
- If a field is missing from the CV, use an empty string or empty list.
- For experience bullets, rewrite them to be strong, active, and impactful — not just copied verbatim.
- For role_label, infer the best professional title based on their experience.
- For achievements, extract the 3-4 most impressive things from their CV (awards, notable projects, key stats).
- For summary, write a compelling 3-sentence professional summary based on their experience.

SCHEMA:
{{
  "name": "Full name",
  "role_label": "Professional title / role",
  "email": "email",
  "phone": "phone",
  "location": "city, country",
  "summary": "3-sentence professional summary",
  "extra_contact": [{{"label": "GitHub", "value": "url"}}],
  "skills": [{{"group": "Group name", "items": ["skill1", "skill2"]}}],
  "education": [{{"degree": "degree", "school": "school", "year": "year"}}],
  "languages": [{{"name": "language", "level": "proficiency"}}],
  "achievements": [{{"title": "short title", "detail": "one sentence detail"}}],
  "experience": [
    {{
      "title": "Job title",
      "org": "Organisation",
      "date": "Start – End",
      "bullets": ["Strong action bullet 1", "Strong action bullet 2"]
    }}
  ],
  "extra_sections": []
}}

RAW CV TEXT:
{raw_text}
"""

async def extract_cv(raw_text: str) -> CVProfile:
    """Extract structured CV data from raw text using Claude Sonnet."""

    response = claude.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": EXTRACTION_PROMPT.format(raw_text=raw_text)
        }]
    )

    text = response.content[0].text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    text = text.strip()

    data = json.loads(text)

    # Normalize achievements — Claude sometimes returns plain strings
    if "achievements" in data:
        normalized = []
        for a in data["achievements"]:
            if isinstance(a, str):
                normalized.append({"title": a[:60], "detail": a})
            elif isinstance(a, dict):
                normalized.append(a)
        data["achievements"] = normalized

    return CVProfile(**data)
