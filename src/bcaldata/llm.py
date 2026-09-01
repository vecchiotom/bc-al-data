"""Thin vLLM client for the local Qwen3.8-27B (OpenAI-compatible)."""
from __future__ import annotations
import os
from openai import OpenAI

BASE_URL = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:8000/v1")
MODEL = os.environ.get("LOCAL_LLM_MODEL", "qwen3.8-27b-vllm")
_client = OpenAI(base_url=BASE_URL, api_key=os.environ.get("LOCAL_API_KEY", "local"))


def chat(messages: list[dict], *, temperature: float = 0.2, max_tokens: int = 1024,
         reasoning: str = "low") -> str:
    extra = {"chat_template_kwargs": {"reasoning_effort": reasoning}} if reasoning else {}
    r = _client.chat.completions.create(
        model=MODEL, messages=messages, temperature=temperature,
        max_tokens=max_tokens, extra_body=extra,
    )
    return r.choices[0].message.content or ""


def batch(prompts: list[list[dict]], **kw) -> list[str]:
    return [chat(p, **kw) for p in prompts]
