# Part of SeaOps. See LICENSE file for full copyright and licensing details.
{
    'name': 'AI — Local LLM',
    'version': '20.0.1.0.0',
    'author': 'Tri Vo',
    'summary': 'Connect Odoo AI to Ollama, vLLM, LM Studio and OpenAI-compatible local LLMs',
    'description': """
        Enables Odoo 20 AI features to connect to local LLM servers (Ollama, vLLM, LM Studio, etc.)
        or custom OpenAI-compatible endpoints without requiring Odoo IAP credits.
    """,
    'category': 'Technical',
    'depends': ['base', 'ai'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
