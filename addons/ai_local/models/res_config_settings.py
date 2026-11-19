# Part of SeaOps. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


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

