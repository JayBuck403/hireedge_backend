import io
import zipfile
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    ExtractCVRequest, TailorCVRequest, FetchJobRequest,
    GenerateRequest, CVProfile, EmailDraftRequest, EmailDraftResponse,
    JobDetails,
)
from app.services.extractor import extract_cv
from app.services.job_fetcher import fetch_job
from app.services.tailor import tailor_cv, generate_cover_letter
from app.services.renderer import render_cv_pdf, render_cover_letter_pdf
from app.services.email_drafter import generate_email_draft

router = APIRouter()

# ── Health ────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "HireEdge API", "version": "0.1.0"}

# ── Templates ─────────────────────────────────────────────────

@router.get("/templates")
async def get_templates():
    """Return all available CV templates with display names."""
    from app.utils.sector_detector import get_all_templates
    return {"templates": get_all_templates()}

# ── CV Extraction ─────────────────────────────────────────────

@router.post("/cv/extract", response_model=CVProfile)
async def extract_cv_endpoint(request: ExtractCVRequest):
    """
    Extract structured CV profile from raw CV text.
    Flutter sends the raw text extracted from the uploaded PDF/image.
    """
    try:
        profile = await extract_cv(request.raw_text)
        return profile
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/cv/extract-file", response_model=CVProfile)
async def extract_cv_file_endpoint(file: UploadFile = File(...)):
    """
    Extract structured CV profile from an uploaded PDF or TXT file.
    Handles PDF text extraction server-side using PyPDF2.
    """
    try:
        contents = await file.read()

        if file.filename and file.filename.lower().endswith('.pdf'):
            import io
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(contents))
            raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            # Assume plain text
            raw_text = contents.decode("utf-8", errors="ignore")

        if not raw_text.strip():
            raise ValueError("Could not extract text from the uploaded file.")

        profile = await extract_cv(raw_text)
        return profile
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"File extraction failed: {str(e)}")

# ── Job Fetching ──────────────────────────────────────────────

@router.post("/job/fetch")
async def fetch_job_endpoint(request: FetchJobRequest):
    """
    Fetch and parse a job listing from a URL.
    Called when user shares or pastes a job link.
    """
    try:
        from app.utils.sector_detector import detect_template, TEMPLATE_DISPLAY_NAMES
        job = await fetch_job(request.url)
        # Auto-detect best template and attach to response
        recommended = detect_template(job.description, job.title)
        return {
            **job.model_dump(),
            "recommended_template": recommended,
            "recommended_template_name": TEMPLATE_DISPLAY_NAMES.get(recommended, "Modern Pro"),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Job fetch failed: {str(e)}")

# ── CV Tailoring ──────────────────────────────────────────────

@router.post("/cv/tailor", response_model=CVProfile)
async def tailor_cv_endpoint(request: TailorCVRequest):
    """
    Tailor an existing CV profile to a specific job description.
    Returns the tailored CVProfile JSON.
    """
    try:
        from app.models.schemas import JobDetails
        job = JobDetails(
            title=request.job_title,
            company=request.company,
            location="",
            job_type="",
            description=request.job_description,
            requirements=[]
        )
        tailored = await tailor_cv(request.profile, job)
        return tailored
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Tailoring failed: {str(e)}")

# ── PDF Rendering ─────────────────────────────────────────────

@router.post("/cv/render")
async def render_cv_endpoint(request: CVProfile):
    """Render a CVProfile to a PDF. Returns raw PDF bytes."""
    try:
        pdf = render_cv_pdf(request, template="modern")
        return StreamingResponse(
            io.BytesIO(pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cv.pdf"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Render failed: {str(e)}")

# ── Full Pipeline ─────────────────────────────────────────────

@router.post("/generate")
async def generate_endpoint(request: GenerateRequest):
    """
    Full end-to-end pipeline:
    1. Fetch + parse job from URL
    2. Tailor CV profile to job
    3. Generate cover letter
    4. Render CV + cover letter PDFs
    5. Return as ZIP

    This is the core endpoint Flutter calls after user shares a job link.
    """
    try:
        # Step 1 — Fetch job
        job = await fetch_job(request.job_url)

        # Step 2 — Tailor CV
        tailored_profile = await tailor_cv(request.profile, job)

        # Step 3 — Generate cover letter
        cover_letter_body = ""
        if request.include_cover_letter:
            cover_letter_body = await generate_cover_letter(tailored_profile, job)

        # Step 4 — Render PDFs
        cv_pdf = render_cv_pdf(tailored_profile, template=request.template)
        cover_pdf = None
        if request.include_cover_letter and cover_letter_body:
            cover_pdf = render_cover_letter_pdf(
                tailored_profile, cover_letter_body,
                job.title, job.company
            )

        # Step 5 — Bundle as ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            safe_name = tailored_profile.name.replace(" ", "_")
            zf.writestr(f"{safe_name}_CV.pdf", cv_pdf)
            if cover_pdf:
                zf.writestr(f"{safe_name}_CoverLetter.pdf", cover_pdf)
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=hireedge_{safe_name}.zip",
                "X-Job-Title": job.title,
                "X-Company": job.company,
            }
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

# ── Email Draft ───────────────────────────────────────────────

@router.post("/email/draft", response_model=EmailDraftResponse)
async def email_draft_endpoint(request: EmailDraftRequest):
    """
    Generate a cover email draft for a high-match job.
    Uses ghostwriting logic: Hook → Proof → CTA (3 paragraphs).
    """
    try:
        job = JobDetails(
            title=request.job_title,
            company=request.company,
            location="",
            job_type="",
            description=request.job_description,
            requirements=[],
        )
        result = await generate_email_draft(
            profile=request.profile,
            job=job,
            recruiter_name=request.recruiter_name,
        )
        return EmailDraftResponse(**result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Email draft failed: {str(e)}")
