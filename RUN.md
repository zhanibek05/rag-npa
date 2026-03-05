# RUN

## 1) Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Подготовка индекса (один раз или после смены источника)

```bash
python src/build_corpus.py
python src/build_index.py
```

## 3) Запуск сервисов

Терминал 1 (Ollama):
```bash
ollama pull llama3.1:8b
ollama serve
```

Терминал 2 (Backend):
```bash
source .venv/bin/activate
python src/api.py
```

Терминал 3 (Frontend, если нужен UI):
```bash
cd frontend
npm install
npm run dev
```

## 4) Проверка

- Backend health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## 5) Быстрый тест без UI

```bash
source .venv/bin/activate
python src/search.py "финансирование образования" --top-k 5
python src/answer.py "Как финансируются образовательные организации?" --top-k 10 --max-context-chars 7000 --device cpu
```
