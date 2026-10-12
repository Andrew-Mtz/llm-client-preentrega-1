import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from schemas import ChatMessage, LLMConfig, Provider
from services.llm_service import AsyncLLMManager


async def main():
    print("Preparando request...")
    await asyncio.to_thread(load_dotenv, Path(__file__).resolve().parent / ".env")

    try:
        model = os.getenv("LLM_MODEL", "").strip()
        if not model:
            raise ValueError("Completá LLM_MODEL en .env con un modelo del proveedor elegido.")
        config = LLMConfig(
            provider=Provider(os.getenv("LLM_PROVIDER", "openai").strip().lower()),
            model=model,
            max_tokens=1024,
            openai_model=os.getenv("OPENAI_MODEL", "").strip() or None,
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "").strip() or None,
            gemini_model=os.getenv("GEMINI_MODEL", "").strip() or None,
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip() or None,
            google_api_key=os.getenv("GOOGLE_API_KEY", "").strip() or None,
        )
        manager = AsyncLLMManager(config, on_status=lambda message: print(f"\n{message}", flush=True))
    except ValidationError:
        print("Error de configuración: revisá los valores de LLMConfig en .env.")
        return
    except ValueError:
        print("Revisá el proveedor y el modelo configurados en .env.")
        return
    except Exception:
        print("No se pudo preparar la solicitud. Revisá la configuración.")
        return

    messages = [
        ChatMessage(
            role="system",
            content="Respondé de forma clara y concisa, en un máximo de 3 oraciones.",
        ),
        ChatMessage(role="user", content="¿Qué es la entropía?"),
    ]

    print("Respuesta normal:")
    print("Estableciendo conexión...")
    try:
        response = await manager.generate(messages)
        if response.error is not None:
            print("No hay proveedores disponibles. Intentá nuevamente más tarde.")
        else:
            print("Generando respuesta...")
            print(response.content)
    except Exception:
        print("No se pudo generar la respuesta.")

    print("\nRespuesta en streaming:")
    print("Generando respuesta...")
    try:
        async for chunk in manager.generate_stream(messages):
            print(chunk, end="", flush=True)
        if manager.last_response is not None and manager.last_response.error is not None:
            print("\nNo hay proveedores disponibles. Intentá nuevamente más tarde.")
    except Exception:
        print("\nNo se pudo completar la respuesta.")
    finally:
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nValidación interrumpida.")
