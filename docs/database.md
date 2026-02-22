# Модель данных

## ER-диаграмма

```
┌──────────────────────────┐         ┌──────────────────────────────┐
│           cvs            │         │       job_descriptions        │
├──────────────────────────┤         ├──────────────────────────────┤
│ id            INTEGER PK │         │ id              INTEGER PK   │
│ file_path     VARCHAR    │         │ text            TEXT         │
│ raw_text      TEXT       │         │ extracted_req.  JSON         │
│ created_at    DATETIME   │         │ created_at      DATETIME     │
└──────┬───────────────────┘         └──────────────┬───────────────┘
       │ 1                                           │ 1
       │                                             │
       │ N                                           │ N
┌──────▼───────────────────┐         ┌──────────────▼───────────────┐
│        cv_sections        │         │          interviews           │
├──────────────────────────┤         ├──────────────────────────────┤
│ id            INTEGER PK │         │ id              INTEGER PK   │
│ cv_id         INTEGER FK ├────────►│ cv_id           INTEGER FK   │
│ section_name  VARCHAR    │         │ jd_id           INTEGER FK   │
│ content       TEXT       │         │ status          VARCHAR       │
└──────────────────────────┘         │ level           VARCHAR       │
                                     │ num_questions   INTEGER       │
                                     │ plan            JSON          │
                                     │ current_q_idx   INTEGER       │
                                     │ started_at      DATETIME      │
                                     │ finished_at     DATETIME      │
                                     └──────┬─────────┬─────────────┘
                                            │ 1       │ 1
                                            │         │
                                       N ▼       N ▼
                               ┌──────────────┐ ┌──────────────────┐
                               │   messages   │ │     reports      │
                               ├──────────────┤ ├──────────────────┤
                               │ id        PK │ │ id           PK  │
                               │ interview_id │ │ entity_type  VAR │
                               │ role         │ │ entity_id    INT │
                               │ text         │ │ report_json  JSON│
                               │ created_at   │ │ interview_id FK  │
                               └──────────────┘ │ created_at   DT  │
                                                 └──────────────────┘
```

---

## Описание таблиц

### `cvs` — Резюме

Хранит каждое загруженное резюме.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `file_path` | VARCHAR(512) | Путь к файлу в папке `uploads/` |
| `raw_text` | TEXT | Нормализованный полный текст резюме |
| `created_at` | DATETIME | Дата и время загрузки (UTC) |

**Связи:**
- Один CV → много `cv_sections` (cascade delete)
- Один CV → много `interviews`

---

### `cv_sections` — Секции резюме

Хранит разбивку CV на именованные блоки.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `cv_id` | INTEGER FK | Ссылка на `cvs.id` |
| `section_name` | VARCHAR(100) | Имя секции (см. ниже) |
| `content` | TEXT | Текстовое содержимое секции |

**Возможные значения `section_name`:**

| Значение | Описание |
|----------|----------|
| `contacts` | Контактные данные |
| `summary` | Краткое резюме / профиль |
| `skills` | Навыки и технологии |
| `experience` | Опыт работы |
| `education` | Образование |
| `projects` | Проекты / портфолио |
| `certifications` | Сертификаты и курсы |
| `languages` | Языки |
| `other` | Прочее (нераспознанные секции) |

---

### `job_descriptions` — Описания вакансий

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `text` | TEXT | Исходный текст вакансии |
| `extracted_requirements` | JSON | Структурированные требования (см. ниже) |
| `created_at` | DATETIME | Дата создания (UTC) |

**Структура `extracted_requirements`:**

```json
{
  "hard_skills": ["Python", "FastAPI", "PostgreSQL"],
  "soft_skills": ["Teamwork", "Communication"],
  "responsibilities": ["Design APIs", "Write tests"],
  "keywords": ["backend", "REST", "microservices"]
}
```

---

### `interviews` — Сессии интервью

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `cv_id` | INTEGER FK | Ссылка на резюме |
| `jd_id` | INTEGER FK | Ссылка на вакансию (опционально) |
| `status` | VARCHAR(20) | Статус: `created` / `in_progress` / `finished` |
| `level` | VARCHAR(20) | Уровень кандидата: `junior` / `mid` / `senior` |
| `num_questions` | INTEGER | Итоговое кол-во вопросов |
| `plan` | JSON | Список вопросов, сгенерированных AI |
| `current_question_index` | INTEGER | Индекс текущего вопроса (0-based) |
| `started_at` | DATETIME | Время начала |
| `finished_at` | DATETIME | Время завершения (NULL если не завершено) |

**Структура `plan`:**

```json
{
  "questions": [
    {
      "text": "Расскажите о вашем опыте работы с FastAPI.",
      "type": "technical",
      "category": "Backend Development"
    },
    {
      "text": "Опишите ситуацию, когда вам пришлось решить сложную проблему.",
      "type": "behavioral",
      "category": "Problem Solving"
    }
  ]
}
```

**Типы вопросов (`type`):**

| Тип | Описание |
|-----|----------|
| `technical` | Технические вопросы по стеку |
| `behavioral` | Поведенческие вопросы (STAR-метод) |
| `situational` | Ситуационные задачи |
| `cv_based` | Вопросы по конкретным пунктам резюме |

---

### `messages` — Сообщения интервью

Полная история чата в рамках сессии интервью.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `interview_id` | INTEGER FK | Ссылка на `interviews.id` |
| `role` | VARCHAR(20) | `user` (кандидат) или `assistant` (система) |
| `text` | TEXT | Текст сообщения |
| `created_at` | DATETIME | Время сообщения (UTC) |

**Соглашение для текста системных сообщений:**
- Вопрос: обычный текст
- Обратная связь: текст начинается с `[Feedback] `

---

### `reports` — Отчёты

Универсальная таблица для хранения JSON-отчётов любого типа.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | Уникальный идентификатор |
| `entity_type` | VARCHAR(20) | `cv` / `match` / `interview` |
| `entity_id` | INTEGER | ID соответствующей сущности |
| `report_json` | JSON | Полный отчёт в JSON |
| `interview_id` | INTEGER FK | Ссылка на интервью (только для типа `interview`) |
| `created_at` | DATETIME | Дата создания (UTC) |

**Структура `report_json` для типа `cv`:**
```json
{
  "issues": ["Нет раздела Summary", "Слабые глаголы..."],
  "tips": ["Добавьте количественные достижения..."],
  "rewrites": [{"original": "...", "improved": "..."}]
}
```

**Структура `report_json` для типа `match`:**
```json
{
  "match_score": 72,
  "matched_skills": ["Python", "REST API"],
  "missing_skills": ["Kubernetes", "Kafka"],
  "recommendations": ["Добавьте опыт работы с Docker..."],
  "jd_id": 3
}
```

**Структура `report_json` для типа `interview`:**
```json
{
  "overall_score": 3.8,
  "criteria_scores": {
    "relevance": 4,
    "clarity": 3,
    "structure": 4,
    "technical_depth": 3,
    "communication": 5
  },
  "strengths": ["Чёткая структура ответов..."],
  "weaknesses": ["Недостаточно технической глубины..."],
  "recommendations": ["Используйте STAR-метод..."],
  "improved_answers": [
    {
      "question": "...",
      "original": "...",
      "improved": "..."
    }
  ]
}
```

---

## Каскадное удаление

При удалении CV (`DELETE /api/cv/{id}`) автоматически удаляются все связанные `cv_sections` (настроено через SQLAlchemy `cascade="all, delete-orphan"`). Аналогично для `Interview` → `Message`.

## Переход на PostgreSQL

Для production-окружения достаточно изменить `DATABASE_URL` в `.env`:

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cv_helper
```

И добавить зависимость:

```bash
pip install asyncpg
```
