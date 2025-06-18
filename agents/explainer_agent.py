"""
Explainer Agent: Explains code and results using LLMs.
"""
from typing import Any
import re
import streamlit as st

class ExplainerAgent:
    def __init__(self, llm, model_type: str = 'groq'):
        self.llm = llm
        self.model_type = model_type

    def explain(self, sql: str, result: Any) -> str:
        if not sql or sql.strip().lower() in ["none", "null", "", "-- error:"]:
            st.session_state["logs"].append("[ExplainerAgent] No valid SQL to explain.")
            return "**Explanation:** No recent query found. Try asking something like 'Show total fare by payment type.'"
        # Direct explanation for single aggregate or group by queries
        agg_match = re.match(r"SELECT\\s+(MAX|MIN|AVG|SUM|COUNT)\\((.*?)\\)\\s+FROM", sql.strip(), re.IGNORECASE)
        group_by_match = re.search(r"GROUP BY\\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
        if agg_match:
            agg_func = agg_match.group(1).upper()
            col = agg_match.group(2).strip()
            value = None
            if hasattr(result, 'iloc') and result.shape[1] == 1 and not result.empty:
                value = result.iloc[0,0]
            elif hasattr(result, 'values') and len(result.values) > 0:
                value = result.values[0][0]
            if value is not None:
                if agg_func == 'MAX':
                    return f"**Query Description:** This query finds the highest value in the '{col}' column.\n**Business Insight:** The highest {col.replace('_',' ')} is {value}."
                elif agg_func == 'MIN':
                    return f"**Query Description:** This query finds the lowest value in the '{col}' column.\n**Business Insight:** The lowest {col.replace('_',' ')} is {value}."
                elif agg_func == 'AVG':
                    return f"**Query Description:** This query calculates the average of the '{col}' column.\n**Business Insight:** The average {col.replace('_',' ')} is {value}."
                elif agg_func == 'SUM':
                    return f"**Query Description:** This query sums all values in the '{col}' column.\n**Business Insight:** The total {col.replace('_',' ')} is {value}."
                elif agg_func == 'COUNT':
                    return f"**Query Description:** This query counts the number of rows in the dataset.\n**Business Insight:** The total number of rows is {value}."
        elif group_by_match and hasattr(result, 'head') and not result.empty:
            group_col = group_by_match.group(1)
            # Try to get the top group and value
            if hasattr(result, 'columns') and result.shape[0] > 0:
                top_row = result.iloc[0]
                group_val = top_row[0]
                metric_val = top_row[1] if len(top_row) > 1 else None
                return f"**Query Description:** This query groups the data by '{group_col}' and aggregates a metric.\n**Business Insight:** The most common {group_col.replace('_',' ')} is {group_val} with a value of {metric_val}."
        # Fallback: if result is empty
        if not result or (hasattr(result, 'empty') and result.empty):
            return "**Explanation:** No meaningful data returned."
        # Fallback to LLM prompt
        prompt = f"""
You are a helpful data analyst. Given the following SQL query and its result, do two things:
1. Briefly describe in plain English what the query is doing (e.g., 'This query finds the vendor with the most customers.').
2. Provide a one-line business insight from the result (e.g., 'Vendor 2 received the highest number of customers: 88,327.').

Format your answer as:
**Query Description:** <description>
**Business Insight:** <insight>

---

SQL Query:
{sql}

Result (first rows):
{result.head().to_markdown(index=False) if hasattr(result, 'head') else str(result)}

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
        if not explanation or 'no explanation available' in explanation.lower():
            return "**Explanation:** Could not generate a meaningful explanation for this query."
        return explanation.strip()
