# RAG NPA Backend

Backend для поиска и ответов по НПА (RAG):
- извлечение текста НПА,
- чанкинг,
- индексация в FAISS,
- semantic search,
- генерация ответа через Ollama.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Подготовка данных

```bash
python src/build_corpus.py
python src/build_index.py
```

Результат в `data/`:
- `act_chunks.jsonl`
- `chunks_meta.jsonl`
- `faiss.index`

## Запуск

Настройки читаются автоматически из файла `.env` (без `export`).

1. Запустить Ollama:

```bash
ollama pull llama3.1:8b
ollama serve
```

2. Запустить backend:

```bash
source .venv/bin/activate
python src/api.py
```

API: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`

## CLI (для проверки retrieval/RAG)

```bash
python src/search.py "финансирование образовательных организаций" --top-k 5
python src/answer.py "Как финансируются образовательные организации?" --top-k 10 --max-context-chars 7000 --device cpu
```

## Переменные окружения

Основные переменные в `.env`:
- `INDEX_PATH` (default `./data/faiss.index`)
- `META_PATH` (default `./data/chunks_meta.jsonl`)
- `EMBEDDING_MODEL` (default `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- `EMBEDDING_DEVICE` (default `cpu`)
- `LLM_PROVIDER` (`ollama` или `openai`)
- `LLM_MODEL` (общий override, опционально)
- `OLLAMA_URL` (default `http://localhost:11434/api/generate`)
- `OLLAMA_MODEL` (default `llama3.1:8b`)
- `OPENAI_API_KEY` (нужен для OpenAI)
- `OPENAI_MODEL` (default `gpt-4o-mini`)

Переключение на OpenAI:
- в `.env`: `LLM_PROVIDER=openai`
- заполнить `OPENAI_API_KEY`

## API

### `GET /health`
Статус сервиса и загрузки индекса.

### `POST /search`
```json
{
  "query": "Ваш запрос",
  "top_k": 5
}
```

### `POST /answer`
```json
{
  "query": "Ваш вопрос",
  "top_k": 10,
  "max_context_chars": 7000
}
```

## Актуальная структура `src`

```text
src/
  api.py
  answer.py
  search.py
  build_corpus.py
  build_index.py
  core/
    config.py
    io.py
    retrieval.py
    context.py
    llm.py
    service.py
```
