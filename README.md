# Cliente LLM asíncrono

Script de validación con clientes de OpenAI, Anthropic y Gemini, una interfaz común y schemas Pydantic.

## Requisitos

- Python 3.10 o superior y pip. El entorno local fue verificado con Python 3.14.
- Conexión a Internet y una API key válida de al menos un proveedor, con acceso al modelo configurado.
- Dependencias de `requirements.txt`: `pydantic>=2`, `python-dotenv`, `openai`, `anthropic` y `google-genai`.

## Instalación en PowerShell

Desde la carpeta `llm-client`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, se puede ejecutar directamente el intérprete del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Variables de entorno y modelos

Si todavía no existe `.env`, crearlo copiando la plantilla:

```powershell
Copy-Item .env.example .env
```

Completar las claves manualmente, sin publicarlas. Los campos vacíos de la plantilla son intencionales.

| Variable | Uso |
| --- | --- |
| `OPENAI_API_KEY` | Clave de OpenAI; necesaria para intentar ese proveedor. |
| `ANTHROPIC_API_KEY` | Clave de Anthropic; necesaria para intentar ese proveedor. |
| `GOOGLE_API_KEY` | Clave de Gemini; necesaria para intentar ese proveedor. |
| `LLM_PROVIDER` | Valor válido de `LLMConfig`: `openai`, `anthropic` o `gemini`. Por defecto `openai`; no cambia el orden fijo del fallback. |
| `LLM_MODEL` | Modelo común obligatorio en el script; se usa cuando no hay un modelo específico para el proveedor. |
| `OPENAI_MODEL` | Modelo opcional de OpenAI; tiene prioridad sobre `LLM_MODEL` para OpenAI. |
| `ANTHROPIC_MODEL` | Modelo opcional de Anthropic; tiene prioridad sobre `LLM_MODEL` para Anthropic. |
| `GEMINI_MODEL` | Modelo opcional de Gemini; tiene prioridad sobre `LLM_MODEL` para Gemini. |

Elegir nombres de modelos disponibles para cada cuenta y compatibles con las APIs utilizadas. Los nombres no son intercambiables entre proveedores, por lo que conviene completar los tres campos específicos para probar todo el fallback. Un proveedor sin clave se considera no disponible y se intenta el siguiente.

El script carga `.env` desde su propia carpeta. Las variables ya presentes en el entorno tienen prioridad. Ambas pruebas usan `max_tokens=1024`, temperatura predeterminada `0.7` y la instrucción de responder en un máximo de tres oraciones. Gemini mapea el límite a `max_output_tokens` y configura `thinking_level=low` únicamente para `gemini-3.5-flash`.

## Ejecución

Con el entorno activado:

```powershell
python main.py
```

Se pregunta «¿Qué es la entropía?» en dos solicitudes independientes:

- **Normal:** espera una respuesta completa y muestra su contenido; internamente devuelve `ModelResponse`.
- **Streaming:** consume el generador con `async for` y muestra cada chunk inmediatamente.

Cada solicitud intenta **OpenAI → Anthropic → Gemini**. Un error controlado o una excepción hace avanzar al siguiente proveedor. Un stream vacío también se considera fallo. Si un stream falla después de emitir texto, ese texto permanece visible y se muestra un mensaje de estado antes de intentar la alternativa. No se agregan retries en el manager; los SDK conservan sus opciones predeterminadas.

Si fallan todos, la generación normal devuelve un error controlado y el streaming termina con el error guardado en `manager.last_response`. La consola muestra mensajes amigables, sin imprimir los detalles técnicos internos.

## Archivos privados y generados

`.gitignore` excluye `.env`, `.venv/`, `__pycache__/`, `*.pyc` y archivos comunes de editor. La plantilla `.env.example` contiene solamente nombres de variables y valores no secretos.

Una vez creado el repositorio Git, comprobar las exclusiones y que estos archivos no estén rastreados:

```powershell
git check-ignore .env .venv/ __pycache__/ ejemplo.pyc
git ls-files -- .env '.venv/**' '**/__pycache__/**' '*.pyc'
```

El segundo comando no debe listar archivos. `.gitignore` no deja de rastrear archivos agregados anteriormente.
