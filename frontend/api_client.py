import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BACKEND_URL}{path}"


def upload_cv(file_bytes: bytes, filename: str) -> dict:
    resp = requests.post(
        _url("/api/cv/upload"),
        files={"file": (filename, file_bytes, _guess_mime(filename))},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def get_cv(cv_id: int) -> dict:
    resp = requests.get(_url(f"/api/cv/{cv_id}"), timeout=30)
    resp.raise_for_status()
    return resp.json()


def analyze_cv(cv_id: int) -> dict:
    resp = requests.post(_url(f"/api/cv/{cv_id}/analyze"), timeout=60)
    resp.raise_for_status()
    return resp.json()


def delete_cv(cv_id: int) -> dict:
    resp = requests.delete(_url(f"/api/cv/{cv_id}"), timeout=30)
    resp.raise_for_status()
    return resp.json()


def create_jd(text: str) -> dict:
    resp = requests.post(_url("/api/jd"), json={"text": text}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def match_cv_jd(cv_id: int, jd_id: int) -> dict:
    resp = requests.post(
        _url("/api/match"),
        json={"cv_id": cv_id, "jd_id": jd_id},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def start_interview(cv_id: int, jd_id: int | None, company_info: str | None, level: str, num_questions: int) -> dict:
    payload = {
        "cv_id": cv_id,
        "jd_id": jd_id,
        "company_info": company_info,
        "level": level,
        "num_questions": num_questions,
    }
    resp = requests.post(_url("/api/interview/start"), json=payload, timeout=90)
    resp.raise_for_status()
    return resp.json()


def send_interview_message(session_id: int, answer: str) -> dict:
    resp = requests.post(
        _url(f"/api/interview/{session_id}/message"),
        json={"answer": answer},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def finish_interview(session_id: int) -> dict:
    resp = requests.post(_url(f"/api/interview/{session_id}/finish"), timeout=90)
    resp.raise_for_status()
    return resp.json()


def _guess_mime(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")
