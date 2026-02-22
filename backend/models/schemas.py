from pydantic import BaseModel
from typing import Any


# ── CV ──────────────────────────────────────────────────────────────────────

class CVUploadResponse(BaseModel):
    cv_id: int
    message: str


class CVSectionOut(BaseModel):
    section_name: str
    content: str


class CVDetailResponse(BaseModel):
    cv_id: int
    raw_text: str
    sections: list[CVSectionOut]


class CVAnalysisResponse(BaseModel):
    cv_id: int
    issues: list[str]
    tips: list[str]
    rewrites: list[dict[str, str]]


# ── Job Description ──────────────────────────────────────────────────────────

class JDCreateRequest(BaseModel):
    text: str


class JDCreateResponse(BaseModel):
    jd_id: int
    extracted_requirements: dict[str, Any]


class MatchRequest(BaseModel):
    cv_id: int
    jd_id: int


class MatchResponse(BaseModel):
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]


# ── Interview ────────────────────────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    cv_id: int
    jd_id: int | None = None
    company_info: str | None = None
    level: str = "junior"
    num_questions: int = 10


class InterviewStartResponse(BaseModel):
    session_id: int
    question: str
    question_number: int
    total_questions: int


class InterviewMessageRequest(BaseModel):
    answer: str


class InterviewMessageResponse(BaseModel):
    feedback: str
    next_question: str | None
    question_number: int
    total_questions: int
    is_last: bool


class InterviewFinishResponse(BaseModel):
    session_id: int
    report: dict[str, Any]
