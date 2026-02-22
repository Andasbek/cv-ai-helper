from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.db_models import CV, CVSection, JobDescription, Report
from backend.models.schemas import JDCreateRequest, JDCreateResponse, MatchRequest, MatchResponse
from backend.services.jd_matcher import extract_jd_requirements, match_cv_to_jd

router = APIRouter(prefix="/api", tags=["jd"])


@router.post("/jd", response_model=JDCreateResponse)
async def create_jd(req: JDCreateRequest, db: AsyncSession = Depends(get_db)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty")

    requirements = await extract_jd_requirements(req.text)

    jd = JobDescription(text=req.text, extracted_requirements=requirements)
    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    return JDCreateResponse(jd_id=jd.id, extracted_requirements=requirements)


@router.post("/match", response_model=MatchResponse)
async def match_cv_jd(req: MatchRequest, db: AsyncSession = Depends(get_db)):
    cv = await db.get(CV, req.cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    jd = await db.get(JobDescription, req.jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    result = await db.execute(select(CVSection).where(CVSection.cv_id == req.cv_id))
    sections = result.scalars().all()
    sections_dict = {s.section_name: s.content for s in sections}
    if not sections_dict:
        sections_dict = {"full_cv": cv.raw_text}

    match_result = await match_cv_to_jd(sections_dict, jd.extracted_requirements or {})

    report = Report(
        entity_type="match",
        entity_id=req.cv_id,
        report_json={**match_result, "jd_id": req.jd_id},
    )
    db.add(report)
    await db.commit()

    return MatchResponse(**match_result)
