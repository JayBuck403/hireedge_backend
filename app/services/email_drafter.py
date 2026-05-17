"""
Ghostwriting service — generates cover email drafts for high-match jobs.

Prompt logic:
  P1 - Hook: specific to the company/role
  P2 - Proof: links candidate projects to job requirements
  P3 - CTA: confident close with next steps
"""

import json
from app.core.config import claude, MODEL
from app.models.schemas import CVProfile, JobDetails

EMAIL_DRAFT_PROMPT = """
You are an expert ghostwriter for job application emails. Write a concise,
compelling cover email for the candidate who is applying to this role.

RULES:
- Return ONLY a JSON object with keys: "subject", "body". No preamble, no
  markdown backticks.
- "subject" should be a short, professional email subject line.
- "body" should be exactly 3 paragraphs separated by double newlines.
  * Paragraph 1 (The Hook): Reference something specific about the company — a
    recent product launch, expansion, or initiative. Show you've done homework.
  * Paragraph 2 (The Proof): Directly link 2-3 of the candidate's achievements
    or projects to the job requirements. Use concrete numbers.
  * Paragraph 3 (The CTA): Confident close. Express readiness, mention the
    attached CV, and invite a conversation.
- Tone: Professional, confident, and tech-forward. Not stiff or sycophantic.
- Do NOT use cliché openers like "I am writing to express my interest".
- Address the email to the recruiter name provided (or "Hiring Manager" if blank).
- Keep total length under 200 words.

RECRUITER: {recruiter_name}
JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION: {job_description}

CANDIDATE PROFILE:
Name: {name}
Current Role: {role_label}
Summary: {summary}
Key Experience:
{experience_summary}
Key Skills: {skills_summary}
"""


async def generate_email_draft(
    profile: CVProfile,
    job: JobDetails,
    recruiter_name: str = "",
) -> dict:
    """Generate a 3-paragraph cover email draft using Claude."""

    # Summarise top 3 experience items
    exp_summary = "\n".join([
        f"- {e.title} at {e.org} ({e.date}): {e.bullets[0] if e.bullets else ''}"
        for e in profile.experience[:3]
    ])

    # Flatten skills
    all_skills = []
    for sg in profile.skills:
        all_skills.extend(sg.items)
    skills_summary = ", ".join(all_skills[:12])

    recruiter = recruiter_name.strip() or "Hiring Manager"

    response = claude.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": EMAIL_DRAFT_PROMPT.format(
                recruiter_name=recruiter,
                job_title=job.title,
                company=job.company,
                job_description=job.description,
                name=profile.name,
                role_label=profile.role_label,
                summary=profile.summary,
                experience_summary=exp_summary,
                skills_summary=skills_summary,
            )
        }]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    raw = raw.strip()

    data = json.loads(raw)
    return {
        "subject": data.get("subject", f"Application: {job.title} at {job.company}"),
        "body": data.get("body", ""),
        "recruiter_name": recruiter,
    }
