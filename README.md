# CV AI Helper & Interview Preparation Platform

A web application for CV analysis, job description matching, and mock interview practice powered by OpenAI GPT-4o.

## Features

- **CV Upload & Parsing** — upload PDF or TXT resume, auto-extract text and detect sections
- **AI CV Analysis** — get issues, improvement tips, and rewrite suggestions
- **JD Matching** — compare your CV against a job description with a match score and skill gaps
- **Mock Interview** — practice interview chat with per-answer feedback and a final scored report

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend API | FastAPI |
| Database | SQLite + SQLAlchemy (async) |
| AI | OpenAI GPT-4o |
| PDF parsing | pdfplumber |

## Setup

### 1. Clone and set up environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Run the backend

```bash
uvicorn backend.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 4. Run the frontend (separate terminal)

```bash
streamlit run frontend/app.py
# Opens at http://localhost:8501
```

## Usage

1. Go to **Upload CV** — upload your PDF or TXT resume
2. Go to **CV Analysis** — click "Run AI Analysis" for feedback
3. Go to **JD Match** — paste a job description to see your match score
4. Go to **Interview** — configure and start a mock interview session

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cv/upload` | Upload CV file |
| GET | `/api/cv/{id}` | Get CV text and sections |
| POST | `/api/cv/{id}/analyze` | Run AI analysis |
| DELETE | `/api/cv/{id}` | Delete CV |
| POST | `/api/jd` | Submit job description |
| POST | `/api/match` | Match CV against JD |
| POST | `/api/interview/start` | Start interview session |
| POST | `/api/interview/{id}/message` | Send answer, get feedback |
| POST | `/api/interview/{id}/finish` | Get final report |

## Project Structure

```
cv-ai-helper/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── database.py       # Async SQLAlchemy
│   ├── config.py         # Settings (pydantic-settings)
│   ├── models/           # DB models + Pydantic schemas
│   ├── api/              # Route handlers (cv, jd, interview)
│   ├── services/         # Business logic + AI calls
│   └── utils/            # File validation/storage
├── frontend/
│   ├── app.py            # Streamlit landing page
│   ├── api_client.py     # HTTP client wrapper
│   └── pages/            # 4 Streamlit pages
├── uploads/              # Uploaded files (gitignored)
└── requirements.txt
```
