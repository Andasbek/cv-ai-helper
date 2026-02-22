# Сервисы и бизнес-логика

Вся бизнес-логика вынесена в папку `backend/services/`. Каждый модуль не имеет состояния и может быть протестирован независимо.

---

## `parser.py` — Извлечение текста

**Файл:** [backend/services/parser.py](../backend/services/parser.py)

### Назначение

Извлекает читаемый текст из загруженного файла резюме и нормализует его.

### Функции

#### `extract_text(path: str) -> str`

Точка входа — определяет формат файла по расширению и вызывает нужный парсер.

```python
ext = Path(path).suffix.lower()  # .pdf / .txt / .docx
```

#### `extract_text_from_pdf(path: str) -> str`

Использует библиотеку `pdfplumber` для извлечения текста из каждой страницы PDF.

```python
with pdfplumber.open(path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
```

> **Ограничение:** работает только с текстовыми PDF. Для PDF-сканов (изображений) потребуется OCR (будущая фича).

#### `extract_text_from_txt(path: str) -> str`

Читает файл с кодировкой UTF-8, при ошибках подставляет символ замены (`errors="replace"`).

#### `extract_text_from_docx(path: str) -> str`

Использует `python-docx` для чтения параграфов документа Word.

#### `normalize_text(text: str) -> str`

Очищает извлечённый текст:
1. Нормализует переносы строк (`\r\n` → `\n`)
2. Сжимает три и более пустых строк до двух
3. Убирает trailing-пробелы в каждой строке
4. Сжимает множественные пробелы и табуляции

---

## `segmenter.py` — Сегментация CV

**Файл:** [backend/services/segmenter.py](../backend/services/segmenter.py)

### Назначение

Разбивает нормализованный текст резюме на именованные секции с помощью регулярных выражений.

### Алгоритм

1. Текст разбивается на строки
2. Каждая строка проверяется регулярным выражением `_SECTION_RE`
3. Если строка является заголовком — определяется имя секции (`_classify_header`)
4. Если строка — содержимое — добавляется к текущей секции
5. Блок до первого заголовка автоматически считается секцией `contacts`

### Функция `segment_cv(text: str) -> dict[str, str]`

```python
# Пример вывода:
{
  "contacts": "John Doe\njohn@example.com\n+1 555...",
  "summary": "Experienced Python developer...",
  "skills": "Python, FastAPI, Docker...",
  "experience": "Senior Developer at Acme Corp (2021–2024)...",
  "education": "BSc Computer Science, MIT, 2020"
}
```

### Распознаваемые секции

| Секция | Ключевые слова |
|--------|---------------|
| `contacts` | contact, personal info, phone, email, linkedin, github, address |
| `summary` | summary, about, objective, profile, overview, career objective |
| `skills` | skills, technologies, competencies, expertise, tools |
| `experience` | experience, work experience, employment history, positions held |
| `education` | education, academic, degrees, qualifications, university, school |
| `projects` | projects, portfolio, personal projects, open-source |
| `certifications` | certifications, certificates, licenses, courses, training |
| `languages` | languages, linguistics |

> **Примечание:** сегментатор использует эвристику (regex) и не является 100% точным. При нестандартном форматировании секции могут не распознаться — в этом случае весь текст помещается в секцию `contacts`.

---

## `file_utils.py` — Работа с файлами

**Файл:** [backend/utils/file_utils.py](../backend/utils/file_utils.py)

### Назначение

Безопасная работа с загружаемыми файлами: валидация, сохранение, удаление.

### Функции

#### `validate_file(filename, content_type, size)`

Проверяет три условия, иначе бросает `HTTPException(400)`:
- Расширение файла входит в `{.pdf, .txt, .docx}`
- MIME-тип соответствует расширению
- Размер файла не превышает `MAX_FILE_SIZE_MB` (по умолчанию 20 MB)

#### `save_upload(file: UploadFile) -> str`

1. Создаёт папку `uploads/` если не существует
2. Генерирует уникальное имя файла через `uuid.uuid4().hex`
3. Читает байты файла и вызывает валидацию
4. Записывает файл на диск
5. Возвращает путь к файлу

```python
# Пример имени файла:
"uploads/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.pdf"
```

#### `delete_file(path: str)`

Безопасно удаляет файл, игнорируя ошибки (файл уже удалён, нет прав и т.д.).

---

## `cv_analyzer.py` — AI-анализ резюме

**Файл:** [backend/services/cv_analyzer.py](../backend/services/cv_analyzer.py)

### Назначение

Анализирует резюме с помощью GPT-4o и возвращает структурированные рекомендации.

### Функция `analyze_cv(cv_sections: dict[str, str]) -> dict`

**Входные данные:** словарь секций CV (`{section_name: content}`).

**Процесс:**
1. Секции объединяются в один текст с разделителями `=== SECTION_NAME ===`
2. Формируется запрос к GPT-4o с системным промптом
3. Ответ парсится как JSON

**Системный промпт проверяет:**
- Отсутствующие секции
- Слабые глаголы действия ("responsible for", "worked on", "helped with")
- Отсутствие метрик и количественных достижений
- Расплывчатые формулировки без конкретики
- Длинные параграфы вместо буллетов
- Отсутствие дат, названий компаний, должностей
- Повторяющиеся формулировки

**Параметры GPT-4o:**
- `model`: `gpt-4o`
- `response_format`: `{"type": "json_object"}`
- `temperature`: `0.3` (низкая — для стабильных, точных оценок)

**Возвращаемый формат:**

```json
{
  "issues": [
    "Отсутствует раздел Summary/Objective",
    "В разделе Experience нет количественных достижений"
  ],
  "tips": [
    "Добавьте Summary с ключевыми компетенциями и годами опыта",
    "Замените 'worked on' на конкретные глаголы: developed, implemented, reduced"
  ],
  "rewrites": [
    {
      "original": "Responsible for backend development",
      "improved": "Developed REST API using FastAPI, reducing response time by 40%"
    }
  ]
}
```

---

## `jd_matcher.py` — Сопоставление с вакансией

**Файл:** [backend/services/jd_matcher.py](../backend/services/jd_matcher.py)

### Назначение

Извлекает требования из текста вакансии и сравнивает их с резюме кандидата.

### Функция `extract_jd_requirements(jd_text: str) -> dict`

**Входные данные:** полный текст описания вакансии.

**Параметры GPT-4o:** `temperature=0.2` (очень низкая — для точного извлечения фактов).

**Возвращаемый формат:**

```json
{
  "hard_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
  "soft_skills": ["Communication", "Teamwork", "Problem solving"],
  "responsibilities": [
    "Design and develop backend services",
    "Write unit and integration tests",
    "Participate in code reviews"
  ],
  "keywords": ["backend", "microservices", "CI/CD", "agile"]
}
```

### Функция `match_cv_to_jd(cv_sections: dict, jd_requirements: dict) -> dict`

**Входные данные:**
- `cv_sections` — секции резюме
- `jd_requirements` — извлечённые требования вакансии (JSON)

Оба набора данных передаются в промпт GPT-4o для сравнительного анализа.

**Возвращаемый формат:**

```json
{
  "match_score": 72,
  "matched_skills": ["Python", "FastAPI", "REST API"],
  "missing_skills": ["Kubernetes", "Kafka", "AWS"],
  "recommendations": [
    "Добавьте опыт работы с контейнеризацией (Docker/Kubernetes)",
    "Упомяните конкретные метрики производительности ваших API"
  ]
}
```

**Интерпретация `match_score`:**

| Диапазон | Оценка |
|----------|--------|
| 70–100 | Хорошее соответствие |
| 40–69 | Умеренное соответствие, есть пробелы |
| 0–39 | Низкое соответствие, значительные пробелы |

---

## `interview_service.py` — Логика интервью

**Файл:** [backend/services/interview_service.py](../backend/services/interview_service.py)

### Назначение

Управляет всем жизненным циклом интервью: генерация плана, оценка ответов, финальный отчёт.

### Функция `generate_interview_plan(...) -> list[dict]`

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `cv_sections` | `dict[str, str]` | Секции резюме |
| `jd_text` | `str \| None` | Текст вакансии (опционально) |
| `company_info` | `str \| None` | Описание компании (опционально) |
| `level` | `str` | junior / mid / senior |
| `num_questions` | `int` | Желаемое кол-во вопросов |

**Стратегия генерации вопросов по уровню:**

| Уровень | Фокус |
|---------|-------|
| `junior` | Фундаментальные знания, мотивация, базовые технические вопросы |
| `mid` | Решение проблем, опыт проектов, архитектурные паттерны |
| `senior` | Лидерство, архитектурные решения, системное мышление |

`temperature=0.6` — более высокое значение для разнообразия вопросов.

---

### Функция `evaluate_answer(question: str, answer: str) -> dict`

Оценивает один ответ кандидата.

**Возвращаемый формат:**

```json
{
  "feedback": "Ответ релевантен, но не хватает конкретных примеров и метрик.",
  "score": 3
}
```

**Шкала оценок:**

| Балл | Описание |
|------|----------|
| 1 | Ответ нерелевантен или отсутствует |
| 2 | Слабо релевантен, нет содержания |
| 3 | Приемлемо, но не хватает глубины |
| 4 | Чёткий, структурированный, релевантный |
| 5 | Отличный: конкретный, впечатляющий |

---

### Функция `generate_final_report(transcript: list[dict]) -> dict`

Генерирует финальный отчёт по всему транскрипту интервью.

**Входные данные** — список объектов:

```json
[
  {
    "question": "Текст вопроса",
    "answer": "Ответ кандидата",
    "feedback": "Обратная связь",
    "type": "technical",
    "category": "Python"
  }
]
```

**Возвращаемый формат:**

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
  "strengths": [
    "Чёткая коммуникация и понятные объяснения",
    "Хорошее понимание базовых концепций Python"
  ],
  "weaknesses": [
    "Ответы на технические вопросы не содержат конкретных примеров",
    "Не используется STAR-структура для поведенческих вопросов"
  ],
  "recommendations": [
    "Практикуйте STAR-метод для behavioral-вопросов",
    "Подготовьте 3-5 конкретных историй из опыта с цифрами"
  ],
  "improved_answers": [
    {
      "question": "Расскажите о сложной задаче...",
      "original": "Я решал проблемы с производительностью...",
      "improved": "В 2023 году на проекте X (Situation) я столкнулся... (Task)... Я предложил... (Action)... В результате время ответа снизилось на 60% (Result)"
    }
  ]
}
```

---

## Общие принципы работы с OpenAI API

Все AI-сервисы используют единый подход:

1. **`AsyncOpenAI`** — асинхронный клиент, совместимый с `async/await` FastAPI
2. **`response_format={"type": "json_object"}`** — гарантирует валидный JSON в ответе
3. **`json.loads()`** — парсинг ответа
4. **Явное указание ключей** (`result.get("key", default)`) — защита от неполных ответов
5. **Модель `gpt-4o`** — используется во всех запросах

**Настройки temperature по типу задачи:**

| Задача | Temperature | Обоснование |
|--------|-------------|-------------|
| Анализ CV | 0.3 | Нужны точные, стабильные оценки |
| Извлечение JD | 0.2 | Максимальная точность извлечения фактов |
| Matching | 0.2 | Точное сравнение без фантазии |
| Генерация вопросов | 0.6 | Разнообразие для реалистичного интервью |
| Оценка ответа | 0.3 | Стабильная оценка |
| Финальный отчёт | 0.3 | Последовательный итоговый анализ |
