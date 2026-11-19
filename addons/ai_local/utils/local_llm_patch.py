# See LICENSE file for full copyright and licensing details.
"""
Patch LLMApiService to support OpenAI-compatible local LLMs.

Odoo AI uses OpenAI's new "Responses API" (/v1/responses), but most local LLM
servers (Ollama, vLLM, LM Studio, LiteLLM) only implement the older
"Chat Completions API" (/v1/chat/completions).

This patch:
  1. Registers a local model in Odoo's provider list so it appears in the UI.
  2. Overrides the base URL to point to the local server.
  3. Translates Odoo's Responses-API calls → Chat Completions format.
  4. Translates Chat Completions responses → Odoo's expected format.

System Parameters to configure (Settings > Technical > System Parameters):
    ai.local_base_url   e.g. http://localhost:11434/v1
    ai.local_api_key    e.g. "ollama" (any string works if server has no auth)
    ai.local_model      e.g. "llama3.2" or "qwen2.5:7b"
"""
import json
import logging

from odoo.addons.ai.utils.llm_providers import PROVIDERS, Provider
from odoo.addons.ai.utils.llm_api_service import LLMApiService

_logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1: Register local model in the openai provider's dropdown list
#
# Why openai? Because Odoo's ai.agent model stores "provider" as one of
# ('openai', 'google'). We piggyback on openai so no DB schema changes needed.
# The local URL/key are stored separately in ir.config_parameter.
# ──────────────────────────────────────────────────────────────────────────────

def _register_local_model():
    """Add local model entries to the OpenAI provider's model list."""
    for provider in PROVIDERS:
        if provider.name == 'openai':
            # provider.llms is a list (mutable despite being in a NamedTuple)
            existing_ids = {m[0] for m in provider.llms}

            local_models = [
                ('local-default', 'Local AI (default model)'),
            ]
            for model_id, model_label in local_models:
                if model_id not in existing_ids:
                    provider.llms.append((model_id, model_label))
                    _logger.info("AI: registered local model '%s' in provider list", model_id)
            break

_register_local_model()


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2: Patch __init__ to detect when we're targeting the local server
#
# Logic:
#   - If provider == 'openai' AND ai.local_base_url is configured
#     → override base_url + enable chat/completions mode
#   - Otherwise → behave normally (real OpenAI)
# ──────────────────────────────────────────────────────────────────────────────

_orig_init = LLMApiService.__init__

def _patched_init(self, env, provider='openai'):
    _orig_init(self, env, provider)
    self._use_chat_completions = False

    if provider == 'openai':
        local_url = env['ir.config_parameter'].sudo().get_param('ai.local_base_url')
        if local_url:
            self.base_url = local_url.rstrip('/')
            self._use_chat_completions = True
            _logger.debug("AI: using local LLM at %s", self.base_url)

LLMApiService.__init__ = _patched_init


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3: Patch _get_api_token to use local key when available
#
# When local_base_url is set, try ai.local_api_key first.
# If not set, fall through to the normal openai key logic.
# ──────────────────────────────────────────────────────────────────────────────

_orig_get_api_token = LLMApiService._get_api_token

def _patched_get_api_token(self):
    if getattr(self, '_use_chat_completions', False):
        local_key = self.env['ir.config_parameter'].sudo().get_param('ai.local_api_key')
        if local_key:
            return local_key
    return _orig_get_api_token(self)

LLMApiService._get_api_token = _patched_get_api_token


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4: Patch _request_llm to dispatch to our chat/completions handler
# ──────────────────────────────────────────────────────────────────────────────

_orig_request_llm = LLMApiService._request_llm

def _patched_request_llm(self, *args, **kwargs):
    if getattr(self, '_use_chat_completions', False):
        return self._request_llm_chat_completions(*args, **kwargs)
    return _orig_request_llm(self, *args, **kwargs)

LLMApiService._request_llm = _patched_request_llm


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5: Add the actual chat/completions request method
#
# Translates from Odoo's Responses API format to Chat Completions format.
#
# Odoo Responses API body:
#   { "model": "...",
#     "input": [
#       {"role": "system", "content": [{"type": "input_text", "text": "..."}]},
#       {"role": "user",   "content": [{"type": "input_text", "text": "..."}]},
#     ],
#     "tools": [{"type": "function", "name": "...", "strict": True, ...}] }
#
# Chat Completions body:
#   { "model": "...",
#     "messages": [
#       {"role": "system", "content": "..."},
#       {"role": "user",   "content": "..."},
#     ],
#     "tools": [{"type": "function", "function": {"name": "...", ...}}] }
# ──────────────────────────────────────────────────────────────────────────────

def _request_llm_chat_completions(
    self, llm_model, system_prompts, user_prompts, tools=None,
    files=None, schema=None, temperature=0.2, inputs=(), web_grounding=False
):
    """Send a chat/completions request to the local LLM server."""

    # Resolve actual model name from config (allows 'local-default' → real name)
    actual_model = self.env['ir.config_parameter'].sudo().get_param('ai.local_model') or llm_model

    # ── Build messages ────────────────────────────────────────────────────────
    messages = []

    # System prompt (combine all into one message)
    if system_prompts:
        messages.append({
            "role": "system",
            "content": "\n\n".join(system_prompts),
        })

    # History: inputs come in as tool responses or previous assistant messages.
    # They are already in Chat Completions format because we built them that way
    # in _patched_build_tool_call_response below.
    for inp in (inputs or []):
        messages.append(inp)

    # User message (combine text + file content)
    user_parts = list(user_prompts)
    if files:
        for f in files:
            if f.get("mimetype") == "text/plain":
                user_parts.append(f["value"])
            # Note: images/PDFs are skipped — most local models don't support them

    messages.append({
        "role": "user",
        "content": "\n\n".join(user_parts),
    })

    # ── Build request body ────────────────────────────────────────────────────
    body = {
        "model": actual_model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,  # CRITICAL: prevent streaming (NDJSON) response
    }

    # Structured output via JSON schema (not all local models support this)
    if schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "schema": schema,
                "strict": True,
            },
        }

    # Tools — translate from Odoo's format to Chat Completions format
    if tools:
        body["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": tool_parameter_schema,
                },
            }
            for tool_name, (tool_description, __, __, tool_parameter_schema) in tools.items()
        ]
        body["tool_choice"] = "auto"

    # ── Make the HTTP request ─────────────────────────────────────────────────
    # Local/remote LLMs can take much longer than 30s (default) to generate.
    # Use a configurable timeout, defaulting to 300s (5 minutes).
    timeout = int(self.env['ir.config_parameter'].sudo().get_param('ai.local_timeout', '300'))
    _logger.debug("AI: POST %s/chat/completions model=%s timeout=%ss", self.base_url, actual_model, timeout)
    response = self._request(
        method="post",
        endpoint="/chat/completions",
        headers=self._get_base_headers(),
        body=body,
        timeout=timeout,
    )

    return self._parse_chat_completions_response(response, tools, inputs)


def _parse_chat_completions_response(self, response, tools=None, inputs=()):
    """
    Parse a /chat/completions response into Odoo's expected 3-tuple:
        (text_responses, tools_to_call, next_inputs)

    Chat Completions response format:
        { "choices": [{
            "message": {
                "role": "assistant",
                "content": "text response OR null if tool call",
                "tool_calls": [{
                    "id": "call_abc123",
                    "type": "function",
                    "function": { "name": "...", "arguments": "{...}" }
                }]
            }
        }] }
    """
    choices = response.get("choices") or []
    if not choices:
        _logger.warning("AI: empty choices in response: %s", response)
        return [], [], list(inputs or [])

    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []

    text_responses = []
    to_call = []
    next_inputs = list(inputs or [])

    if tool_calls:
        # Add the assistant's message (with tool_calls) to conversation history
        # so the model knows what tools it already called
        next_inputs.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        })

        for tc in tool_calls:
            fn = tc.get("function") or {}
            tool_name = fn.get("name", "")
            call_id = tc.get("id") or tool_name

            try:
                arguments = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                _logger.error("AI: malformed tool arguments: %s", fn)
                arguments = {}

            # Clean up empty or falsy __end_message to prevent early termination
            # with an empty response (ValueError: Processing loop ended with no response).
            if "__end_message" in arguments:
                val = arguments["__end_message"]
                if not val or (isinstance(val, str) and not val.strip()):
                    arguments.pop("__end_message")

            to_call.append((tool_name, call_id, arguments))

    elif content:
        text_responses.append(content)

    return text_responses, to_call, next_inputs


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6: Patch _build_tool_call_response
#
# After a tool runs, Odoo appends the result to "inputs" for the next LLM call.
# Format differs between providers:
#
# Responses API (OpenAI):
#   { "type": "function_call_output", "call_id": "...", "output": "..." }
#
# Chat Completions:
#   { "role": "tool", "tool_call_id": "...", "content": "..." }
# ──────────────────────────────────────────────────────────────────────────────

_orig_build_tool_call_response = LLMApiService._build_tool_call_response

def _patched_build_tool_call_response(self, tool_call_id, return_value):
    if getattr(self, '_use_chat_completions', False):
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": str(return_value),
        }
    return _orig_build_tool_call_response(self, tool_call_id, return_value)


# ──────────────────────────────────────────────────────────────────────────────
# Apply all patches to the LLMApiService class
# ──────────────────────────────────────────────────────────────────────────────

LLMApiService._request_llm_chat_completions = _request_llm_chat_completions
LLMApiService._parse_chat_completions_response = _parse_chat_completions_response
LLMApiService._build_tool_call_response = _patched_build_tool_call_response

_logger.info("AI Local LLM patch loaded successfully.")
