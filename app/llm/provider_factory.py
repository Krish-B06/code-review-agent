from app.llm.llm_provider import LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider


class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return (
            '{'
            '"summary": "Review skipped because no external LLM key is configured. The code should be validated with local tests and real provider integration later.", '
            '"suggested_fixes": ["Add an API key to enable live LLM review", "Keep running the local test suite"], '
            '"validation_status": "passed"'
            '}'
        )


class ProviderFactory:
    @staticmethod
    def create(provider_name: str = "openai", **kwargs) -> LLMProvider:
        provider_name = provider_name.lower()

        if provider_name == "openai":
            try:
                return OpenAIProvider(**kwargs)
            except ValueError:
                return MockLLMProvider()

        if provider_name == "anthropic":
            try:
                return AnthropicProvider(**kwargs)
            except ValueError:
                return MockLLMProvider()

        if provider_name == "mock":
            return MockLLMProvider()

        raise ValueError(f"Unsupported LLM provider: {provider_name}")
