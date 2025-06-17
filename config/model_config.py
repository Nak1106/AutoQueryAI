"""
Model configuration and selector for AutoQueryAI.
"""
import os
from dotenv import load_dotenv

MODELS = {
    'Mistral': 'mistral',
    'HuggingFace': 'hf',
}

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # fallback to .env.template
        template_path = os.path.join(os.path.dirname(__file__), '.env.template')
        if os.path.exists(template_path):
            load_dotenv(template_path)

def get_model_key(model_name: str) -> str:
    load_env()
    if model_name == 'mistral':
        return os.getenv('MISTRAL_API_KEY', '')
    elif model_name == 'hf':
        return os.getenv('HF_API_KEY', '')
    return ''
