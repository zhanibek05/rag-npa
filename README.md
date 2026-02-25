# RAG NPA (Education)

Локальный CLI-ассистент для ответов по НПА в сфере образования.
Проект реализует классический RAG-пайплайн:

1. Скачивание и очистка текста НПА.
2. Разбиение на абзацы и чанки.
3. Построение эмбеддингов и FAISS-индекса.
4. Семантический поиск релевантных чанков.
5. Генерация ответа через локальную LLM (Ollama).

## 1) Требования

- Python `3.10+` (у вас сейчас `3.14`, это ок)
- Linux/macOS (ниже команды для bash)
- Установленный Ollama для генерации ответов

Опционально:
- GPU для LLM (эмбеддинги лучше запускать на `cpu`, чтобы не ловить OOM)

## 2) Установка

```bash
cd /home/zhanibek/projects/diploma/rag_npa
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Подготовка данных (парсинг НПА)

Скрипт: `src/build_corpus.py`

Что делает:
- Загружает страницу НПА (по умолчанию `https://adilet.zan.kz/rus/docs/Z070000319_`)
- Удаляет технические блоки (`script/style/...`)
- Извлекает текстовые элементы (`h1..h4`, `p`, `li`)
- Формирует:
  - сырой текст,
  - абзацы в JSONL,
  - чанки в JSONL.

Запуск:

```bash
python src/build_corpus.py
```

Ключевые параметры:
- `--url` - URL НПА
- `--verify-ssl` - включить строгую проверку TLS-сертификата
- `--max-chars` - размер чанка в символах (по умолчанию `1200`)
- `--overlap-paragraphs` - overlap по абзацам (по умолчанию `2`)
- `--out-dir` - папка вывода (по умолчанию `./data`)

Важно про SSL:
- Сейчас по умолчанию `verify_ssl=False` внутри скрипта.
- Это сделано из-за ошибок сертификата в некоторых окружениях.
- В нормальной среде рекомендуется запускать с `--verify-ssl`.

Выходные файлы:
- `data/act_raw.txt`
- `data/act_paragraphs.jsonl`
- `data/act_chunks.jsonl`

## 4) Построение индекса

Скрипт: `src/build_index.py`

Что делает:
- Читает `act_chunks.jsonl`
- Строит эмбеддинги (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- Нормализует вектора
- Создает FAISS индекс `IndexFlatIP`
- Сохраняет метаданные чанков в `chunks_meta.jsonl`

Запуск:

```bash
python src/build_index.py
```

Параметры:
- `--chunks` - путь к чанкам
- `--out-dir` - папка вывода
- `--model` - модель эмбеддингов
- `--batch-size` - batch при векторизации

Выходные файлы:
- `data/faiss.index`
- `data/chunks_meta.jsonl`

## 5) Проверка поиска (без LLM)

Скрипт: `src/search.py`

Запуск:

```bash
python src/search.py "какие требования к образовательной программе" --top-k 5
```

Что выводит:
- Топ релевантных чанков
- similarity score
- `id` чанка

Это главный этап отладки RAG. Если здесь плохие результаты, LLM тоже ответит плохо.

## 6) Генерация ответа через Ollama

Скрипт: `src/answer.py`

### 6.1 Установка и запуск Ollama

Установка (Linux):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Скачать модель:

```bash
ollama pull llama3.1:8b
```

Запустить сервис:

```bash
ollama serve
```

Проверка:

```bash
curl http://localhost:11434/api/tags
```

### 6.2 Запуск ответа

```bash
python src/answer.py "Как осуществляется финансирование образовательных организаций?" --top-k 10 --max-context-chars 7000 --device cpu
```

Параметры:
- `--index` - путь к FAISS индексу
- `--meta` - путь к метаданным чанков
- `--model` - модель эмбеддингов
- `--device` - `cpu` или `cuda` для эмбеддингов
- `--top-k` - сколько чанков брать из поиска
- `--ollama-model` - имя модели в Ollama
- `--max-context-chars` - ограничение контекста для LLM

## 7) Структура проекта

```text
rag_npa/
  data/
    act_raw.txt
    act_paragraphs.jsonl
    act_chunks.jsonl
    chunks_meta.jsonl
    faiss.index
  src/
    build_corpus.py
    build_index.py
    search.py
    answer.py
  requirements.txt
  README.md
```

## 8) Частые проблемы и решения

### `SyntaxError` в `answer.py`
Обычно это случайно вставленные команды shell в код. Открой файл и удалите лишние строки.

### `torch.OutOfMemoryError: CUDA out of memory`
Причина: эмбеддинги и Ollama одновременно используют GPU.
Решение: запускать `answer.py` с `--device cpu`.

### `UNEXPECTED: embeddings.position_ids`
Это предупреждение загрузки весов, для этой модели обычно безопасно и не блокирует работу.

### Ответы "недостаточно информации"
Обычно причина в retrieval, а не в LLM.
Что делать:
- увеличить `--top-k` (`10..20`)
- увеличить `--max-context-chars`
- уменьшить размер чанков в `build_corpus.py` и пересобрать индекс

## 9) Рекомендуемый рабочий цикл

После смены источника/параметров чанкинга:

```bash
python src/build_corpus.py
python src/build_index.py
python src/search.py "тестовый запрос" --top-k 10
python src/answer.py "тестовый запрос" --top-k 10 --device cpu
```

## 10) Публикация в GitHub

Перед пушем убедитесь, что не коммитятся:
- `.venv/`
- локальные модели и кэши
- большие артефакты (индексы, промежуточные файлы)

В проект добавлен `.gitignore`, который это покрывает.
