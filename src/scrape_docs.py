"""
scrape_docs.py — скрапит полный текст документов из таблицы documents
где index_status='pending', сохраняет raw_text и ставит status='scraped'.

Запуск:
    python -m src.scrape_docs
    python -m src.scrape_docs --limit 50   # для теста
"""

import argparse
import re
import time
import warnings
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from urllib3.exceptions import InsecureRequestWarning

try:
    from src.core.config import DATABASE_URL
    from src.core.models import Document
except ModuleNotFoundError:
    from core.config import DATABASE_URL
    from core.models import Document


def fetch_html(url: str, session: requests.Session) -> str:
    warnings.simplefilter("ignore", InsecureRequestWarning)
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # убираем мусор
    for tag in soup.find_all(["script", "style", "noscript", "nav",
                               "header", "footer", "aside"]):
        tag.decompose()

    # основной контейнер документа на adilet.zan.kz
    main = soup.find("div", id="container")
    if main is None:
        # fallback: самый большой блок текста
        best = None
        for div in soup.find_all(["div", "article", "section"]):
            t = div.get_text(" ", strip=True)
            if len(t) < 2000:
                continue
            if best is None or len(t) > best[0]:
                best = (len(t), div)
        main = best[1] if best else soup

    # убираем навигационные элементы внутри контейнера
    for tag in main.find_all(class_=re.compile(
            r"docToolbar|docNpaInfo|menu|breadcrumb|toolbar|print")):
        tag.decompose()

    paragraphs = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if el.find_parent(["nav", "header", "footer", "aside"]):
            continue
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0,
                        help="Максимум документов за один запуск (0 = все)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Задержка между запросами (сек)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Повторить документы со статусом failed")
    args = parser.parse_args()

    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    http = requests.Session()
    http.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; RAG-NPA-Bot/1.0; diploma research)"
    )

    with Session() as db:
        statuses = ["pending"]
        if args.retry_failed:
            statuses.append("failed")

        q = select(Document).where(Document.index_status.in_(statuses))
        if args.limit:
            q = q.limit(args.limit)
        docs = db.scalars(q).all()

    print(f"Документов для скрапинга: {len(docs)}")

    ok = failed = 0
    for i, doc in enumerate(docs, 1):
        try:
            html = fetch_html(doc.url, http)
            text = extract_text(html)

            if len(text) < 100:
                raise ValueError("Слишком мало текста — возможно, страница не загрузилась")

            with Session() as db:
                d = db.get(Document, doc.id)
                d.raw_text = text
                d.scraped_at = datetime.now(timezone.utc)
                d.index_status = "scraped"
                db.commit()

            ok += 1
            print(f"  [{i}/{len(docs)}] OK  {doc.id}  ({len(text)} символов)")

        except Exception as e:
            with Session() as db:
                d = db.get(Document, doc.id)
                d.index_status = "failed"
                db.commit()
            failed += 1
            print(f"  [{i}/{len(docs)}] FAIL {doc.id}: {e}")

        if i < len(docs):
            time.sleep(args.delay)

    print(f"\nГотово. Успешно: {ok}, ошибок: {failed}")


if __name__ == "__main__":
    main()
