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

class OllamaClient:
    """LLM backend that calls a local Ollama instance via its OpenAI-compatible endpoint.

    Only the text-output path is used — the agent tool-use loop is skipped because
    Ollama's tool-call reliability varies widely by model. JSON output is requested
    via response_format and reinforced in the system prompt.
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._client = httpx.Client(timeout=180.0)

    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        output_schema: dict[str, Any],
        tools: list[dict[str, Any]] | None = None,
    ) -> _OllamaResponse:
        # Tool-calling is not used with Ollama; the JSON schema in the system prompt is enough.
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
            resp = self._client.post(
                f"{self._base_url}/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": openai_messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "stream": False,
                },
            )
            resp.raise_for_status()
        except httpx.ConnectError as e:
            raise AIError(
                f"Cannot reach Ollama at {self._base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            ) from e
        except httpx.HTTPStatusError as e:
            raise AIError(f"Ollama returned HTTP {e.response.status_code}.") from e

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        finish = data["choices"][0].get("finish_reason", "stop")
        log.info("Ollama response model=%s finish_reason=%s", self._model, finish)
        return _OllamaResponse(text)
