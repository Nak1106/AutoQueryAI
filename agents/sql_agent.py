"""
SQL Agent: Converts natural language to SQL or pandas code using LLMs.
"""
from typing import Any, Dict, List
import streamlit as st
import time
import re

FEW_SHOT_EXAMPLES = """
User: Show total sales by country
SQL: SELECT country, SUM(sales) FROM data GROUP BY country;

User: List all customers from France
SQL: SELECT * FROM data WHERE country = 'France';

User: Show average order value by year
SQL: SELECT strftime('%Y', order_date) AS year, AVG(order_value) FROM data GROUP BY year;

User: Now show by product
SQL: SELECT product, AVG(order_value) FROM data GROUP BY product;

User: Show the top 5 categories by revenue
SQL: SELECT category, SUM(revenue) FROM data GROUP BY category ORDER BY SUM(revenue) DESC LIMIT 5;

User: Show all orders in 2023 over $100
SQL: SELECT * FROM orders WHERE order_date >= '2023-01-01' AND total > 100;

User: List customers and their order totals
SQL: SELECT c.name, SUM(o.total) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name;

User: Show customers who spent more than average
SQL: SELECT name FROM customers WHERE total > (SELECT AVG(total) FROM customers);
"""

class SQLAgent:
    def __init__(self, llm, model_type: str = 'mistral'):
        self.llm = llm
        self.model_type = model_type  # 'mistral' or 'hf'

    def nl_to_sql(self, question: str, schema: Dict[str, Any], chat_history: List[Dict[str, str]], prefer_pandas: bool = False) -> str:
        if not schema or not schema.get('columns'):
            st.session_state["logs"].append("[SQLAgent] Error: Empty or malformed schema.")
            return "-- Error: No schema available."

        schema_str = self._schema_to_str(schema)
        chat_str = self._chat_history_to_str(chat_history)

        prompt = f"""
You are a helpful data analyst. Based on the database schema and user's natural language question, generate a {'pandas' if prefer_pandas else 'SQL'} query.

Schema:
{schema_str}

Chat History:
{chat_str}

Here are some example questions and queries:
{FEW_SHOT_EXAMPLES}

IMPORTANT: Assume the SQL engine is DuckDB. Use EXTRACT(HOUR FROM timestamp) instead of strftime. Output ONLY the raw query with NO explanation, markdown, or code blocks. Do NOT wrap in triple backticks or include any commentary.

Question:
{question}

{'Pandas Code:' if prefer_pandas else 'SQL Query:'}
"""

        t0 = time.time()
        st.session_state["logs"].append(f"[SQLAgent] Prompt (model={self.model_type}, len={len(prompt)}):\n{prompt}")
        try:
            if self.model_type == 'mistral':
                response = self.llm.invoke(prompt)
            elif self.model_type == 'hf':
                response = self.llm(prompt, max_new_tokens=128, return_full_text=False)
            else:
                response = "SELECT * FROM data LIMIT 5;"

            t1 = time.time()
            raw_output = response if isinstance(response, str) else (response[0]['generated_text'] if isinstance(response, list) else str(response))
            st.session_state["logs"].append(f"[SQLAgent] Response (time={t1 - t0:.2f}s):\n{raw_output}")
            return self._extract_sql(raw_output)

        except Exception as e:
            st.session_state["logs"].append(f"[SQLAgent] Error: {e}")
            return f"-- Error: {e}"

    def nl_to_pandas(self, question: str, schema: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
        return self.nl_to_sql(question, schema, chat_history, prefer_pandas=True)

    def _schema_to_str(self, schema: Dict[str, Any]) -> str:
        if not schema:
            return ""
        cols = [f"{col['name']} ({col['dtype']})" for col in schema.get('columns', [])]
        return f"Columns: {', '.join(cols)}; Rows: {schema.get('num_rows', 0)}"

    def _chat_history_to_str(self, chat_history: List[Dict[str, str]]) -> str:
        if not chat_history:
            return ""
        return '\n'.join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

    def _extract_sql(self, text: str) -> str:
        match = re.search(r"(SELECT|INSERT|UPDATE|DELETE).*?(;|\Z)", text, re.IGNORECASE | re.DOTALL)
        return match.group(0).strip() if match else text.strip().strip('`').replace('```sql','').replace('```','')
