from typing import AsyncGenerator, Callable, List, Optional

from clients import BaseLLMClient, OpenAIClient, AnthropicClient, GeminiClient
from schemas import LLMConfig, Provider, ChatMessage, ModelResponse


class AsyncLLMManager:
    _providers = (Provider.OPENAI, Provider.ANTHROPIC, Provider.GEMINI)

    def __init__(self, config: LLMConfig, on_status: Optional[Callable[[str], None]] = None):
        self.config = config
        self.on_status = on_status
        self.last_response: Optional[ModelResponse] = None

    def _status(self, message: str):
        if self.on_status is not None:
            self.on_status(message)

    def _model(self, provider: Provider) -> str:
        return getattr(self.config, f"{provider.value}_model") or self.config.model

    def _crear_cliente(self, provider: Provider) -> BaseLLMClient:
        client_class, key = {
            Provider.OPENAI: (OpenAIClient, self.config.openai_api_key),
            Provider.ANTHROPIC: (AnthropicClient, self.config.anthropic_api_key),
            Provider.GEMINI: (GeminiClient, self.config.google_api_key),
        }[provider]
        if not key or not key.get_secret_value().strip():
            raise ValueError(f"Falta API key para {provider.value}")
        return client_class(
            api_key=key.get_secret_value(),
            model=self._model(provider),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

    def _attempt(self, provider: Provider):
        name = {Provider.OPENAI: "OpenAI", Provider.ANTHROPIC: "Anthropic", Provider.GEMINI: "Gemini"}[provider]
        self._status(f"Intentando con {name}...")

    def _failed(self, provider: Provider):
        if provider != self._providers[-1]:
            self._status("Proveedor no disponible, intentando alternativa...")

    def _failure_response(self, errors: List[str]) -> ModelResponse:
        return ModelResponse(
            provider=Provider.GEMINI,
            model=self._model(Provider.GEMINI),
            content="",
            error="; ".join(errors),
        )

    async def generate(self, messages: List[ChatMessage]) -> ModelResponse:
        self.last_response = None
        errors = []
        for provider in self._providers:
            self._attempt(provider)
            try:
                client = self._crear_cliente(provider)
                response = await client.generate(messages)
                if response.error is None:
                    self.last_response = response
                    return response
                errors.append(f"{provider.value}: {response.error}")
            except Exception as error:
                errors.append(f"{provider.value}: {error}")
            self._failed(provider)
        self.last_response = self._failure_response(errors)
        return self.last_response

    async def generate_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        self.last_response = None
        errors = []
        for provider in self._providers:
            self._attempt(provider)
            chunks = []
            try:
                client = self._crear_cliente(provider)
                async for chunk in client.generate_stream(messages):
                    if chunk:
                        chunks.append(chunk)
                        yield chunk
                if not chunks:
                    raise RuntimeError("El proveedor terminó el stream sin texto")
                self.last_response = ModelResponse(
                    provider=provider, model=self._model(provider), content="".join(chunks)
                )
                return
            except Exception as error:
                errors.append(f"{provider.value}: {error}")
            self._failed(provider)
        self.last_response = self._failure_response(errors)
