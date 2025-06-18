"""
QueryHistory: Save and retrieve previous queries, SQL, results, and explanations.
"""
import streamlit as st

class QueryHistory:
    def __init__(self):
        if 'query_history' not in st.session_state:
            st.session_state['query_history'] = []

    def add(self, question, sql, result, explanation):
        st.session_state['query_history'].append({
            'question': question,
            'sql': sql,
            'result': result,
            'explanation': explanation
        })

    def get_all(self):
        return st.session_state['query_history']

    def clear(self):
        st.session_state['query_history'] = []
