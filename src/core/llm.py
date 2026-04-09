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


def generate_text(
    prompt: str,
    model: str,
    provider: str = LLM_PROVIDER,
    temperature: float = 0.2,
    timeout: int = 120,
) -> str:
    if provider == "openai":
        return openai_generate(
            model=model,
            prompt=prompt,
            temperature=temperature,
            timeout=timeout,
        )
    if provider == "ollama":
        return ollama_generate(
            model=model,
            prompt=prompt,
            temperature=temperature,
            timeout=timeout,
        )
    raise RuntimeError(f"Unsupported LLM_PROVIDER={provider!r}. Use 'ollama' or 'openai'.")
