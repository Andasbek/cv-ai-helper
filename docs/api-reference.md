# Справочник API

Базовый URL: `http://localhost:8000`

Интерактивная документация (Swagger UI): `http://localhost:8000/docs`

---

## Общие соглашения

- Все запросы и ответы в формате **JSON** (кроме загрузки файла — multipart/form-data)
- При ошибке возвращается объект `{"detail": "описание ошибки"}`
- Временны́е метки в формате ISO 8601 UTC

---

## Health Check

### `GET /health`

Проверка работоспособности сервера.

**Ответ:**
```json
{"status": "ok"}
```

---

## Модуль CV

### `POST /api/cv/upload`

Загрузка файла резюме.

**Тип запроса:** `multipart/form-data`

**Параметры формы:**

| Поле | Тип | Описание |
|------|-----|----------|
| `file` | File | PDF, TXT или DOCX файл (макс. 20 MB) |

**Пример запроса (curl):**
```bash
curl -X POST http://localhost:8000/api/cv/upload \
  -F "file=@/path/to/resume.pdf"
```

**Ответ `200 OK`:**
```json
{
  "cv_id": 1,
  "message": "CV uploaded and parsed successfully."
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 400 | Неподдерживаемый тип файла или размер превышен |
| 422 | Не удалось извлечь текст (пустой или скан-PDF) |

---

### `GET /api/cv/{cv_id}`

Получение данных резюме по ID.

**Параметры пути:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `cv_id` | integer | ID резюме |

**Пример запроса:**
```bash
curl http://localhost:8000/api/cv/1
```

**Ответ `200 OK`:**
```json
{
  "cv_id": 1,
  "raw_text": "John Doe\njohn@example.com\n...",
  "sections": [
    {
      "section_name": "contacts",
      "content": "John Doe\njohn@example.com\n+1 555-0100"
    },
    {
      "section_name": "skills",
      "content": "Python, FastAPI, PostgreSQL, Docker"
    },
    {
      "section_name": "experience",
      "content": "Senior Developer at Acme Corp (2021–2024)\n..."
    }
  ]
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | CV с указанным ID не найдено |

---

### `POST /api/cv/{cv_id}/analyze`

Запуск AI-анализа резюме. Создаёт запись в таблице `reports`.

> Время выполнения: 20–40 секунд (зависит от OpenAI API)

**Параметры пути:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `cv_id` | integer | ID резюме |

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/cv/1/analyze
```

**Ответ `200 OK`:**
```json
{
  "cv_id": 1,
  "issues": [
    "Отсутствует раздел Summary/Objective",
    "В разделе Experience нет количественных достижений",
    "Используются слабые глаголы: 'responsible for', 'worked on'"
  ],
  "tips": [
    "Добавьте Summary с ключевыми компетенциями (2–3 предложения)",
    "Добавьте метрики к каждой должности: числа, проценты, сроки",
    "Замените 'worked on' → 'developed', 'implemented', 'launched'"
  ],
  "rewrites": [
    {
      "original": "Responsible for backend development",
      "improved": "Developed REST APIs using FastAPI, cutting response time by 40%"
    }
  ]
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | CV не найдено |
| 500 | Ошибка API OpenAI |

---

### `DELETE /api/cv/{cv_id}`

Удаление резюме и файла с диска.

**Параметры пути:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `cv_id` | integer | ID резюме |

**Пример запроса:**
```bash
curl -X DELETE http://localhost:8000/api/cv/1
```

**Ответ `200 OK`:**
```json
{"message": "CV deleted successfully"}
```

---

## Модуль Job Description

### `POST /api/jd`

Сохранение вакансии и извлечение требований с помощью AI.

**Тело запроса:**
```json
{
  "text": "We are looking for a Backend Python Developer...\n\nRequirements:\n- Python 3.10+\n- FastAPI or Django\n- PostgreSQL..."
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/jd \
  -H "Content-Type: application/json" \
  -d '{"text": "Backend Python Developer..."}'
```

**Ответ `200 OK`:**
```json
{
  "jd_id": 1,
  "extracted_requirements": {
    "hard_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
    "soft_skills": ["Communication", "Teamwork"],
    "responsibilities": [
      "Design and develop backend services",
      "Write unit and integration tests"
    ],
    "keywords": ["backend", "microservices", "CI/CD"]
  }
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 400 | Пустой текст вакансии |

---

### `POST /api/match`

Сопоставление CV с вакансией.

**Тело запроса:**
```json
{
  "cv_id": 1,
  "jd_id": 1
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -d '{"cv_id": 1, "jd_id": 1}'
```

**Ответ `200 OK`:**
```json
{
  "match_score": 72,
  "matched_skills": ["Python", "FastAPI", "REST API", "PostgreSQL"],
  "missing_skills": ["Docker", "Kubernetes", "AWS"],
  "recommendations": [
    "Добавьте в резюме опыт работы с контейнеризацией",
    "Упомяните проекты с деплоем в облаке"
  ]
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | CV или JD не найдены |

---

## Модуль Interview

### `POST /api/interview/start`

Создание и запуск новой сессии интервью.

**Тело запроса:**
```json
{
  "cv_id": 1,
  "jd_id": 1,
  "company_info": "Acme Corp — SaaS-платформа для автоматизации логистики",
  "level": "junior",
  "num_questions": 10
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `cv_id` | integer | ✓ | ID резюме |
| `jd_id` | integer | — | ID вакансии |
| `company_info` | string | — | Краткое описание компании |
| `level` | string | — | `junior` / `mid` / `senior` (по умолчанию: `junior`) |
| `num_questions` | integer | — | Кол-во вопросов (по умолчанию: 10) |

**Ответ `200 OK`:**
```json
{
  "session_id": 1,
  "question": "Расскажите о себе и почему вас интересует эта позиция?",
  "question_number": 1,
  "total_questions": 10
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | CV или JD не найдены |
| 500 | Не удалось сгенерировать вопросы |

---

### `POST /api/interview/{session_id}/message`

Отправка ответа кандидата и получение следующего вопроса.

**Параметры пути:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | integer | ID сессии интервью |

**Тело запроса:**
```json
{
  "answer": "Я изучал Python в университете и 2 года работал на фрилансе. Мне интересна эта позиция, потому что..."
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/interview/1/message \
  -H "Content-Type: application/json" \
  -d '{"answer": "Я изучал Python..."}'
```

**Ответ `200 OK`:**
```json
{
  "feedback": "Хороший ответ, но можно добавить конкретные примеры проектов с результатами.",
  "next_question": "Расскажите о вашем опыте работы с FastAPI. Какой самый сложный проект вы реализовали?",
  "question_number": 2,
  "total_questions": 10,
  "is_last": false
}
```

Когда `is_last: true`:
```json
{
  "feedback": "Отличный ответ с конкретными примерами!",
  "next_question": null,
  "question_number": 10,
  "total_questions": 10,
  "is_last": true
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | Сессия интервью не найдена |
| 400 | Интервью уже завершено |

---

### `POST /api/interview/{session_id}/finish`

Завершение интервью и генерация финального отчёта.

> Вызывайте только когда `is_last: true`. Требует минимум одного ответа.
> Время выполнения: до 60 секунд.

**Параметры пути:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | integer | ID сессии интервью |

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/interview/1/finish
```

**Ответ `200 OK`:**
```json
{
  "session_id": 1,
  "report": {
    "overall_score": 3.8,
    "criteria_scores": {
      "relevance": 4,
      "clarity": 3,
      "structure": 4,
      "technical_depth": 3,
      "communication": 5
    },
    "strengths": [
      "Чёткая коммуникация",
      "Хорошее понимание базовых концепций"
    ],
    "weaknesses": [
      "Ответы без конкретных цифр и метрик",
      "Не используется STAR-структура"
    ],
    "recommendations": [
      "Практикуйте STAR-метод для behavioral-вопросов",
      "Подготовьте 3–5 историй из опыта с конкретными результатами"
    ],
    "improved_answers": [
      {
        "question": "Расскажите о сложной задаче...",
        "original": "Я решал проблемы с производительностью базы данных",
        "improved": "В проекте X (2023) я столкнулся с деградацией производительности при 10k RPS. Я проанализировал slow queries, добавил индексы и кэширование через Redis. В результате время ответа снизилось с 800мс до 120мс."
      }
    ]
  }
}
```

**Возможные ошибки:**

| Код | Описание |
|-----|----------|
| 404 | Сессия не найдена |
| 400 | Нет записанных ответов |

---

## Коды ошибок

| HTTP-код | Значение |
|----------|----------|
| 200 | Успешный запрос |
| 400 | Ошибка в данных запроса (невалидный файл, пустые поля) |
| 404 | Ресурс не найден (неверный ID) |
| 422 | Ошибка обработки данных (не удалось извлечь текст) |
| 500 | Внутренняя ошибка сервера (ошибка OpenAI и т.д.) |

**Формат ошибки:**
```json
{
  "detail": "CV not found"
}
```

---

## Полный сценарий использования

```bash
# 1. Загрузить CV
CV_ID=$(curl -s -X POST http://localhost:8000/api/cv/upload \
  -F "file=@resume.pdf" | python3 -c "import sys,json; print(json.load(sys.stdin)['cv_id'])")

# 2. Получить секции
curl http://localhost:8000/api/cv/$CV_ID

# 3. Анализировать CV
curl -X POST http://localhost:8000/api/cv/$CV_ID/analyze

# 4. Добавить вакансию
JD_ID=$(curl -s -X POST http://localhost:8000/api/jd \
  -H "Content-Type: application/json" \
  -d '{"text": "Senior Python Developer..."}' | python3 -c "import sys,json; print(json.load(sys.stdin)['jd_id'])")

# 5. Сопоставить CV с вакансией
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -d "{\"cv_id\": $CV_ID, \"jd_id\": $JD_ID}"

# 6. Запустить интервью
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d "{\"cv_id\": $CV_ID, \"jd_id\": $JD_ID, \"level\": \"junior\", \"num_questions\": 5}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# 7. Ответить на вопрос
curl -X POST http://localhost:8000/api/interview/$SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d '{"answer": "Мой опыт..."}'

# 8. Получить финальный отчёт (после всех вопросов)
curl -X POST http://localhost:8000/api/interview/$SESSION_ID/finish
```
