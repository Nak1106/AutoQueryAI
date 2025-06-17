"""
RouterAgent: Classifies user questions and routes to the appropriate agent.
Returns one of: 'sql', 'pandas', 'explainer', 'profiler', 'chart'.
"""
from typing import Dict, Any
import re
import streamlit as st

class RouterAgent:
    def __init__(self):
        # Define routing rules as (keywords, intent)
        self.rules = [
            (['about', 'summary', 'overview'], 'profiler'),
            (['plot', 'chart', 'graph'], 'chart'),
            (['missing', 'null', 'outlier'], 'profiler'),
            (["what is this dataset"], 'explainer'),
        ]

    def route(self, question: str) -> str:
        q = question.lower()
        for keywords, intent in self.rules:
            if any(word in q for word in keywords):
                st.session_state["logs"].append(f"[RouterAgent] classified intent as: {intent}")
                return intent
        # Fallback: if question is not SQL-like, return error
        if not any(word in q for word in ['select', 'show', 'list', 'find', 'group by', 'order by', 'where', 'count', 'sum', 'avg', 'min', 'max']):
            st.session_state["logs"].append("[RouterAgent] classified intent as: unable to generate SQL")
            return '-- Unable to generate SQL: consider using a summary or chart instead.'
        st.session_state["logs"].append("[RouterAgent] classified intent as: sql")
        return 'sql'
