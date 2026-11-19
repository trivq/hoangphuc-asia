# Part of SeaOps. See LICENSE file for full copyright and licensing details.
import requests
from odoo import fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    local_ai_enabled = fields.Boolean(
        string="Enable Local AI Connection",
        config_parameter='ai.local_ai_enabled',
        groups='base.group_system',
    )
    local_base_url = fields.Char(
        string="Local AI Base URL",
        config_parameter='ai.local_base_url',
        readonly=False,
        groups='base.group_system',
    )
    local_api_key = fields.Char(
        string="Local AI API Key",
        config_parameter='ai.local_api_key',
        readonly=False,
        groups='base.group_system',
    )
    local_model = fields.Char(
        string="Local AI Default Model",
        config_parameter='ai.local_model',
        readonly=False,
        groups='base.group_system',
    )

    def action_test_local_ai_connection(self):
        """Test connection to the configured Local LLM endpoint."""
        self.ensure_one()
        url = (self.local_base_url or "").strip().rstrip('/')
        if not url:
            raise UserError("Vui lòng nhập Base URL trước khi kiểm tra kết nối.")

        if not url.endswith('/chat/completions'):
            if url.endswith('/v1'):
                url = f"{url}/chat/completions"
            else:
                url = f"{url}/v1/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.local_api_key:
            headers["Authorization"] = f"Bearer {self.local_api_key.strip()}"

        model = (self.local_model or "").strip() or "llama3"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Xin chào"}],
            "max_tokens": 150,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            reply = ""
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message") or {}
                reply = msg.get("content") or msg.get("reasoning_content") or ""
            reply = str(reply or "").strip()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Kết nối thành công!",
                    "message": f"Model '{model}' phản hồi: {reply[:150]}",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            raise UserError(f"Kết nối thất bại tới {url}:\n{e}")
