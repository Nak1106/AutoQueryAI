"""
Chart Agent: Generates chart code or visualization instructions from NL prompts.
"""
from typing import Any, Dict
import streamlit as st
import re

class ChartAgent:
    def __init__(self, llm, model_type: str = 'groq'):
        self.llm = llm
        self.model_type = model_type

    def wants_chart(self, question: str) -> bool:
        # Simple heuristic for demo
        chart_keywords = ["plot", "chart", "visualize", "bar", "line", "pie", "graph"]
        return any(word in question.lower() for word in chart_keywords)

    def prompt_to_chart_code(self, question: str, schema: Dict[str, Any], result_df: Any) -> str:
        prompt = f"""
You are a Python data visualization expert. Given the user's question, the schema, and the result DataFrame, generate Python code using plotly to visualize the result. Only output the code, no explanation.

Schema:
{schema}

Question:
{question}

Result (first rows):
{result_df.head().to_markdown(index=False) if hasattr(result_df, 'head') else str(result_df)}

Plotly Code:
"""
        st.session_state["logs"].append(f"[ChartAgent] Prompt:\n{prompt}")
        if self.model_type == 'groq':
            response = self.llm.invoke(prompt)
            code = response.content if hasattr(response, 'content') else str(response)
        elif self.model_type == 'hf':
            response = self.llm(prompt, max_new_tokens=128, return_full_text=False)
            code = response[0]['generated_text'] if isinstance(response, list) else str(response)
        else:
            code = "import plotly.express as px\nfig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1]); fig.show()"
        st.session_state["logs"].append(f"[ChartAgent] Response:\n{code}")
        return self._extract_code(code)

    def _extract_code(self, text: str) -> str:
        # Extract code block if present
        match = re.search(r'```python(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
