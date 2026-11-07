"""Thin wrapper over the Anthropic SDK so the agent code can be tested with a fake."""

import json
import logging
from typing import Any, Protocol

import anthropic
import httpx

from plainspeak.config import Settings

log = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AIError(RuntimeError):
    """Claude could not produce a usable response. The message is safe to show users."""


class LLM(Protocol):
    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        output_schema: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any: ...


class ClaudeClient:
    def __init__(self, settings: Settings) -> None:
        # With no explicit key the SDK resolves ANTHROPIC_API_KEY / an `ant auth login` profile.
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
        self._model = settings.anthropic_model
        self._effort = settings.anthropic_effort
        self._fallbacks = settings.anthropic_fallbacks

    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        output_schema: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        output_config: dict[str, Any] = {"format": {"type": "json_schema", "schema": output_schema}}
        if self._effort:
            output_config["effort"] = self._effort
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 16000,
            "system": system,
            "messages": messages,
            "output_config": output_config,
        }
        if tools:
            kwargs["tools"] = tools
        try:
            if self._fallbacks:
                response = self._client.beta.messages.create(
                    **kwargs, fallbacks=self._fallbacks, betas=[FALLBACK_BETA]
                )
            else:
                response = self._client.messages.create(**kwargs)
        except anthropic.AuthenticationError as e:
            raise AIError("Anthropic credentials are missing or invalid.") from e
        except TypeError as e:
            # The SDK raises TypeError when no credential source can be resolved.
            if "authentication" not in str(e):
                raise
            raise AIError(
                "Anthropic credentials are missing. Set ANTHROPIC_API_KEY in .env."
            ) from e
        except anthropic.RateLimitError as e:
            raise AIError("Claude is rate limited. Try again shortly.") from e
        except anthropic.BadRequestError as e:
            log.error("Claude rejected the request: %s", e.message)
            raise AIError("Claude rejected the request. Check the server log.") from e
        except anthropic.APIStatusError as e:
            log.error("Claude API error %s (request %s)", e.status_code, e.request_id)
            raise AIError(f"Claude API error ({e.status_code}).") from e
        except anthropic.APIConnectionError as e:
            raise AIError("Could not reach the Claude API.") from e
        log.info("Claude response %s stop_reason=%s", response.id, response.stop_reason)
        return response


def parse_json_output(response: Any) -> dict[str, Any]:
    """Read the structured JSON result from a final (non-tool-use) response."""
    if response.stop_reason == "refusal":
        raise AIError("The AI declined to answer this request.")
    if response.stop_reason == "max_tokens":
        raise AIError("The AI response was cut off.")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise AIError("The AI returned no text output.")
    # Strip markdown code fences that some models wrap JSON in
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise AIError("The AI returned invalid JSON.") from e


# ── Anthropic-compatible response wrappers for Ollama ─────────────────────────

class _TextBlock:
    """Minimal Anthropic TextBlock lookalike."""
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _OllamaResponse:
    """Wraps an Ollama chat response in the Anthropic Message interface."""

    def __init__(self, text: str) -> None:
        self.id = "ollama"
        self.stop_reason = "end_turn"
        self.content = [_TextBlock(text)]


# ── Ollama client ──────────────────────────────────────────────────────────────

class OpenAICompatClient:
    """Generic LLM backend for any OpenAI-compatible endpoint (Ollama, Groq, Together AI…).

    Tool-calling is not used — JSON output is requested via response_format and reinforced
    in the system prompt, which works reliably across all compatible providers.
    """

    def __init__(self, base_url: str, model: str, api_key: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._completions_url = self._base_url + "/v1/chat/completions"
        self._model = model
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        output_schema: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> _OllamaResponse:
        # Tool-calling is not used; the JSON schema in the system prompt is enough.
        if tools:
            log.debug("Ollama: %d tool definition(s) ignored (not supported)", len(tools))
        # Flatten Anthropic-format content blocks to plain text for Ollama
        openai_messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    system
                    + "\n\n# Output format\nRespond with ONLY a single valid JSON object — "
                    "no markdown fences, no explanation. The JSON must conform to this schema:\n"
                    + json.dumps(output_schema, indent=2)
                ),
            }
        ]
        for msg in messages:
            content = msg["content"]
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict):
                        btype = block.get("type", "")
                        if btype == "text":
                            parts.append(block.get("text", ""))
                        elif btype == "tool_result":
                            parts.append(f"[Tool result] {block.get('content', '')}")
                        elif btype == "tool_use":
                            parts.append(f"[Tool call: {block.get('name', '')}]")
                    elif hasattr(block, "type"):
                        if block.type == "text":
                            parts.append(block.text)
                        elif block.type == "tool_use":
                            parts.append(f"[Tool call: {block.name}]")
                text = "\n".join(filter(None, parts))
            else:
                text = str(content)
            openai_messages.append({"role": msg["role"], "content": text})

        try:
            with httpx.Client(timeout=180.0, headers=self._headers) as client:
                resp = client.post(
                    self._completions_url,
                    json={
                        "model": self._model,
                        "messages": openai_messages,
                        # response_format omitted — many free models reject it at the
                        # connection level; the system prompt already enforces JSON output.
                        "temperature": 0.1,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError as e:
            raise AIError(
                f"Cannot reach AI backend at {self._base_url}. "
                "Check your connection or restart Ollama with `ollama serve`."
            ) from e
        except httpx.TimeoutException as e:
            raise AIError(
                "AI request timed out — the model may be busy. Try again in a moment."
            ) from e
        except httpx.HTTPStatusError as e:
            body_text = ""
            try:
                body_text = e.response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            msg = f"AI backend returned HTTP {e.response.status_code}"
            raise AIError(f"{msg}: {body_text}" if body_text else msg) from e
        except httpx.RequestError as e:
            raise AIError(f"AI backend connection error ({type(e).__name__}).") from e

        choices = data.get("choices")
        if not choices:
            err_msg = data.get("error", {})
            if isinstance(err_msg, dict):
                err_msg = err_msg.get("message", str(data))
            log.error("OpenAI-compat no choices: %s", err_msg)
            raise AIError(f"AI backend error: {err_msg}")
        text = choices[0]["message"]["content"]
        finish = choices[0].get("finish_reason", "stop")
        log.info("OpenAI-compat response model=%s finish_reason=%s", self._model, finish)
        return _OllamaResponse(text)


class OllamaClient(OpenAICompatClient):
    """Local Ollama instance."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings.ollama_base_url, settings.ollama_model)


class GroqClient(OpenAICompatClient):
    """Groq cloud inference — fast, free tier, OpenAI-compatible."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            "https://api.groq.com/openai",
            settings.groq_model,
            settings.groq_api_key,
        )


class OpenRouterClient(OpenAICompatClient):
    """OpenRouter — free cloud inference across 100+ models."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            "https://openrouter.ai/api",
            settings.openrouter_model,
            settings.openrouter_api_key,
        )


class GeminiClient(OpenAICompatClient):
    """Google Gemini via AI Studio — free tier, 1 500 req/day, OpenAI-compatible."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            "https://generativelanguage.googleapis.com/v1beta/openai",
            settings.gemini_model,
            settings.gemini_api_key,
        )
        # Gemini's path omits the /v1 prefix used by other providers
        self._completions_url = (
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        )
