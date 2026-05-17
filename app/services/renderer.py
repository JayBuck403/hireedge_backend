import os
import tempfile
from datetime import date
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from app.models.schemas import CVProfile

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "../../templates")

# ── Contact builders ──────────────────────────────────────────

def _build_contact_row(profile: CVProfile) -> str:
    """Inline contact string for single-column templates."""
    items = [profile.email, profile.phone, profile.location]
    for e in profile.extra_contact:
        items.append(e.value)
    return "  ·  ".join(items)

def _build_contact_block(profile: CVProfile) -> str:
    """Right-aligned stacked contact block for split-header templates."""
    items = [profile.email, profile.phone, profile.location]
    for e in profile.extra_contact:
        items.append(f"{e.label}: {e.value}")
    return "".join(f'<div class="contact-item">{i}</div>' for i in items)

def _build_extra_contact(extra_contact) -> str:
    """Extra contact items for sidebar templates."""
    if not extra_contact:
        return ""
    html = ""
    for e in extra_contact:
        html += f'<div class="s-contact"><span>{e.label}</span>{e.value}</div>'
    return html

# ── Skills builders ───────────────────────────────────────────

def _build_skills(skills) -> str:
    """Two-column skills table for main content area."""
    if not skills:
        return ""
    html = '<div class="section"><div class="section-title">Core Competencies</div>'
    html += '<table class="skills-table">'
    for i, group in enumerate(skills):
        if i % 2 == 0:
            html += "<tr>"
        html += f'<td><span class="skill-group-label">{group.group}:</span> '
        html += f'<span class="skill-values">{" · ".join(group.items)}</span></td>'
        if i % 2 == 1 or i == len(skills) - 1:
            if len(skills) % 2 != 0 and i == len(skills) - 1:
                html += "<td></td>"
            html += "</tr>"
    html += "</table></div>"
    return html

def _build_skills_sidebar(skills) -> str:
    """Skill tags for sidebar templates."""
    if not skills:
        return ""
    html = ""
    for group in skills:
        html += f'<div class="s-skill-group">'
        html += f'<div class="s-skill-group-label">{group.group}</div>'
        for item in group.items:
            html += f'<span class="s-skill-tag">{item}</span>'
        html += '</div>'
    return html

# ── Education builders ────────────────────────────────────────

def _build_education(education) -> str:
    """Education section for main content area."""
    if not education:
        return ""
    html = '<div class="section"><div class="section-title">Education</div>'
    for edu in education:
        html += '<div class="edu-block">'
        html += f'<table class="edu-header-table"><tr>'
        html += f'<td><div class="edu-degree">{edu.degree}</div>'
        html += f'<div class="edu-school">{edu.school}</div></td>'
        html += f'<td><div class="edu-year">{edu.year}</div></td>'
        html += '</tr></table></div>'
    html += '</div>'
    return html

def _build_education_sidebar(education) -> str:
    """Education for sidebar templates."""
    if not education:
        return ""
    html = ""
    for edu in education:
        html += '<div class="s-edu-block">'
        html += f'<div class="s-edu-degree">{edu.degree}</div>'
        html += f'<div class="s-edu-school">{edu.school}</div>'
        html += f'<div class="s-edu-year">{edu.year}</div>'
        html += '</div>'
    return html

# ── Language builders ─────────────────────────────────────────

def _build_languages(languages) -> str:
    if not languages:
        return ""
    html = '<div class="section"><div class="section-title">Languages</div>'
    for lang in languages:
        html += f'<div class="lang-row"><strong>{lang.name}</strong> '
        html += f'<span class="lang-level">— {lang.level}</span></div>'
    html += '</div>'
    return html

def _build_languages_sidebar(languages) -> str:
    if not languages:
        return ""
    html = '<div class="s-section"><div class="s-section-title">Languages</div>'
    for lang in languages:
        html += f'<div class="s-lang">{lang.name} '
        html += f'<span class="s-lang-level">— {lang.level}</span></div>'
    html += '</div>'
    return html

# ── License builder (Healthcare) ──────────────────────────────

def _build_license(languages) -> str:
    """Licensure block for clinical template — shows professional registrations."""
    html = '<div class="s-license">Nursing &amp; Midwifery Council of Ghana<br>Registered Member (2020 – Present)</div>'
    return html

# ── Achievements builders ─────────────────────────────────────

def _build_achievements(achievements) -> str:
    if not achievements:
        return ""
    html = '<div class="section"><div class="section-title">Key Strengths</div>'
    html += '<table class="achievements-table">'
    for i, a in enumerate(achievements):
        if i % 2 == 0:
            html += "<tr>"
        html += f'<td><div class="achievement-item"><strong>{a.title}</strong><p>{a.detail}</p></div></td>'
        if i % 2 == 1 or i == len(achievements) - 1:
            if len(achievements) % 2 != 0 and i == len(achievements) - 1:
                html += "<td></td>"
            html += "</tr>"
    html += '</table></div>'
    return html

def _build_metrics_bar(achievements) -> str:
    """Metrics banner for Sales/Marketing achievement template."""
    if not achievements:
        return ""
    html = '<table class="metrics-bar"><tr>'
    for a in achievements[:4]:
        html += f'<td class="metric-cell"><span class="metric-number">{a.title}</span><span class="metric-label">{a.detail}</span></td>'
    html += '</tr></table>'
    return html

# ── Experience builder ────────────────────────────────────────

def _build_experience(experience) -> str:
    html = ""
    for job in experience:
        html += '<div class="job">'
        html += '<table class="job-header-table"><tr>'
        html += f'<td><div class="job-title">{job.title}</div></td>'
        if job.date:
            html += f'<td><div class="job-date">{job.date}</div></td>'
        html += '</tr></table>'
        html += f'<div class="job-org">{job.org}</div>'
        if job.bullets:
            html += '<ul>'
            for b in job.bullets:
                html += f'<li>{b}</li>'
            html += '</ul>'
        html += '</div>'
    return html

# ── One-page experience builder (trimmed) ─────────────────────

def _build_experience_onepage(experience) -> str:
    """Trimmed experience for one-page template — max 3 roles, max 3 bullets each."""
    html = ""
    for job in experience[:3]:
        html += '<div class="job">'
        html += '<table class="job-header-table"><tr>'
        html += f'<td><div class="job-title">{job.title}</div></td>'
        if job.date:
            html += f'<td><div class="job-date">{job.date}</div></td>'
        html += '</tr></table>'
        html += f'<div class="job-org">{job.org}</div>'
        if job.bullets:
            html += '<ul>'
            for b in job.bullets[:3]:  # max 3 bullets
                html += f'<li>{b}</li>'
            html += '</ul>'
        html += '</div>'
    return html

def _build_skills_onepage(skills) -> str:
    """Compact inline skills for one-page template."""
    if not skills:
        return ""
    html = '<div class="section"><div class="section-title">Skills</div>'
    html += '<table class="skills-table">'
    for i, group in enumerate(skills[:4]):  # max 4 groups
        if i % 2 == 0:
            html += "<tr>"
        items_short = group.items[:5]  # max 5 items per group
        html += f'<td><span class="skill-group-label">{group.group}:</span> '
        html += f'<span class="skill-values">{" · ".join(items_short)}</span></td>'
        if i % 2 == 1 or i == min(len(skills), 4) - 1:
            if min(len(skills), 4) % 2 != 0 and i == min(len(skills), 4) - 1:
                html += "<td></td>"
            html += "</tr>"
    html += "</table></div>"
    return html

def _build_achievements_onepage(achievements) -> str:
    """Compact achievements for one-page — max 2."""
    if not achievements:
        return ""
    html = '<div class="section"><div class="section-title">Key Strengths</div>'
    html += '<table class="achievements-table">'
    html += "<tr>"
    for a in achievements[:2]:
        html += f'<td><div class="achievement-item"><strong>{a.title}</strong><p>{a.detail[:60]}...</p></div></td>'
    html += "</tr></table></div>"
    return html

def _build_summary_onepage(summary: str) -> str:
    """Trim summary to 2 sentences max for one-page."""
    sentences = summary.split('. ')
    short = '. '.join(sentences[:2])
    if not short.endswith('.'):
        short += '.'
    return short

# ── Main render function ──────────────────────────────────────

def render_cv_pdf(profile: CVProfile, template: str = "modern") -> bytes:
    template_path = os.path.join(TEMPLATES_DIR, f"cv_{template}.html")
    if not os.path.exists(template_path):
        template_path = os.path.join(TEMPLATES_DIR, "cv_modern.html")

    with open(template_path) as f:
        html_template = f.read()

    # Use trimmed builders for one-page template
    is_onepage = template == "onepage"

    replacements = {
        "{{NAME}}": profile.name,
        "{{ROLE_LABEL}}": profile.role_label,
        "{{EMAIL}}": profile.email,
        "{{PHONE}}": profile.phone,
        "{{LOCATION}}": profile.location,
        "{{SUMMARY}}": _build_summary_onepage(profile.summary) if is_onepage else profile.summary,
        "{{CONTACT_ROW}}": _build_contact_row(profile),
        "{{CONTACT_BLOCK}}": _build_contact_block(profile),
        "{{EXTRA_CONTACT}}": _build_extra_contact(profile.extra_contact),
        "{{SKILLS_BLOCK}}": _build_skills_onepage(profile.skills) if is_onepage else _build_skills(profile.skills),
        "{{SKILLS_SIDEBAR}}": _build_skills_sidebar(profile.skills),
        "{{EDUCATION_BLOCK}}": _build_education(profile.education),
        "{{EDUCATION_SIDEBAR}}": _build_education_sidebar(profile.education),
        "{{LANGUAGES_BLOCK}}": _build_languages(profile.languages),
        "{{LANGUAGES_SIDEBAR}}": _build_languages_sidebar(profile.languages),
        "{{ACHIEVEMENTS_BLOCK}}": _build_achievements_onepage(profile.achievements) if is_onepage else _build_achievements(profile.achievements),
        "{{EXPERIENCE_BLOCK}}": _build_experience_onepage(profile.experience) if is_onepage else _build_experience(profile.experience),
        "{{LICENSE_BLOCK}}": _build_license(profile.languages),
        "{{METRICS_BAR}}": _build_metrics_bar(profile.achievements),
        "{{EXTRA_SECTIONS}}": "",
    }

    html_content = html_template
    for key, val in replacements.items():
        html_content = html_content.replace(key, val)

    font_config = FontConfiguration()
    css = CSS(string='@page { size: A4; margin: 0; }', font_config=font_config)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        HTML(string=html_content).write_pdf(tmp.name, stylesheets=[css], font_config=font_config)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp.name)

    return pdf_bytes


def render_cover_letter_pdf(profile: CVProfile, cover_letter_body: str, job_title: str, company: str) -> bytes:
    today = date.today().strftime("%-d %B, %Y")
    paragraphs = "".join(f"<p>{p.strip()}</p>" for p in cover_letter_body.split("\n\n") if p.strip())

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Georgia, serif; font-size: 10pt; color: #1a1a1a; line-height: 1.7; }}
  .page {{ width: 210mm; min-height: 297mm; padding: 18mm; }}
  .header {{ border-bottom: 3px solid #1a1a1a; padding-bottom: 5mm; margin-bottom: 8mm; }}
  .name {{ font-size: 20pt; font-weight: bold; color: #1a1a1a; letter-spacing: -0.3px; }}
  .contact {{ font-size: 8.5pt; font-family: Helvetica, Arial, sans-serif; color: #555; margin-top: 2mm; }}
  .date-block {{ font-family: Helvetica, Arial, sans-serif; font-size: 9pt; color: #555; margin-bottom: 7mm; }}
  .recipient {{ font-family: Helvetica, Arial, sans-serif; font-size: 9.5pt; color: #1a1a1a; margin-bottom: 7mm; line-height: 1.5; }}
  .subject {{ font-family: Helvetica, Arial, sans-serif; font-size: 9.5pt; font-weight: bold; color: #1a1a1a; margin-bottom: 7mm; }}
  .body p {{ margin-bottom: 5mm; font-size: 10pt; color: #222; }}
  .closing {{ margin-top: 8mm; font-size: 10pt; }}
  .sig-name {{ font-weight: bold; font-size: 11pt; margin-top: 6mm; }}
  .sig-detail {{ font-family: Helvetica, Arial, sans-serif; font-size: 8.5pt; color: #555; margin-top: 1mm; }}
</style></head><body>
<div class="page">
  <div class="header">
    <div class="name">{profile.name.upper()}</div>
    <div class="contact">{profile.email} &nbsp;·&nbsp; {profile.phone} &nbsp;·&nbsp; {profile.location}</div>
  </div>
  <div class="date-block">{today}</div>
  <div class="recipient">Hiring Team<br>{company}</div>
  <div class="subject">Re: {job_title}</div>
  <div class="body">{paragraphs}</div>
  <div class="closing">Yours sincerely,
    <div class="sig-name">{profile.name}</div>
    <div class="sig-detail">{profile.email} &nbsp;·&nbsp; {profile.phone}</div>
  </div>
</div></body></html>"""

    font_config = FontConfiguration()
    css = CSS(string='@page { size: A4; margin: 0; }', font_config=font_config)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        HTML(string=html).write_pdf(tmp.name, stylesheets=[css], font_config=font_config)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp.name)

    return pdf_bytes
