"""
LLM Loader: Returns a Mistral or HuggingFace pipeline instance based on model selection.
"""
from transformers import pipeline
import os
import requests

class MistralLLM:
    def __init__(self, api_key: str, model_name: str = "mistral-medium"):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://api.mistral.ai/v1/chat/completions"

    def invoke(self, prompt: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256,
            "temperature": 0.2
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

def get_llm(model_type: str, api_key: str):
    if model_type == 'mistral':
        return MistralLLM(api_key)
    elif model_type == 'hf':
        return pipeline(
            "text-generation",
            model="HuggingFaceH4/zephyr-7b-beta",
            token=api_key,
            max_new_tokens=128
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
