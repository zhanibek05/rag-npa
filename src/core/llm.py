import requests

from .config import OLLAMA_URL


def ollama_generate(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    timeout: int = 120,
    url: str = OLLAMA_URL,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()
