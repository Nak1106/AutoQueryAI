"""
Explainer Agent: Explains code and results using LLMs.
"""
from typing import Any
import streamlit as st

class ExplainerAgent:
    def __init__(self, llm, model_type: str = 'groq'):
        self.llm = llm
        self.model_type = model_type

    def explain(self, sql: str, result: Any) -> str:
        if not sql or not sql.strip() or sql.strip().lower() in ["none", "null", "", "-- error:"]:
            st.session_state["logs"].append("[ExplainerAgent] No valid SQL to explain.")
            return "I didn't receive a valid query to explain. Please try rephrasing your question."
        prompt = f"""
You are a helpful data analyst. Given the following SQL query and its result, do two things:
1. Briefly describe in plain English what the query is doing (e.g., 'This query finds the vendor with the most customers.').
2. Provide a one-line business insight from the result (e.g., 'Vendor 2 received the highest number of customers: 88,327.').

Format your answer as:
**Query Description:** <description>
**Business Insight:** <insight>

SQL Query:
{sql}

Result (first rows):
{str(result)}

Explanation:
"""
        st.session_state["logs"].append(f"[ExplainerAgent] Prompt:\n{prompt}")
        if self.model_type == 'groq':
            response = self.llm.invoke(prompt)
            explanation = response.content if hasattr(response, 'content') else str(response)
        elif self.model_type == 'hf':
            response = self.llm(prompt, max_new_tokens=128, return_full_text=False)
            explanation = response[0]['generated_text'] if isinstance(response, list) else str(response)
        else:
            explanation = "No explanation available."
        st.session_state["logs"].append(f"[ExplainerAgent] Response:\n{explanation}")
        return explanation.strip()
