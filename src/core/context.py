from typing import Dict, List


def build_context(chunks: List[Dict], max_chars: int = 3000) -> str:
    parts = []
    total = 0
    for i, chunk in enumerate(chunks, start=1):
        text = chunk["text"].strip()
        block = f"[Источник {i}]\n{text}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)

