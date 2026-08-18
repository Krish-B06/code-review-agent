import os
from typing import Optional

from app.llm.llm_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required.")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "The anthropic package is required. Install it with: pip install anthropic"
            ) from exc

        self.client = Anthropic(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text or ""
