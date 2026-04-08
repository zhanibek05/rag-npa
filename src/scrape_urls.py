"""
scrape_urls.py — собирает список документов со страниц поиска adilet.zan.kz
(сфера: Образование, статус: действующий) и сохраняет в таблицу documents.

Запуск:
    python src/scrape_urls.py
    python src/scrape_urls.py --max-pages 5   # для теста
"""

import argparse
import re
import time
import warnings
from datetime import date
from typing import Optional

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib3.exceptions import InsecureRequestWarning

try:
    from src.core.config import DATABASE_URL
    from src.core.models import Document
except ModuleNotFoundError:
    from core.config import DATABASE_URL
    from core.models import Document

# ir=1_021 → Образование, st=new|upd → Действующий
BASE_URL = "https://adilet.zan.kz"
SEARCH_URL = BASE_URL + "/rus/search/docs/ir=1_021&page={page}&st=new%7Cupd"
FIRST_PAGE_URL = BASE_URL + "/rus/search/docs/ir=1_021&st=new%7Cupd"

SKIP_DOC_TYPES = {"Изменения", "Дополнения"}

_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def _parse_date(text: str) -> Optional[date]:
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    month = _MONTHS.get(month_str)
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _doc_id_from_url(href: str) -> Optional[str]:
    m = re.search(r"/docs/([A-Za-z0-9_]+)", href)
    return m.group(1) if m else None


def fetch_page(url: str, session: requests.Session) -> BeautifulSoup:
    warnings.simplefilter("ignore", InsecureRequestWarning)
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def total_pages(soup: BeautifulSoup) -> int:
    pager = soup.find("div", class_="wp-pagenavi")
    if not pager:
        return 1
    # ищем «Страница 1 из N»
    m = re.search(r"из\s+(\d+)", pager.get_text())
    return int(m.group(1)) if m else 1


def parse_results(soup: BeautifulSoup) -> list[dict]:
    docs = []
    for holder in soup.find_all("div", class_="post_holder"):
        link = holder.select_one("h4.post_header a")
        if not link:
            continue

        href = link.get("href", "")
        if "/rus/docs/" not in href:
            continue

        doc_id = _doc_id_from_url(href)
        if not doc_id:
            continue

        url = BASE_URL + href.split("?")[0].rstrip("/")
        title = link.get_text(" ", strip=True)

        # реквизит в <p>: «Закон Республики Казахстан от 5 февраля 2026 года № 260-VIII ЗРК»
        requisite_el = holder.find("p")
        requisite = requisite_el.get_text(" ", strip=True) if requisite_el else ""

        # тип документа — первое слово реквизита
        doc_type = None
        m = re.match(
            r"^(Закон|Постановление|Приказ|Решение|Указ|Кодекс|Конституция"
            r"|Регламент|Инструкция|Положение|Устав|Концепция|Программа)",
            requisite,
        )
        if m:
            doc_type = m.group(1)

        if doc_type and doc_type in SKIP_DOC_TYPES:
            continue

        adopted_date = _parse_date(requisite)

        docs.append(dict(
            id=doc_id,
            url=url,
            title=title,
            doc_type=doc_type,
            status="Действующий",
            adopted_date=adopted_date,
            index_status="pending",
        ))
    return docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Максимум страниц (0 = все)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Задержка между запросами (сек)")
    args = parser.parse_args()

    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    http = requests.Session()
    http.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; RAG-NPA-Bot/1.0; diploma research)"
    )

    print("Загружаю первую страницу...")
    first_soup = fetch_page(FIRST_PAGE_URL, http)
    n_pages = total_pages(first_soup)
    if args.max_pages:
        n_pages = min(n_pages, args.max_pages)
    print(f"Всего страниц: {n_pages}")

    added = skipped = 0
    for page in range(1, n_pages + 1):
        if page == 1:
            soup = first_soup
        else:
            soup = fetch_page(SEARCH_URL.format(page=page), http)

        docs = parse_results(soup)

        with Session() as db:
            for d in docs:
                if db.get(Document, d["id"]):
                    skipped += 1
                    continue
                db.add(Document(**d))
                added += 1
            db.commit()

        print(f"  Страница {page}/{n_pages}: +{len(docs)} новых")

        if page < n_pages:
            time.sleep(args.delay)

    print(f"\nГотово. Добавлено: {added}, пропущено (уже есть): {skipped}")


if __name__ == "__main__":
    main()
