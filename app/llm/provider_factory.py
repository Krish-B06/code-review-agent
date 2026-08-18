from app.llm.llm_provider import LLMProvider
from app.llm.openai_provider import OpenAIProvider


class ProviderFactory:
    @staticmethod
    def create(provider_name: str = "openai", **kwargs) -> LLMProvider:
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return OpenAIProvider(**kwargs)

        raise ValueError(f"Unsupported LLM provider: {provider_name}")
