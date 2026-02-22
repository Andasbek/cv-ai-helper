from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.db_models import CV, CVSection, Report
from backend.models.schemas import CVUploadResponse, CVDetailResponse, CVSectionOut, CVAnalysisResponse
from backend.services.parser import extract_text
from backend.services.segmenter import segment_cv
from backend.services.cv_analyzer import analyze_cv
from backend.utils.file_utils import save_upload, delete_file

router = APIRouter(prefix="/api/cv", tags=["cv"])


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Save file to disk (validation happens inside save_upload)
    file_path = await save_upload(file)

    try:
        raw_text = extract_text(file_path)
    except Exception as e:
        delete_file(file_path)
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    if not raw_text.strip():
        delete_file(file_path)
        raise HTTPException(status_code=422, detail="Extracted text is empty. Is the file a scanned image?")

    sections = segment_cv(raw_text)

    cv = CV(file_path=file_path, raw_text=raw_text)
    db.add(cv)
    await db.flush()

    for name, content in sections.items():
        db.add(CVSection(cv_id=cv.id, section_name=name, content=content))

    await db.commit()
    await db.refresh(cv)

    return CVUploadResponse(cv_id=cv.id, message="CV uploaded and parsed successfully.")


@router.get("/{cv_id}", response_model=CVDetailResponse)
async def get_cv(cv_id: int, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    result = await db.execute(select(CVSection).where(CVSection.cv_id == cv_id))
    sections = result.scalars().all()

    return CVDetailResponse(
        cv_id=cv.id,
        raw_text=cv.raw_text,
        sections=[CVSectionOut(section_name=s.section_name, content=s.content) for s in sections],
    )


@router.delete("/{cv_id}")
async def delete_cv(cv_id: int, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    delete_file(cv.file_path)
    await db.delete(cv)
    await db.commit()
    return {"message": "CV deleted successfully"}


@router.post("/{cv_id}/analyze", response_model=CVAnalysisResponse)
async def analyze_cv_endpoint(cv_id: int, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    result = await db.execute(select(CVSection).where(CVSection.cv_id == cv_id))
    sections = result.scalars().all()
    sections_dict = {s.section_name: s.content for s in sections}

    if not sections_dict:
        sections_dict = {"full_cv": cv.raw_text}

    analysis = await analyze_cv(sections_dict)

    report = Report(
        entity_type="cv",
        entity_id=cv_id,
        report_json=analysis,
    )
    db.add(report)
    await db.commit()

    return CVAnalysisResponse(cv_id=cv_id, **analysis)
