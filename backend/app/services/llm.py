import os
from openai import OpenAI
from fastapi import HTTPException


def call_chat_model(messages, model: str = "gpt-4.1-mini") -> str:
    """
    Calls OpenAI Chat Completions and returns the assistant content.
    Uses response_format=json_object for reliable JSON output.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set"
        )

    try:
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
