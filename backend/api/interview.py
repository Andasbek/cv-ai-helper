from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.db_models import CV, CVSection, JobDescription, Interview, Message, Report
from backend.models.schemas import (
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewMessageRequest,
    InterviewMessageResponse,
    InterviewFinishResponse,
)
from backend.services.interview_service import (
    generate_interview_plan,
    evaluate_answer,
    generate_final_report,
)

router = APIRouter(prefix="/api/interview", tags=["interview"])


async def _get_cv_sections(cv_id: int, db: AsyncSession) -> dict[str, str]:
    cv = await db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    result = await db.execute(select(CVSection).where(CVSection.cv_id == cv_id))
    sections = result.scalars().all()
    if sections:
        return {s.section_name: s.content for s in sections}
    return {"full_cv": cv.raw_text}


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(req: InterviewStartRequest, db: AsyncSession = Depends(get_db)):
    cv_sections = await _get_cv_sections(req.cv_id, db)

    jd_text = None
    if req.jd_id:
        jd = await db.get(JobDescription, req.jd_id)
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")
        jd_text = jd.text

    questions = await generate_interview_plan(
        cv_sections=cv_sections,
        jd_text=jd_text,
        company_info=req.company_info,
        level=req.level,
        num_questions=req.num_questions,
    )

    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate interview questions")

    interview = Interview(
        cv_id=req.cv_id,
        jd_id=req.jd_id,
        status="in_progress",
        level=req.level,
        num_questions=len(questions),
        plan={"questions": questions},
        current_question_index=0,
    )
    db.add(interview)
    await db.flush()

    first_q = questions[0]["text"]
    db.add(Message(interview_id=interview.id, role="assistant", text=first_q))

    await db.commit()
    await db.refresh(interview)

    return InterviewStartResponse(
        session_id=interview.id,
        question=first_q,
        question_number=1,
        total_questions=len(questions),
    )


@router.post("/{session_id}/message", response_model=InterviewMessageResponse)
async def send_message(
    session_id: int,
    req: InterviewMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    interview = await db.get(Interview, session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if interview.status == "finished":
        raise HTTPException(status_code=400, detail="Interview is already finished")

    questions = interview.plan.get("questions", [])
    current_idx = interview.current_question_index
    current_question = questions[current_idx]["text"]

    # Store user answer
    db.add(Message(interview_id=session_id, role="user", text=req.answer))

    # Evaluate the answer
    eval_result = await evaluate_answer(current_question, req.answer)
    feedback = eval_result["feedback"]

    # Store feedback message
    db.add(Message(interview_id=session_id, role="assistant", text=f"[Feedback] {feedback}"))

    # Move to next question
    next_idx = current_idx + 1
    is_last = next_idx >= len(questions)

    next_question = None
    if not is_last:
        next_question = questions[next_idx]["text"]
        db.add(Message(interview_id=session_id, role="assistant", text=next_question))
        interview.current_question_index = next_idx

    await db.commit()

    return InterviewMessageResponse(
        feedback=feedback,
        next_question=next_question,
        question_number=next_idx + 1 if not is_last else len(questions),
        total_questions=len(questions),
        is_last=is_last,
    )


@router.post("/{session_id}/finish", response_model=InterviewFinishResponse)
async def finish_interview(session_id: int, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")

    result = await db.execute(
        select(Message)
        .where(Message.interview_id == session_id)
        .order_by(Message.id)
    )
    messages = result.scalars().all()

    # Build transcript: pair questions with answers
    questions = interview.plan.get("questions", [])
    transcript = []
    q_idx = 0
    i = 0
    msg_list = list(messages)

    while i < len(msg_list) and q_idx < len(questions):
        msg = msg_list[i]
        if msg.role == "assistant" and not msg.text.startswith("[Feedback]"):
            # This is a question
            question_text = msg.text
            answer_text = ""
            feedback_text = ""
            # Look ahead for user answer
            if i + 1 < len(msg_list) and msg_list[i + 1].role == "user":
                answer_text = msg_list[i + 1].text
                i += 1
            # Look ahead for feedback
            if i + 1 < len(msg_list) and msg_list[i + 1].text.startswith("[Feedback]"):
                feedback_text = msg_list[i + 1].text.replace("[Feedback] ", "")
                i += 1
            transcript.append({
                "question": question_text,
                "answer": answer_text,
                "feedback": feedback_text,
                "type": questions[q_idx].get("type", "general") if q_idx < len(questions) else "general",
                "category": questions[q_idx].get("category", "") if q_idx < len(questions) else "",
            })
            q_idx += 1
        i += 1

    if not transcript:
        raise HTTPException(status_code=400, detail="No answers recorded yet")

    report_data = await generate_final_report(transcript)

    interview.status = "finished"
    interview.finished_at = datetime.now(timezone.utc)

    report = Report(
        entity_type="interview",
        entity_id=session_id,
        report_json=report_data,
        interview_id=session_id,
    )
    db.add(report)
    await db.commit()

    return InterviewFinishResponse(session_id=session_id, report=report_data)
