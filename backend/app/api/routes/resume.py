from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import io
from app.core.dependencies import get_current_user
from app.models import ProfileResponse, ResumeResponse
from app.db.supabase_client import get_supabase_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

def extract_text_from_pdf(content: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

def extract_text_from_file(content: bytes, filename: str) -> str:
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(content)
    else:
        return content.decode("utf-8", errors="ignore")

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: ProfileResponse = Depends(get_current_user)
):
    if not file.filename.endswith((".txt", ".pdf", ".doc", ".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt, .pdf, .doc, .docx files are supported"
        )
    
    content = await file.read()
    raw_text = extract_text_from_file(content, file.filename)
    
    if len(raw_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from file"
        )
    
    supabase = get_supabase_client()
    
    # Mark existing base resume as non-base
    supabase.table("resumes")\
        .update({"is_base": False})\
        .eq("user_id", str(current_user.id))\
        .eq("is_base", True)\
        .execute()
    
    # Save with properly extracted text
    result = supabase.table("resumes").insert({
        "user_id": str(current_user.id),
        "title": file.filename,
        "raw_text": raw_text,
        "is_base": True
    }).execute()
    
    logger.info(
        f"Resume uploaded | "
        f"user={current_user.email} | "
        f"chars={len(raw_text)}"
    )
    
    return ResumeResponse(**result.data[0])


@router.get("/", response_model=list[ResumeResponse])
async def get_resumes(
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    result = supabase.table("resumes")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("created_at", desc=True)\
        .execute()
    
    return [ResumeResponse(**r) for r in result.data]


@router.get("/base", response_model=ResumeResponse)
async def get_base_resume(
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    result = supabase.table("resumes")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .eq("is_base", True)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No base resume found — please upload one first"
        )
    
    return ResumeResponse(**result.data)