import json
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _now():
    return datetime.now(timezone.utc)


class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sections: Mapped[list["CVSection"]] = relationship(
        "CVSection", back_populates="cv", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="cv")


class CVSection(Base):
    __tablename__ = "cv_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(Integer, ForeignKey("cvs.id"), nullable=False)
    section_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    cv: Mapped["CV"] = relationship("CV", back_populates="sections")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_requirements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="jd")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(Integer, ForeignKey("cvs.id"), nullable=False)
    jd_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="created")  # created/in_progress/finished
    level: Mapped[str] = mapped_column(String(20), default="junior")
    num_questions: Mapped[int] = mapped_column(Integer, default=10)
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cv: Mapped["CV"] = relationship("CV", back_populates="interviews")
    jd: Mapped["JobDescription"] = relationship("JobDescription", back_populates="interviews")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="interview", cascade="all, delete-orphan", order_by="Message.id"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="interview")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interviews.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="messages")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # cv/match/interview
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interview_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("interviews.id"), nullable=True)
    interview: Mapped["Interview | None"] = relationship("Interview", back_populates="reports")
