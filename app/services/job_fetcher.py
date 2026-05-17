import httpx
import json
import re
from app.core.config import claude, MODEL
from app.models.schemas import JobDetails

PARSE_PROMPT_TEMPLATE = """
You are a job description parser. Extract structured information from the job description text below.

Return ONLY a valid JSON object. No preamble, no markdown backticks.

SCHEMA:
{{
  "title": "Job title",
  "company": "Company name",
  "location": "Location (Remote / City)",
  "job_type": "Full-time / Part-time / Contract / Remote",
  "description": "2-3 sentence summary of what the role is about",
  "requirements": ["requirement 1", "requirement 2", "requirement 3"]
}}

JOB DESCRIPTION TEXT:
{text}
"""

async def fetch_job(url: str) -> JobDetails:
    """Fetch a job listing URL and extract structured job details."""

    # Fetch the page
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20.0,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text[:6000]  # Cap to avoid token overrun

    # Parse with Claude
    result = claude.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": PARSE_PROMPT_TEMPLATE.format(text=text)
        }]
    )

    raw = result.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (```json) and last line (```)
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    raw = raw.strip()

    data = json.loads(raw)
    return JobDetails(**data)
