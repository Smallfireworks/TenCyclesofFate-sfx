import logging
from typing import Optional

from .config import settings
from . import openai_client

try:
    from . import gemini_client
except Exception:
    gemini_client = None

logger = logging.getLogger(__name__)


async def get_ai_response(
    prompt: str,
    history: Optional[list[dict]] = None,
    model: Optional[str] = None,
    force_json: bool = True,
) -> str:
    """
    Unified AI provider entry.
    settings.AI_PROVIDER: openai|gemini|auto
    Fallback rules:
      - If provider == openai: use OpenAI
      - If provider == gemini: try Gemini, on failure fallback to OpenAI if allowed
      - If provider == auto: prefer Gemini, fallback to OpenAI on any failure
    Additional guards:
      - If BLOCK_GEMINI_IN_MAINLAND and Gemini key/conn fails -> skip Gemini
    """
    provider = (settings.AI_PROVIDER or "openai").lower()

    async def _try_gemini() -> Optional[str]:
        if not gemini_client:
            return None
        if settings.BLOCK_GEMINI_IN_MAINLAND and not settings.GEMINI_API_KEY:
            # Treat as blocked/unavailable
            return None
        try:
            return await gemini_client.get_ai_response(
                prompt=prompt,
                history=history,
                model=getattr(settings, "GEMINI_MODEL", None),
                force_json=force_json,
            )
        except Exception as e:
            logger.warning(f"Gemini not available, will fallback. Reason: {e}")
            return None

    if provider == "openai":
        return await openai_client.get_ai_response(prompt, history, model or settings.OPENAI_MODEL, force_json)

    if provider == "gemini":
        resp = await _try_gemini()
        if resp is not None:
            return resp
        # Fallback to OpenAI if configured to do so
        if settings.AI_PROVIDER_FALLBACK == "openai":
            return await openai_client.get_ai_response(prompt, history, model or settings.OPENAI_MODEL, force_json)
        raise RuntimeError("Gemini provider selected but unavailable, and no fallback configured.")

    # auto
    resp = await _try_gemini()
    if resp is not None:
        return resp
    return await openai_client.get_ai_response(prompt, history, model or settings.OPENAI_MODEL, force_json)

