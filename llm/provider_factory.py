from __future__ import annotations

from config_models import ProvidersFile
from llm.anthropic_provider import AnthropicProvider
from llm.base import LLMProvider
from llm.gemini_provider import GeminiProvider
from llm.ollama_provider import OllamaProvider
from llm.openai_provider import OpenAIProvider


def make_provider(name: str, model: str | None, providers: ProvidersFile) -> LLMProvider:
    conf = providers.providers.get(name)
    if conf is None:
        raise ValueError(f"Unknown provider: {name}")

    selected_model = model or conf.default_model
    if name == "anthropic":
        return AnthropicProvider(conf.api_key, selected_model, conf.available_models, conf.base_url, conf.timeout)
    if name == "openai":
        return OpenAIProvider(conf.api_key, selected_model, conf.available_models, conf.base_url, conf.timeout)
    if name == "gemini":
        return GeminiProvider(conf.api_key, selected_model, conf.available_models, conf.timeout)
    if name == "ollama":
        return OllamaProvider(conf.base_url, selected_model, conf.available_models)
    raise ValueError(f"Unsupported provider: {name}")

