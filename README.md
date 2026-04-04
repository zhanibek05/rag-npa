# RAG NPA

Q&A ассистент по НПА Казахстана (сфера: образование). Стек: FastAPI + PostgreSQL + Qdrant + Ollama/OpenAI.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить переменные
```

## Подготовка данных

```bash
# 1. Собрать список документов из adilet.zan.kz
python -m src.scrape_urls

# 2. Скачать полный текст документов
python -m src.scrape_docs

# 3. Разбить на чанки и загрузить в Qdrant
python -m src.build_index
```

Поддерживается ручная загрузка DOCX/PDF/TXT через `POST /documents/upload`.

## Запуск

```bash
# Запустить Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Применить миграции БД
alembic upgrade head

# Запустить backend
uvicorn src.api:app --reload

# Запустить frontend
cd frontend && npm install && npm run dev
```

API: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`

## Переменные окружения

| Переменная | Default | Описание |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL DSN |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint |
| `QDRANT_COLLECTION` | `npa_chunks` | Название коллекции |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | SentenceTransformer |
| `EMBEDDING_DEVICE` | `cpu` | `cpu` или `cuda` |
| `LLM_PROVIDER` | `ollama` | `ollama` или `openai` |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | |
| `OLLAMA_MODEL` | `llama3.1:8b` | |
| `OPENAI_API_KEY` | — | Нужен при `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | |
| `SECRET_KEY` | — | JWT секрет |

## Структура `src`

```
src/
  api.py              — FastAPI приложение
  build_index.py      — чанкинг + индексация в Qdrant
  scrape_urls.py      — сбор URL документов с adilet.zan.kz
  scrape_docs.py      — скачивание полного текста документов
  routers/
    documents.py      — CRUD документов + загрузка файлов
  core/
    config.py
    models.py         — SQLAlchemy модели (Document, User, ChatSession, ChatMessage)
    database.py
    retrieval.py
    context.py
    llm.py
    service.py
```
