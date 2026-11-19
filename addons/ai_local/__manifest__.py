# See LICENSE file for full copyright and licensing details.
{
    'name': 'AI — Local LLM',
    'version': '19.0.1.0.0',
    'summary': 'Patch Odoo AI module to support OpenAI-compatible local LLMs',
    'description': """
        Allows Odoo AI module to use any OpenAI-compatible local LLM server
        (Ollama, vLLM, LM Studio, LiteLLM, etc.) by patching LLMApiService
        to use /chat/completions instead of /responses.

        Configuration (Settings > Technical > System Parameters):
            ai.local_base_url  = http://localhost:11434/v1
            ai.local_api_key   = ollama  (or any string if no auth needed)
            ai.local_model     = llama3  (model name your server understands)
    """,
    'category': 'Technical',
    'depends': ['ai', 'ai_app'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'license': 'OPL-1',
}
