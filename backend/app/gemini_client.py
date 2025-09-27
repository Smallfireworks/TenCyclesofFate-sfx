import logging
import asyncio
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .config import settings

logger = logging.getLogger(__name__)


def _build_prompt(prompt: str, history: Optional[list[dict]] = None) -> str:
    """Convert chat-style history to a single text prompt for Gemini."""
    parts: list[str] = []
    if history:
        for m in history:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"[系统指令]\n{content}\n")
            elif role == "assistant":
                parts.append(f"[星君答复]\n{content}\n")
            else:
                parts.append(f"[玩家]\n{content}\n")
    parts.append(f"[当前请求]\n{prompt}")
    return "\n\n".join(parts)


async def get_ai_response(
    prompt: str,
    history: Optional[list[dict]] = None,
    model: Optional[str] = None,
    force_json: bool = True,
) -> str:
    """Get response from Google Gemini."""
    if genai is None:
        raise RuntimeError("google-generativeai not installed")

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Configure Gemini
    config_kwargs = {"api_key": api_key}
    if settings.GEMINI_BASE_URL:
        config_kwargs["client_options"] = {"api_endpoint": settings.GEMINI_BASE_URL}
    
    genai.configure(**config_kwargs)

    _model = model or settings.GEMINI_MODEL
    text = _build_prompt(prompt, history)

    def _run_blocking():
        m = genai.GenerativeModel(_model)
        resp = m.generate_content(text)
        return resp.text or ""

    try:
        result_text = await asyncio.to_thread(_run_blocking)
        if not result_text:
            raise ValueError("Empty response from Gemini")
        return result_text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
