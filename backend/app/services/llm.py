import logging
import os

from fastapi import HTTPException
from openai import OpenAI

logger = logging.getLogger(__name__)

# Singleton — created once at import time, reused for every request
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
    return _client


def call_chat_model(messages, model: str = "gpt-4.1-mini") -> str:
    """
    Calls OpenAI Chat Completions and returns the assistant content.
    Uses response_format=json_object for reliable JSON output.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    try:
        completion = _get_client().chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content

    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        raise HTTPException(status_code=502, detail="AI service error. Please try again.")
