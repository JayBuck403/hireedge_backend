"""
sector_detector.py
Detects job sector from a job description and maps it to the right CV template.
Uses keyword matching first (free), Claude only for ambiguous cases.
"""

SECTOR_KEYWORDS = {
    "conservative": [
        "bank", "banking", "finance", "financial", "investment", "insurance",
        "credit", "loan", "mortgage", "treasury", "audit", "accounting",
        "ecobank", "gcb", "fidelity bank", "stanbic", "absa", "cal bank",
        "actuary", "compliance", "risk management", "aml", "kyc"
    ],
    "impact": [
        "ngo", "non-governmental", "nonprofit", "non-profit", "development",
        "humanitarian", "unicef", "undp", "usaid", "world bank", "giz",
        "mastercard foundation", "oxfam", "care", "save the children",
        "community", "advocacy", "gender", "social impact", "programme officer",
        "monitoring", "evaluation", "m&e", "livelihoods", "capacity building"
    ],
    "formal": [
        "government", "public sector", "ministry", "commission", "authority",
        "ghana revenue", "gra", "lands commission", "electoral commission",
        "civil service", "public service", "municipal", "district assembly",
        "metropolitan", "ghana health service", "ghs", "ghana education service",
        "statutory", "regulatory", "policy", "parliament"
    ],
    "clinical": [
        "nurse", "nursing", "doctor", "physician", "medical", "clinical",
        "hospital", "health", "patient", "pharmacy", "pharmacist", "midwife",
        "lab", "laboratory", "radiology", "surgery", "ward", "anaesthesia",
        "ghana health service", "teaching hospital", "korle bu", "komfo anokye"
    ],
    "modern": [
        "software", "developer", "engineer", "flutter", "react", "python",
        "javascript", "mobile", "web", "app", "api", "cloud", "devops",
        "machine learning", "ai", "data science", "product manager",
        "ux", "ui", "design", "startup", "tech", "agile", "scrum"
    ],
    "technical": [
        "civil engineer", "structural", "mechanical", "electrical engineer",
        "construction", "project engineer", "site engineer", "quantity surveyor",
        "architecture", "surveying", "mining", "petroleum", "oil and gas",
        "newmont", "anglogold", "tullow", "ghana gas"
    ],
    "achievement": [
        "sales", "marketing", "business development", "account manager",
        "commercial", "revenue", "targets", "leads", "pipeline", "crm",
        "brand", "digital marketing", "social media", "advertising",
        "communications", "public relations", "pr"
    ],
    "creative": [
        "graphic designer", "creative director", "art director", "illustrator",
        "photographer", "videographer", "content creator", "journalist",
        "media", "broadcast", "film", "animation", "motion graphics"
    ],
    "academic": [
        "lecturer", "professor", "researcher", "research assistant",
        "teaching assistant", "phd", "postdoctoral", "faculty", "university",
        "college", "academic", "publications", "thesis", "dissertation"
    ],
    "minimal": [
        "hotel", "hospitality", "restaurant", "chef", "front desk",
        "housekeeping", "food and beverage", "guest relations", "tourism",
        "travel", "airline", "cabin crew", "customer service"
    ],
}

TEMPLATE_DISPLAY_NAMES = {
    "conservative": "Banking & Finance",
    "impact": "NGO & Development",
    "formal": "Public Sector",
    "clinical": "Healthcare",
    "modern": "Tech & Startups",
    "technical": "Engineering",
    "achievement": "Sales & Marketing",
    "creative": "Creative & Media",
    "academic": "Academic & Research",
    "minimal": "Hospitality & Services",
}

def detect_template(job_description: str, job_title: str = "") -> str:
    """
    Detect the best CV template for a job based on keyword matching.
    Returns template name string.
    Falls back to 'modern' if no clear match.
    """
    text = f"{job_title} {job_description}".lower()

    scores = {template: 0 for template in SECTOR_KEYWORDS}

    for template, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[template] += 1

    best = max(scores, key=scores.get)

    # Only use the match if it has at least 1 keyword hit
    if scores[best] == 0:
        return "modern"  # safe default

    return best


def get_all_templates() -> list[dict]:
    """Return all available templates with display names."""
    return [
        {"id": k, "name": v}
        for k, v in TEMPLATE_DISPLAY_NAMES.items()
    ]
