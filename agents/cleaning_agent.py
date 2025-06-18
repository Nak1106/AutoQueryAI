"""
CleaningAgent: Converts NL cleaning requests to pandas code and applies them.
"""
from typing import Any
import streamlit as st

class CleaningAgent:
    def __init__(self, llm, model_type: str = 'groq'):
        self.llm = llm
        self.model_type = model_type

    def nl_to_pandas(self, user_request: str, df_columns: list) -> str:
        prompt = f"""
You are a Python data cleaning assistant. Given the following user request and columns, generate a single line of pandas code to perform the cleaning operation. Do not include comments or explanations.

Columns: {', '.join(df_columns)}
Request: {user_request}
Code:
"""
        if self.model_type == 'groq':
            response = self.llm.invoke(prompt)
            code = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        elif self.model_type == 'hf':
            response = self.llm(prompt, max_new_tokens=64, return_full_text=False)
            code = response[0]['generated_text'].strip() if isinstance(response, list) else str(response).strip()
        else:
            code = ""
        return code

    def apply_cleaning(self, code: str, df: Any):
        try:
            local_vars = {'df': df.copy()}
            exec(code, {}, local_vars)
            return local_vars['df']
        except Exception as e:
            st.session_state["logs"].append(f"[CleaningAgent] Cleaning error: {e}")
            return df
