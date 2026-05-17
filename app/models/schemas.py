from pydantic import BaseModel
from typing import Optional

# ── CV Data Models ──────────────────────────────────────────

class ExtraContact(BaseModel):
    label: str
    value: str

class SkillGroup(BaseModel):
    group: str
    items: list[str]

class Education(BaseModel):
    degree: str
    school: str
    year: str

class Language(BaseModel):
    name: str
    level: str

class Achievement(BaseModel):
    title: str
    detail: str = ""

class Experience(BaseModel):
    title: str
    org: str
    date: str
    bullets: list[str]

class CVProfile(BaseModel):
    name: str
    role_label: str
    email: str
    phone: str
    location: str
    summary: str
    extra_contact: list[ExtraContact] = []
    skills: list[SkillGroup] = []
    education: list[Education] = []
    languages: list[Language] = []
    achievements: list[Achievement] = []
    experience: list[Experience] = []
    extra_sections: list = []

# ── Request / Response Models ────────────────────────────────

class ExtractCVRequest(BaseModel):
    raw_text: str  # raw text extracted from uploaded CV PDF/image

class TailorCVRequest(BaseModel):
    profile: CVProfile
    job_description: str
    job_title: str
    company: str
    template: str = "modern"  # modern | classic | one-page

class FetchJobRequest(BaseModel):
    url: str

class JobDetails(BaseModel):
    title: str
    company: str
    location: str
    job_type: str
    description: str
    requirements: list[str]
    matched_skills: list[str] = []

class RenderRequest(BaseModel):
    profile: CVProfile
    template: str = "modern"
    include_cover_letter: bool = True
    job_title: str = ""
    company: str = ""

class GenerateRequest(BaseModel):
    """Full end-to-end request — profile + job URL + template"""
    profile: CVProfile
    job_url: str
    template: str = "modern"
    include_cover_letter: bool = True


class EmailDraftRequest(BaseModel):
    """Request to generate a cover email draft for a job match."""
    profile: CVProfile
    job_title: str
    company: str
    job_description: str = ""
    recruiter_name: str = ""  # Falls back to "Hiring Manager"


class EmailDraftResponse(BaseModel):
    """AI-generated cover email draft."""
    subject: str
    body: str
    recruiter_name: str
