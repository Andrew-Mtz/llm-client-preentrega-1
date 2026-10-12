from google import genai
from google.genai import types

from typing import AsyncGenerator, List
from .base import BaseLLMClient
from schemas import Provider, ChatMessage, ModelResponse


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _convertir_mensajes(self, messages: List[ChatMessage]):
        """Gemini separa el system prompt del resto, y llama 'model' al rol del asistente."""
        contents = []
        system_instruction = None
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                rol_gemini = "model" if m.role == "assistant" else "user"
                contents.append(types.Content(role=rol_gemini, parts=[types.Part(text=m.content)]))
        return contents, system_instruction

    async def generate(self, messages: List[ChatMessage]) -> ModelResponse:
        try:
            contents, system_instruction = self._convertir_mensajes(messages)
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    system_instruction=system_instruction,
                    thinking_config=(
                        types.ThinkingConfig(thinking_level="low")
                        if self.model.removeprefix("models/") == "gemini-3.5-flash"
                        else None
                    ),
                ),
            )
            text = response.text
            return ModelResponse(provider=Provider.GEMINI, model=self.model, content=text)
        except Exception as e:
            return ModelResponse(provider=Provider.GEMINI, model=self.model, content="",
                                  error=f"Error de la API de Gemini: {e}")

    async def generate_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        try:
            contents, system_instruction = self._convertir_mensajes(messages)
            stream = await self._client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    system_instruction=system_instruction,
                    thinking_config=(
                        types.ThinkingConfig(thinking_level="low")
                        if self.model.removeprefix("models/") == "gemini-3.5-flash"
                        else None
                    ),
                ),
            )
            emitted_text = False
            finish_reason = None
            block_reason = None
            async for chunk in stream:
                if chunk.candidates:
                    finish_reason = chunk.candidates[0].finish_reason or finish_reason
                if chunk.prompt_feedback:
                    block_reason = chunk.prompt_feedback.block_reason or block_reason
                text = chunk.text
                if text:
                    emitted_text = True
                    yield text
            if not emitted_text:
                raise RuntimeError(
                    "Gemini terminó el stream sin texto "
                    f"(finish_reason={finish_reason}, block_reason={block_reason})"
                )
        except Exception as e:
            raise
