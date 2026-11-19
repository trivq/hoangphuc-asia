# Part of SeaOps. See LICENSE file for full copyright and licensing details.
"""
Patch Odoo 20 AI module to support OpenAI-compatible local LLMs (Ollama, vLLM, LM Studio, etc.).

In Odoo 20, all AI interactions (chat, agent loops, completions) flow through:
    odoo.addons.ai.utils.ai_utils.call_odoo_ai_transport
and
    odoo.addons.ai.utils.ai_utils.call_odoo_ai

This patch intercepts those calls when `ai.local_ai_enabled` is True:
1. Translates Odoo 20 Message parts -> OpenAI /chat/completions format.
2. Sends the request to the local server (e.g. Ollama, vLLM, LM Studio).
3. Translates the response back to Odoo 20 AssistantMessage format.
4. For synchronous calls: returns {'result': AssistantMessage}.
5. For asynchronous calls: directly resolves the waiting ai.session state machine.
"""
import json
import logging
import uuid
import requests

import odoo
from odoo import api
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ai.utils import ai_utils
except ImportError:
    _logger.warning("ai_local: Odoo 20 module 'ai' not found or ai_utils missing, patch skipped.")
    ai_utils = None


def _format_endpoint_url(base_url):
    """Normalize base URL to /chat/completions endpoint."""
    url = (base_url or "").strip().rstrip("/")
    if not url:
        return ""
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def _convert_odoo_to_openai_messages(messages, instructions):
    """Convert Odoo 20 messages into OpenAI chat completions payload."""
    openai_messages = []
    if instructions:
        openai_messages.append({"role": "system", "content": instructions})

    for msg in messages or []:
        role = msg.get("role")
        content_parts = msg.get("content")

        if isinstance(content_parts, str):
            openai_messages.append({"role": role or "user", "content": content_parts})
            continue

        text_parts = []
        tool_calls = []

        for part in content_parts or []:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype == "text":
                text_parts.append(part.get("text", ""))
            elif ptype == "tool_call":
                tool_calls.append({
                    "id": str(part.get("call_id") or uuid.uuid4()),
                    "type": "function",
                    "function": {
                        "name": part.get("name"),
                        "arguments": json.dumps(part.get("args") or {}) if isinstance(part.get("args"), dict) else str(part.get("args") or "{}"),
                    },
                })
            elif ptype == "tool_result":
                res_content = ""
                res = part.get("result") or []
                if isinstance(res, list):
                    for rp in res:
                        if isinstance(rp, dict) and rp.get("type") == "text":
                            res_content += rp.get("text", "")
                if not res_content:
                    res_content = json.dumps(res) if not isinstance(res, str) else res
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": str(part.get("tool_call_id") or ""),
                    "content": res_content,
                })

        if role in ("user", "assistant"):
            m = {"role": role}
            if text_parts:
                m["content"] = "".join(text_parts)
            if tool_calls and role == "assistant":
                m["tool_calls"] = tool_calls
            if m.get("content") or m.get("tool_calls"):
                openai_messages.append(m)

    return openai_messages


def _convert_openai_to_odoo_response(choice_message):
    """Convert OpenAI message back into Odoo 20 AssistantMessage structure."""
    content_parts = []
    text = choice_message.get("content")
    if text:
        content_parts.append({"type": "text", "text": text})

    tool_calls = choice_message.get("tool_calls") or []
    for tc in tool_calls:
        fn = tc.get("function") or {}
        raw_args = fn.get("arguments") or "{}"
        try:
            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception:
            parsed_args = raw_args
        content_parts.append({
            "type": "tool_call",
            "name": fn.get("name"),
            "args": parsed_args,
            "call_id": str(tc.get("id") or uuid.uuid4()),
        })

    return {
        "result": {
            "role": "assistant",
            "content": content_parts,
            "provider_metadata": {},
        }
    }


def _call_local_llm(base_url, api_key, model, messages, instructions, tools=None, timeout=60):
    """Dispatch HTTP request to OpenAI-compatible endpoint."""
    url = _format_endpoint_url(base_url)
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model or "llama3",
        "messages": _convert_odoo_to_openai_messages(messages, instructions),
    }
    if tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t.get("name"),
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            }
            for t in tools if isinstance(t, dict) and t.get("name")
        ]

    _logger.info("ai_local: calling %s (model: %s)", url, payload["model"])
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"No choices returned from LLM: {data}")

    return _convert_openai_to_odoo_response(choices[0].get("message") or {})


def _get_param_bool(icp, key):
    """Compatibility getter for boolean parameters across Odoo versions."""
    if hasattr(icp, "get_bool"):
        return icp.get_bool(key)
    if hasattr(icp, "get_param"):
        val = icp.get_param(key)
        return val in (True, "True", "true", "1", 1)
    return False


def _get_param_str(icp, key, default=""):
    """Compatibility getter for string parameters across Odoo versions."""
    if hasattr(icp, "get_str"):
        return icp.get_str(key, default=default)
    if hasattr(icp, "get_param"):
        return icp.get_param(key, default) or default
    return default


def _get_local_config(env=None, dbname=None):
    """Safely fetch local AI configuration parameters using Odoo 20 get_bool / get_str."""
    if env:
        try:
            ICP = env["ir.config_parameter"].sudo()
            enabled = _get_param_bool(ICP, "ai.local_ai_enabled")
            base_url = _get_param_str(ICP, "ai.local_base_url")
            _logger.info("ai_local: env check - enabled=%s, base_url=%s", enabled, base_url)
            if enabled:
                return {
                    "enabled": True,
                    "base_url": base_url,
                    "api_key": _get_param_str(ICP, "ai.local_api_key"),
                    "model": _get_param_str(ICP, "ai.local_model"),
                }
        except Exception as e:
            _logger.warning("ai_local: error reading config from env: %s", e)

    try:
        from odoo.http import request
        if request and hasattr(request, "env") and request.env:
            ICP = request.env["ir.config_parameter"].sudo()
            enabled = _get_param_bool(ICP, "ai.local_ai_enabled")
            base_url = _get_param_str(ICP, "ai.local_base_url")
            _logger.info("ai_local: request.env check - enabled=%s, base_url=%s", enabled, base_url)
            if enabled:
                return {
                    "enabled": True,
                    "base_url": base_url,
                    "api_key": _get_param_str(ICP, "ai.local_api_key"),
                    "model": _get_param_str(ICP, "ai.local_model"),
                }
    except Exception as e:
        _logger.warning("ai_local: error reading config from request.env: %s", e)

    if dbname:
        try:
            registry = Registry(dbname)
            with registry.cursor() as cr:
                env_local = api.Environment(cr, odoo.SUPERUSER_ID, {})
                ICP = env_local["ir.config_parameter"].sudo()
                enabled = _get_param_bool(ICP, "ai.local_ai_enabled")
                base_url = _get_param_str(ICP, "ai.local_base_url")
                _logger.info("ai_local: dbname (%s) check - enabled=%s, base_url=%s", dbname, enabled, base_url)
                if enabled:
                    return {
                        "enabled": True,
                        "base_url": base_url,
                        "api_key": _get_param_str(ICP, "ai.local_api_key"),
                        "model": _get_param_str(ICP, "ai.local_model"),
                    }
        except Exception as e:
            _logger.warning("ai_local: error reading config from dbname %s: %s", dbname, e)

    return {"enabled": False}


if ai_utils:
    _orig_call_odoo_ai_transport = ai_utils.call_odoo_ai_transport
    _orig_call_odoo_ai = ai_utils.call_odoo_ai

    def _patched_call_odoo_ai(env, route, params, add_iap_token=True, timeout=60):
        config = _get_local_config(env=env)
        if config.get("enabled") and config.get("base_url"):
            _logger.info("ai_local: intercepting call_odoo_ai route '%s' via local LLM", route)
            try:
                return _call_local_llm(
                    base_url=config["base_url"],
                    api_key=config.get("api_key"),
                    model=config.get("model"),
                    messages=params.get("messages"),
                    instructions=params.get("instructions"),
                    tools=params.get("tools"),
                    timeout=timeout or 60,
                )
            except Exception as e:
                _logger.exception("ai_local: call_odoo_ai failed: %s", e)
                raise
        return _orig_call_odoo_ai(env, route, params, add_iap_token=add_iap_token, timeout=timeout)

    def _patched_call_odoo_ai_transport(connection, route, params, timeout=30, *, raise_user_error=True):
        dbname = params.get("webhook_dbname") or connection.get("dbuuid")
        config = _get_local_config(dbname=dbname)

        if not config.get("enabled") or not config.get("base_url"):
            _logger.info("ai_local: local AI not enabled or no base_url, falling back to Odoo IAP")
            return _orig_call_odoo_ai_transport(connection, route, params, timeout=timeout, raise_user_error=raise_user_error)

        _logger.info("ai_local: intercepting call_odoo_ai_transport route '%s' via local LLM (%s)", route, config.get("base_url"))
        messages = params.get("messages") or []
        instructions = params.get("instructions") or ""
        tools = params.get("tools")

        try:
            llm_result = _call_local_llm(
                base_url=config["base_url"],
                api_key=config.get("api_key"),
                model=config.get("model"),
                messages=messages,
                instructions=instructions,
                tools=tools,
                timeout=timeout or 60,
            )
        except Exception as e:
            _logger.exception("ai_local: local LLM request failed: %s", e)
            # If local LLM fails, notify the session directly with the error message instead of InsufficientCreditError
            request_uuid = params.get("request_uuid")
            webhook_dbname = params.get("webhook_dbname") or dbname
            if request_uuid and webhook_dbname:
                try:
                    registry = Registry(webhook_dbname)
                    with registry.cursor() as cr:
                        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
                        session = env["ai.session"].search([
                            ("request_uuid", "=", request_uuid),
                            ("loop_state", "=", "waiting_model"),
                        ], limit=1)
                        if session:
                            err_content = f"Lỗi kết nối Local LLM ({config.get('base_url')}): {e}"
                            session._finish_exchange("failed", content=err_content)
                            cr.commit()
                except Exception as clean_err:
                    _logger.exception("ai_local: failed to report local LLM error to session: %s", clean_err)
            return {"success": False}

        if route == "1/get_completions_sync":
            return llm_result

        if route == "1/get_completions":
            request_uuid = params.get("request_uuid")
            webhook_dbname = params.get("webhook_dbname") or dbname
            if request_uuid and webhook_dbname:
                try:
                    registry = Registry(webhook_dbname)
                    with registry.cursor() as cr:
                        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
                        session = env["ai.session"].search([
                            ("request_uuid", "=", request_uuid),
                            ("loop_state", "=", "waiting_model"),
                        ], limit=1)
                        if session:
                            session_env = session._get_completion_env()
                            session.with_env(session_env)._process_completion_result(llm_result)
                            cr.commit()
                            _logger.info("ai_local: successfully resolved async session %s", request_uuid)
                except Exception as e:
                    _logger.exception("ai_local: error processing async session: %s", e)
            return {"success": True}

        return _orig_call_odoo_ai_transport(connection, route, params, timeout=timeout, raise_user_error=raise_user_error)

    ai_utils.call_odoo_ai = _patched_call_odoo_ai
    ai_utils.call_odoo_ai_transport = _patched_call_odoo_ai_transport
    _logger.info("ai_local: successfully patched Odoo 20 AI transport methods")
