# Установка и запуск

## Требования

- **Python** 3.11 или выше
- **OpenAI API ключ** (получить на [platform.openai.com](https://platform.openai.com))
- Операционная система: macOS / Linux / Windows

---

## Шаг 1 — Клонирование и создание виртуального окружения

```bash
# Клонировать репозиторий
git clone <url-репозитория>
cd cv-ai-helper

# Создать виртуальное окружение
python3 -m venv .venv

# Активировать окружение
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

---

## Шаг 2 — Установка зависимостей

```bash
pip install -r requirements.txt
```

Список устанавливаемых пакетов:

| Пакет | Назначение |
|-------|-----------|
| `fastapi` | Веб-фреймворк для API |
| `uvicorn[standard]` | ASGI-сервер |
| `sqlalchemy` + `aiosqlite` | Асинхронная ORM + SQLite |
| `python-multipart` | Приём файлов через форму |
| `pdfplumber` | Извлечение текста из PDF |
| `python-docx` | Извлечение текста из DOCX |
| `openai` | SDK для GPT-4o |
| `pydantic` + `pydantic-settings` | Валидация данных и конфиг |
| `python-dotenv` | Загрузка `.env` |
| `streamlit` | Фронтенд |
| `requests` | HTTP-запросы от фронтенда к API |
| `httpx==0.27.2` | HTTP-клиент (пиннинг для совместимости с openai) |
| `greenlet` | Асинхронный драйвер для SQLAlchemy |

---

## Шаг 3 — Настройка переменных окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```dotenv
OPENAI_API_KEY=sk-...          # Обязательно — ваш ключ OpenAI
DATABASE_URL=sqlite+aiosqlite:///./cv_helper.db  # Путь к базе данных
UPLOAD_DIR=./uploads           # Папка для загружаемых файлов
MAX_FILE_SIZE_MB=20            # Максимальный размер файла
BACKEND_URL=http://localhost:8000  # URL backend (используется фронтендом)
```

> **Важно:** файл `.env` добавлен в `.gitignore` и не попадёт в репозиторий. Никогда не коммитьте API-ключи.

---

## Шаг 4 — Запуск backend

```bash
# Из корня проекта, с активированным .venv
uvicorn backend.main:app --reload
```

При первом запуске автоматически создаются все таблицы SQLite.

- API доступен по адресу: **http://localhost:8000**
- Интерактивная документация Swagger: **http://localhost:8000/docs**
- Альтернативная документация ReDoc: **http://localhost:8000/redoc**
- Health check: **http://localhost:8000/health**

---

## Шаг 5 — Запуск frontend (в отдельном терминале)

```bash
# Активировать окружение
source .venv/bin/activate

# Запустить Streamlit
streamlit run frontend/app.py
```

Приложение откроется в браузере по адресу: **http://localhost:8501**

---

## Проверка работоспособности

```bash
# Проверить health backend
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"ok"}

# Проверить таблицы базы данных
python3 -c "
import sqlite3
conn = sqlite3.connect('cv_helper.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print('Tables:', [t[0] for t in tables])
"
# Ожидаемый вывод: Tables: ['cvs', 'job_descriptions', 'cv_sections', 'interviews', 'messages', 'reports']
```

---

## Частые проблемы

### `TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'`

Причина: несовместимость `openai` с новыми версиями `httpx`.
Решение: убедитесь, что в `requirements.txt` прописан `httpx==0.27.2`.

```bash
pip install "httpx==0.27.2"
```

### `ValueError: the greenlet library is required`

Причина: не установлен `greenlet` (нужен SQLAlchemy для async).
Решение:

```bash
pip install greenlet
```

### `Could not extract text: ...`

Причина: загружен PDF-скан (изображение без слоя текста).
Решение: конвертируйте PDF в текстовый формат или используйте TXT-файл.

---

## Структура папки `uploads/`

Загружаемые файлы сохраняются в `uploads/` с UUID-именем:

```
uploads/
├── .gitkeep
├── a1b2c3d4e5f6...pdf    # загруженное CV
└── ...
```

Файлы удаляются при вызове `DELETE /api/cv/{id}`. В продакшене рекомендуется настроить автоматическую очистку по времени.
