# Архитектура системы

## Общая схема

```
┌─────────────────────────────────────────────────────┐
│                   Браузер пользователя               │
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │          Streamlit Frontend                  │   │
│   │   (:8501)                                   │   │
│   │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│   │  │Upload CV │ │CV Analys.│ │JD Match    │  │   │
│   │  └──────────┘ └──────────┘ └────────────┘  │   │
│   │  ┌──────────────────────────────────────┐  │   │
│   │  │         Interview Chat               │  │   │
│   │  └──────────────────────────────────────┘  │   │
│   │                api_client.py               │   │
│   └──────────────────┬──────────────────────────┘   │
└─────────────────────┼───────────────────────────────┘
                      │ HTTP (requests)
                      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (:8000)                 │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │  api/cv  │  │  api/jd  │  │ api/interview    │  │
│  └────┬─────┘  └────┬─────┘  └────────┬────────┘  │
│       │              │                  │            │
│  ┌────▼─────────────▼──────────────────▼────────┐  │
│  │                 Services                      │  │
│  │  parser  │ segmenter │ cv_analyzer            │  │
│  │  jd_matcher │ interview_service               │  │
│  └────────────────────┬──────────────────────────┘  │
│                       │                              │
│   ┌───────────────────▼────────────────────────┐   │
│   │     SQLAlchemy Async ORM + SQLite           │   │
│   │  cvs │ cv_sections │ job_descriptions       │   │
│   │  interviews │ messages │ reports            │   │
│   └────────────────────────────────────────────┘   │
│                                                     │
│   ┌───────────────────────────────────────────┐    │
│   │         OpenAI GPT-4o API                 │    │
│   │  (cv_analyzer / jd_matcher / interview)   │    │
│   └───────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Слои приложения

### 1. Frontend (Streamlit)

Фронтенд реализован на Streamlit — каждая страница является отдельным `.py` файлом в папке `pages/`. Состояние между страницами передаётся через `st.session_state`.

**Ключевые объекты session_state:**

| Ключ | Тип | Описание |
|------|-----|----------|
| `cv_id` | `int` | ID загруженного CV в БД |
| `cv_sections` | `list[dict]` | Секции CV (name + content) |
| `cv_raw_text` | `str` | Полный текст CV |
| `cv_analysis` | `dict` | Результат AI-анализа CV |
| `jd_id` | `int` | ID сохранённой вакансии |
| `jd_requirements` | `dict` | Извлечённые требования JD |
| `match_result` | `dict` | Результат сопоставления |
| `session_id` | `int` | ID сессии интервью |
| `interview_messages` | `list` | История чата интервью |
| `final_report` | `dict` | Финальный отчёт интервью |

Весь сетевой обмен вынесен в `frontend/api_client.py` — модуль с синхронными `requests`-вызовами к FastAPI.

---

### 2. Backend API (FastAPI)

FastAPI приложение с тремя роутерами:

| Роутер | Префикс | Файл |
|--------|---------|------|
| CV | `/api/cv` | `backend/api/cv.py` |
| JD + Match | `/api` | `backend/api/jd.py` |
| Interview | `/api/interview` | `backend/api/interview.py` |

**Жизненный цикл приложения (`lifespan`):**

```python
@asynccontextmanager
async def lifespan(app):
    await create_tables()   # создание таблиц при старте
    yield
```

**CORS:** разрешены запросы с `http://localhost:8501` (адрес Streamlit).

---

### 3. Services (бизнес-логика)

Каждый сервис — независимый Python-модуль без состояния:

```
parser.py          → extract_text(path) -> str
segmenter.py       → segment_cv(text) -> dict[str, str]
cv_analyzer.py     → analyze_cv(sections) -> dict          [AI]
jd_matcher.py      → extract_jd_requirements(text) -> dict [AI]
                   → match_cv_to_jd(sections, reqs) -> dict [AI]
interview_service.py → generate_interview_plan(...) -> list [AI]
                     → evaluate_answer(q, a) -> dict        [AI]
                     → generate_final_report(transcript) -> dict [AI]
```

AI-сервисы используют `AsyncOpenAI` клиент с `response_format={"type": "json_object"}` для гарантированного получения структурированного JSON.

---

### 4. Database (SQLAlchemy + SQLite)

Используется асинхронный движок (`create_async_engine`) с драйвером `aiosqlite`. В MVP применяется SQLite; для продакшена достаточно сменить `DATABASE_URL` на PostgreSQL с драйвером `asyncpg`.

---

## Потоки данных

### Поток A — Загрузка и парсинг CV

```
Пользователь                 Frontend          Backend                  БД
    │                           │                │                       │
    │ Загружает файл            │                │                       │
    │──────────────────────────►│                │                       │
    │                           │ POST /api/cv/upload                    │
    │                           │───────────────►│                       │
    │                           │                │ save_upload()         │
    │                           │                │ extract_text()        │
    │                           │                │ segment_cv()          │
    │                           │                │ INSERT CV + sections  │
    │                           │                │──────────────────────►│
    │                           │ {cv_id: 1}     │                       │
    │                           │◄───────────────│                       │
    │ Видит секции CV           │                │                       │
    │◄──────────────────────────│                │                       │
```

### Поток B — AI-анализ CV

```
Frontend                       Backend                      OpenAI
    │                             │                            │
    │ POST /api/cv/1/analyze      │                            │
    │────────────────────────────►│                            │
    │                             │ get CV sections from DB    │
    │                             │ build prompt               │
    │                             │ gpt-4o (json_object mode)  │
    │                             │───────────────────────────►│
    │                             │ {issues, tips, rewrites}   │
    │                             │◄───────────────────────────│
    │                             │ INSERT Report              │
    │ {issues, tips, rewrites}    │                            │
    │◄────────────────────────────│                            │
```

### Поток C — JD Matching

```
Frontend             Backend                                  OpenAI
    │                   │                                        │
    │ POST /api/jd       │                                        │
    │──────────────────►│                                        │
    │                   │ extract_jd_requirements() ────────────►│
    │                   │◄───────────────────────────────────────│
    │                   │ INSERT JobDescription                  │
    │ {jd_id, reqs}     │                                        │
    │◄──────────────────│                                        │
    │                   │                                        │
    │ POST /api/match    │                                        │
    │──────────────────►│                                        │
    │                   │ match_cv_to_jd() ─────────────────────►│
    │                   │◄───────────────────────────────────────│
    │ {score, gaps...}  │                                        │
    │◄──────────────────│                                        │
```

### Поток D — Интервью (цикл)

```
Frontend             Backend              OpenAI              БД
    │                   │                    │                  │
    │ POST /start        │                    │                  │
    │──────────────────►│ generate_plan() ──►│                  │
    │                   │◄───────────────────│                  │
    │                   │ INSERT Interview + Message(q1)        │
    │ {session_id, q1}  │                    │                 ─┤
    │◄──────────────────│                    │                  │
    │                   │                    │                  │
    │ POST /{id}/message │                    │                  │
    │ {answer: "..."}   │                    │                  │
    │──────────────────►│ evaluate_answer() ►│                  │
    │                   │◄───────────────────│                  │
    │                   │ INSERT Message(a+feedback+q2)         │
    │ {feedback, q2}    │                    │                 ─┤
    │◄──────────────────│                    │                  │
    │                   │   ... повтор ...   │                  │
    │                   │                    │                  │
    │ POST /{id}/finish  │                    │                  │
    │──────────────────►│ generate_final_report() ─────────────►│
    │                   │◄───────────────────────────────────── │
    │                   │ UPDATE Interview.status = finished    │
    │                   │ INSERT Report                        ─┤
    │ {report}          │                    │                  │
    │◄──────────────────│                    │                  │
```

---

## Диаграмма состояний интервью

```
         ┌──────────────┐
         │   created    │
         └──────┬───────┘
                │ POST /api/interview/start
                ▼
         ┌──────────────┐
         │ in_progress  │◄─── POST /{id}/message (повтор)
         └──────┬───────┘
                │ POST /api/interview/{id}/finish
                ▼
         ┌──────────────┐
         │   finished   │
         └──────────────┘
```

---

## Конфигурация (`backend/config.py`)

Настройки загружаются из файла `.env` через `pydantic-settings`:

```python
class Settings(BaseSettings):
    openai_api_key: str          # Ключ OpenAI API
    database_url: str            # URL подключения к БД
    upload_dir: str              # Папка для файлов
    max_file_size_mb: int        # Лимит размера файла
    backend_url: str             # URL backend для фронтенда
```

Объект `settings` создаётся один раз при импорте и используется во всех сервисах.
