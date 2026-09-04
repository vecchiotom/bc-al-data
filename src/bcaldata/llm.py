"""Thin vLLM client for the local Qwen3.8-27B (OpenAI-compatible)."""
from __future__ import annotations
import os
import time
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

BASE_URL = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:8000/v1")
MODEL = os.environ.get("LOCAL_LLM_MODEL", "qwen3.8-27b-vllm")
_client = OpenAI(base_url=BASE_URL, api_key=os.environ.get("LOCAL_API_KEY", "local"))


def chat(messages: list[dict], *, temperature: float = 0.2, max_tokens: int = 1024,
         reasoning: str = "low", timeout: float | None = None) -> str:
    extra = {"chat_template_kwargs": {"reasoning_effort": reasoning}} if reasoning else {}
    r = _client.chat.completions.create(
        model=MODEL, messages=messages, temperature=temperature,
        max_tokens=max_tokens, extra_body=extra, timeout=timeout,
    )
    return r.choices[0].message.content or ""


def _call_once(p: list[dict], timeout: float | None, kw: dict) -> str:
    """One chat() call with a single retry on timeout / 5xx."""
    for attempt in (0, 1):
        try:
            return chat(p, timeout=timeout, **kw)
        except Exception as e:  # noqa: BLE001 - retry once, then re-raise
            msg = str(e).lower()
            retriable = "timeout" in msg or "timed out" in msg or any(
                f" {c}" in msg or f"{c} " in msg for c in ("500", "502", "503", "504"))
            if attempt == 1 or not retriable:
                raise
            time.sleep(1.0)
    return ""  # unreachable


def batch(prompts: list[list[dict]], *, max_workers: int = 3,
          timeout: float | None = 120.0, **kw) -> list[str]:
    """Run `prompts` concurrently, preserving input order.

    Per-call timeout plus one retry on timeout/5xx. An exhausted call re-raises;
    the exception propagates out of `batch` (callers that must not abort the run
    should pass single prompts or catch per row).
    """
    if not prompts:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(lambda p: _call_once(p, timeout, kw), prompts))
