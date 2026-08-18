import os
from typing import Optional

from app.llm.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "The openai package is required. Install it with: pip install openai"
            ) from exc

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
