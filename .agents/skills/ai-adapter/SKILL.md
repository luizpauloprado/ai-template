---
name: ai-adapter
description: Use when changing the Gemini integration in app/adapters/ai/, adding a generation option (temperature, etc.) to /ai/ask/advanced, or adding a new LLM capability (new port backed by google-genai).
---

# AI adapter (Gemini via google-genai)

## Files

| File | Role |
|---|---|
| `app/adapters/ai/gemini_adapter.py` | `create_client` + `GeminiRetry` (timeout/retry), `to_sdk_config`, `GeminiPricing`, `_log_call`, `ask`, `ask_with_config`, `extract_invoice` |
| `app/domain/models.py` | `GeneratedText` (output), `GenerationConfig` (provider-agnostic options) |
| `app/domain/ports.py` | `Ask`, `AskWithConfig` |
| `app/wires/inbound/ai.py` | `AskIn`, `AskWithConfigIn` (validation bounds) + `to_generation_config` |
| `app/dependencies/ports/ai.py` | `get_ask` / `AskDep`, `get_ask_with_config` / `AskWithConfigDep` |
| `app/dependencies/resources.py` | `get_gemini_client` → 503 when `GEMINI_API_KEY` is empty |

## Rules

- MUST: adapter functions take `client: genai.Client, model: str, pricing: GeminiPricing` first, then the port's arguments. The provider binds all three: `partial(gemini_adapter.<fn>, client, settings.gemini_model, _gemini_pricing(settings))`.
- MUST: log every call with `_log_call(operation, model, pricing, started, response, info)` (`started = time.perf_counter()` before the call). It logs tokens from `response.usage_metadata` and the estimated cost when `GEMINI_*_PRICE_PER_MTOK` are set. `info` holds input sizes only, never prompt/document contents.
- MUST: use the async API: `await client.aio.models.generate_content(...)`.
- MUST: convert SDK responses to domain models (`_to_generated_text`) and never return SDK types. Handle `None` (`response.text or ""`, `response.model_version or model`).
- MUST: keep `GenerationConfig` provider-agnostic. Field names match `types.GenerateContentConfig` so that `to_sdk_config` stays `GenerateContentConfig(**config.model_dump(exclude_none=True))`.
- MUST NOT: import `google.genai` outside `app/adapters/ai/`, `app/dependencies/`, `app/lifespan.py` and `app/main.py`.
- MUST NOT: catch `genai_errors.APIError`. `app/main.py` maps it: 5xx/429 → 503 + `Retry-After`, other → 502; `httpx.TimeoutException` → 504.
- MUST NOT: write retry loops (in adapters or services). Timeout and retry (exponential backoff + jitter on 408/429/5xx/network errors) are configured once in `create_client` via `GeminiRetry` → `types.HttpOptions`, from the `GEMINI_TIMEOUT_SECONDS` / `GEMINI_RETRY_*` settings. Retries are logged by the SDK logger `google_genai._api_client`.
- Services may normalize input (e.g. `prompt.strip()`), but prompt templates/business prompts belong in the service, not in the adapter.

## Recipe: add a generation option (e.g. `presence_penalty`)

Exactly 3 code places, plus tests:

1. `app/domain/models.py`: in `GenerationConfig`, add `presence_penalty: float | None = None`. The name must match the `GenerateContentConfig` field.
2. `app/wires/inbound/ai.py`: in `AskWithConfigIn`, add `presence_penalty: float | None = Field(default=None, ge=-2, le=2)`. `to_generation_config` picks it up automatically.
3. `app/adapters/ai/gemini_adapter.py`: no change while the name matches the SDK. If the SDK name differs, map it explicitly in `to_sdk_config`.
4. Tests: extend `test_to_sdk_config_maps_only_provided_fields` in `tests/unit/test_gemini_adapter.py`. In `tests/acceptance/test_ai_endpoint.py`, assert that the field reaches the port via `fake_ask_with_config(calls)` and that out-of-range values give 422.

## Recipe: add a new LLM capability (e.g. structured summary)

1. Domain model for the output + port in `app/domain/ports.py`, e.g. `Summarize = Callable[[str], Awaitable[Summary]]`.
2. Adapter function in `gemini_adapter.py`:

```python
async def summarize(
    client: genai.Client, model: str, pricing: GeminiPricing, text: str
) -> Summary:
    started = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Summary
        ),
    )
    _log_call("summarize", model, pricing, started, response, f"text_chars={len(text)}")
    return Summary.model_validate_json(response.text or "{}")
```

3. Provider in `app/dependencies/ports/ai.py`:

```python
def get_summarize(client: GeminiClientDep, settings: SettingsDep) -> Summarize:
    return partial(
        gemini_adapter.summarize, client, settings.gemini_model, _gemini_pricing(settings)
    )


SummarizeDep = Annotated[Summarize, Depends(get_summarize)]
```

Re-export both in `app/dependencies/__init__.py`.

4. Service function in `app/services/ai_service.py`, then wires and a route in `app/controllers/ai_controller.py` (see `wires-and-controllers`).
5. Tests: an `AsyncMock` adapter test, a `fake_summarize()` in `tests/fakes.py`, a service unit test, and an acceptance test overriding `deps.get_summarize`.

## Template: adapter unit test

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock


def fake_client(text: str | None, model_version: str | None) -> AsyncMock:
    response = SimpleNamespace(text=text, model_version=model_version)
    client = AsyncMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client
```

Assert the call with `client.aio.models.generate_content.assert_awaited_once_with(model=..., contents=..., config=...)`.

## Verify

```bash
make lint && make test-unit && make test-acceptance
```

Manual check (needs `GEMINI_API_KEY` in `.env`):

```bash
curl -X POST localhost:8000/ai/ask/advanced -H 'content-type: application/json' \
  -d '{"prompt": "hello", "temperature": 0.2, "max_output_tokens": 50}'
```

## Reference implementation

- `app/adapters/ai/gemini_adapter.py`
- `app/dependencies/ports/ai.py`
- `app/controllers/ai_controller.py`
- `tests/unit/test_gemini_adapter.py`, `tests/unit/test_ai_service.py`, `tests/acceptance/test_ai_endpoint.py`
