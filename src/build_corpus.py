import argparse
import json
import re
import warnings
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning


URL_DEFAULT = "https://adilet.zan.kz/rus/docs/Z070000319_"


@dataclass
class Paragraph:
    text: str
    section: Optional[str]
    index: int


def fetch_html(url: str, verify_ssl: bool) -> str:
    if not verify_ssl:
        warnings.simplefilter("ignore", InsecureRequestWarning)
    resp = requests.get(url, timeout=30, verify=verify_ssl)
    resp.raise_for_status()
    return resp.text


def _largest_text_block(soup: BeautifulSoup):
    best = None
    for div in soup.find_all(["div", "article", "section"]):
        text = div.get_text(" ", strip=True)
        if len(text) < 2000:
            continue
        if best is None or len(text) > best[0]:
            best = (len(text), div)
    return best[1] if best else soup


def extract_main(soup: BeautifulSoup):
    main = soup.find("div", id="container")
    if main is None:
        main = _largest_text_block(soup)
    for tag in main.find_all(["script", "style", "noscript"]):
        tag.decompose()
    return main


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def iter_paragraphs(main) -> List[Paragraph]:
    paragraphs: List[Paragraph] = []
    current_section: Optional[str] = None
    idx = 0

    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if el.find_parent(["nav", "header", "footer", "aside"]):
            continue
        cls = " ".join(el.get("class", []))
        if any(x in cls for x in ["docToolbar", "docNpaInfo", "menu", "breadcrumbs"]):
            continue

        text = clean_text(el.get_text(" ", strip=True))
        if not text:
            continue

        if el.name in {"h1", "h2", "h3", "h4"}:
            current_section = text
            continue

        paragraphs.append(Paragraph(text=text, section=current_section, index=idx))
        idx += 1

    return paragraphs


def save_raw_text(path: str, paragraphs: Iterable[Paragraph]):
    with open(path, "w", encoding="utf-8") as f:
        for p in paragraphs:
            if p.section:
                f.write(f"\n## {p.section}\n")
            f.write(p.text + "\n")


def save_paragraphs_jsonl(path: str, url: str, title: str, paragraphs: Iterable[Paragraph]):
    with open(path, "w", encoding="utf-8") as f:
        for p in paragraphs:
            item = {
                "id": f"p_{p.index}",
                "text": p.text,
                "section": p.section,
                "source_url": url,
                "title": title,
                "paragraph_index": p.index,
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def paragraph_offsets(paragraphs: List[Paragraph]) -> List[int]:
    offsets = []
    pos = 0
    for p in paragraphs:
        offsets.append(pos)
        pos += len(p.text) + 1
    return offsets


def chunk_paragraphs(
    paragraphs: List[Paragraph],
    max_chars: int,
    overlap_paragraphs: int,
):
    offsets = paragraph_offsets(paragraphs)
    chunks = []
    i = 0

    while i < len(paragraphs):
        start = i
        cur = []
        cur_len = 0

        while i < len(paragraphs):
            t = paragraphs[i].text
            if cur and cur_len + len(t) + 1 > max_chars:
                break
            cur.append(t)
            cur_len += len(t) + 1
            i += 1

        end_idx = i - 1
        text = "\n".join(cur).strip()
        char_start = offsets[start]
        char_end = offsets[end_idx] + len(paragraphs[end_idx].text)
        chunks.append((text, char_start, char_end, start, end_idx))

        if overlap_paragraphs > 0:
            i = max(i - overlap_paragraphs, start + 1)

    return chunks


def save_chunks_jsonl(
    path: str,
    url: str,
    title: str,
    paragraphs: List[Paragraph],
    max_chars: int,
    overlap_paragraphs: int,
):
    chunks = chunk_paragraphs(paragraphs, max_chars, overlap_paragraphs)
    with open(path, "w", encoding="utf-8") as f:
        for i, (text, char_start, char_end, p_start, p_end) in enumerate(chunks):
            item = {
                "id": f"c_{i}",
                "text": text,
                "source_url": url,
                "title": title,
                "chunk_index": i,
                "char_start": char_start,
                "char_end": char_end,
                "paragraph_start": p_start,
                "paragraph_end": p_end,
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL_DEFAULT)
    parser.add_argument("--verify-ssl", action="store_true", help="Verify HTTPS certificates")
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap-paragraphs", type=int, default=2)
    parser.add_argument("--out-dir", default="./data")
    args = parser.parse_args()

    html = fetch_html(args.url, verify_ssl=args.verify_ssl)
    soup = BeautifulSoup(html, "lxml")
    main = extract_main(soup)

    title_el = main.find(["h1", "h2"]) or soup.find("title")
    title = clean_text(title_el.get_text(" ", strip=True)) if title_el else ""

    paragraphs = iter_paragraphs(main)
    if not paragraphs:
        raise SystemExit("No paragraphs extracted. Parser needs adjustment.")

    out_dir = args.out_dir
    save_raw_text(f"{out_dir}/act_raw.txt", paragraphs)
    save_paragraphs_jsonl(f"{out_dir}/act_paragraphs.jsonl", args.url, title, paragraphs)
    save_chunks_jsonl(
        f"{out_dir}/act_chunks.jsonl",
        args.url,
        title,
        paragraphs,
        args.max_chars,
        args.overlap_paragraphs,
    )

    print(f"Saved {len(paragraphs)} paragraphs.")


if __name__ == "__main__":
    main()
