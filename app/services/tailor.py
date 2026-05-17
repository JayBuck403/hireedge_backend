import json
from app.core.config import claude, MODEL
from app.models.schemas import CVProfile, JobDetails

TAILOR_PROMPT = """
You are an expert CV tailoring specialist. Your job is to rewrite the candidate's CV profile to be optimally tailored for the specific job below.

RULES:
- Return ONLY a valid JSON object matching the exact same schema as the input profile. No preamble, no markdown backticks.
- Rewrite the summary to speak directly to this role and company.
- Rewrite experience bullets to emphasise the most relevant skills and achievements for this job.
- Reorder experience bullets so the most relevant ones come first within each role.
- Add a strong achievements block (3-4 items) that front-loads the candidate's best proof points for this specific role.
- Update role_label to match the job title being applied for.
- Do NOT fabricate experience or skills the candidate does not have.
- Keep all factual information (dates, organisations, qualifications) exactly as provided.
- Write in a professional, confident, active voice.

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION:
{job_description}

REQUIREMENTS:
{requirements}

CANDIDATE PROFILE (JSON):
{profile}
"""

COVER_LETTER_PROMPT = """
You are an expert cover letter writer. Write a compelling, professional cover letter for the candidate applying to this role.

RULES:
- Return ONLY the cover letter body text. No subject line, no date, no address blocks — just the paragraphs.
- 4 paragraphs maximum. Each paragraph 3-4 sentences.
- Paragraph 1: Strong opening that references the specific role and company. Show genuine interest.
- Paragraph 2: Most relevant experience — make a direct connection between candidate background and role requirements.
- Paragraph 3: Unique angle — what makes this candidate stand out beyond the obvious. Address any potential concerns proactively (timezone, career change, etc.).
- Paragraph 4: Confident close. Express readiness, mention the assessment/next steps, and invite further conversation.
- Tone: Professional but human. Not stiff. Not sycophantic.
- Do NOT use phrases like "I am writing to express my interest" or "I believe I would be a great fit".

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION: {job_description}

CANDIDATE PROFILE:
Name: {name}
Role: {role_label}
Summary: {summary}
Key Experience: {experience_summary}
"""

async def tailor_cv(profile: CVProfile, job: JobDetails) -> CVProfile:
    """Tailor a CV profile to a specific job using Claude Sonnet."""

    profile_dict = profile.model_dump()

    response = claude.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": TAILOR_PROMPT.format(
                job_title=job.title,
                company=job.company,
                job_description=job.description,
                requirements="\n".join(f"- {r}" for r in job.requirements),
                profile=json.dumps(profile_dict, indent=2)
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

    # Normalize achievements — Claude sometimes returns plain strings
    if "achievements" in data:
        normalized = []
        for a in data["achievements"]:
            if isinstance(a, str):
                normalized.append({"title": a[:60], "detail": a})
            elif isinstance(a, dict):
                normalized.append(a)
        data["achievements"] = normalized

    # Normalize experience bullets — ensure they're lists of strings
    if "experience" in data:
        for exp in data["experience"]:
            if isinstance(exp, dict) and "bullets" in exp:
                exp["bullets"] = [str(b) for b in exp["bullets"]]

    return CVProfile(**data)


async def generate_cover_letter(profile: CVProfile, job: JobDetails) -> str:
    """Generate a tailored cover letter for the candidate."""

    # Summarise top 3 experience items for the prompt
    exp_summary = "\n".join([
        f"- {e.title} at {e.org} ({e.date}): {e.bullets[0] if e.bullets else ''}"
        for e in profile.experience[:3]
    ])

    response = claude.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": COVER_LETTER_PROMPT.format(
                job_title=job.title,
                company=job.company,
                job_description=job.description,
                name=profile.name,
                role_label=profile.role_label,
                summary=profile.summary,
                experience_summary=exp_summary,
            )
        }]
    )

    return response.content[0].text.strip()
