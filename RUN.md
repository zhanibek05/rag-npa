# Инструкции по запуску

## 1. Подготовка данных (один раз)

```bash
# Активируйте виртуальное окружение
source .venv/bin/activate

# Парсинг НПА
python src/build_corpus.py

# Построение индекса
python src/build_index.py
```

## 2. Запуск Ollama

```bash
# В отдельном терминале
ollama serve

# Убедитесь, что модель загружена
ollama pull llama3.1:8b
```

## 3. Запуск Backend (FastAPI)

```bash
# В отдельном терминале
source .venv/bin/activate
python src/api.py
```

API будет доступен на http://localhost:8000  
Swagger документация: http://localhost:8000/docs

## 4. Запуск Frontend

```bash
# В отдельном терминале
cd frontend
npm run dev
```

Фронтенд будет доступен на http://localhost:5173

## 5. Использование

Откройте браузер на http://localhost:5173 и:
- Переключайтесь между режимами "Поиск" и "Ответ"
- Вводите вопросы по НПА
- Получайте ответы с источниками

### Режим "Поиск" 🔍
Быстрый семантический поиск по документам без генерации ответа.

### Режим "Ответ" 💬
Получите развернутый ответ на вопрос с использованием AI (Ollama) и релевантных источников.

## Структура проекта

```
rag-npa/
├── src/
│   ├── api.py              # FastAPI backend
│   ├── answer.py           # CLI генерация ответов
│   ├── build_corpus.py     # Парсинг документов
│   ├── build_index.py      # Построение индекса
│   └── search.py           # CLI поиск
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # React компонент
│   │   └── App.css         # Стили
│   └── package.json
├── data/
│   ├── faiss.index         # Векторный индекс
│   └── chunks_meta.jsonl   # Метаданные чанков
└── requirements.txt
```

## API Endpoints

### GET /health
Проверка статуса API

### POST /search
Семантический поиск
```json
{
  "query": "Ваш запрос",
  "top_k": 5
}
```

### POST /answer
Генерация ответа с RAG
```json
{
  "query": "Ваш вопрос",
  "top_k": 10,
  "max_context_chars": 7000
}
```

## Troubleshooting

### Backend не запускается
- Проверьте, что активировано виртуальное окружение
- Убедитесь, что построен индекс (`data/faiss.index` существует)
- Проверьте, что установлены все зависимости: `pip install fastapi uvicorn`

### Ollama ошибка
- Запустите `ollama serve` в отдельном терминале
- Загрузите модель: `ollama pull llama3.1:8b`
- Проверьте доступность: `curl http://localhost:11434/api/version`

### Frontend не подключается к Backend
- Проверьте, что Backend запущен на порту 8000
- Откройте http://localhost:8000/health в браузере
- Проверьте CORS настройки в `src/api.py`
