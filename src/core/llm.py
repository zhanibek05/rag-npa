import json
from typing import Generator

import requests

from .config import LLM_PROVIDER, OLLAMA_URL, OPENAI_API_KEY, OPENAI_BASE_URL


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


def ollama_stream(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    timeout: int = 120,
    url: str = OLLAMA_URL,
) -> Generator[str, None, None]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature},
    }
    with requests.post(url, json=payload, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break


def openai_generate(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    timeout: int = 120,
    api_key: str = OPENAI_API_KEY,
) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is empty. Set it in .env")

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL or None, timeout=timeout)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def openai_stream(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    timeout: int = 120,
    api_key: str = OPENAI_API_KEY,
) -> Generator[str, None, None]:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is empty. Set it in .env")

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL or None, timeout=timeout)
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if token:
            yield token


def generate_text(
    prompt: str,
    model: str,
    provider: str = LLM_PROVIDER,
    temperature: float = 0.2,
    timeout: int = 120,
) -> str:
    if provider == "openai":
        return openai_generate(model=model, prompt=prompt, temperature=temperature, timeout=timeout)
    if provider == "ollama":
        return ollama_generate(model=model, prompt=prompt, temperature=temperature, timeout=timeout)
    raise RuntimeError(f"Unsupported LLM_PROVIDER={provider!r}. Use 'ollama' or 'openai'.")


def stream_text(
    prompt: str,
    model: str,
    provider: str = LLM_PROVIDER,
    temperature: float = 0.2,
    timeout: int = 120,
) -> Generator[str, None, None]:
    if provider == "openai":
        yield from openai_stream(model=model, prompt=prompt, temperature=temperature, timeout=timeout)
    elif provider == "ollama":
        yield from ollama_stream(model=model, prompt=prompt, temperature=temperature, timeout=timeout)
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER={provider!r}. Use 'ollama' or 'openai'.")
