"""
Chat history and memory management for AutoQueryAI.
"""
from typing import List, Dict, Any
import json
import os

class ChatHistory:
    def __init__(self, history_file: str = None):
        self.history: List[Dict[str, Any]] = []
        self.history_file = history_file
        if history_file and os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)

    def add_message(self, role: str, content: str):
        self.history.append({'role': role, 'content': content})
        if self.history_file:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history
