"""
RouterAgent: Classifies user questions and routes to the appropriate agent.
Returns one of: 'sql', 'pandas', 'explainer', 'profiler', 'chart'.
"""
import streamlit as st

class RouterAgent:
    def __init__(self):
        # Prioritize metric/numeric/SQL keywords above explainer
        self.intent_keywords = [
            (['highest', 'lowest', 'average', 'sum', 'max', 'min', 'total', 'count', 'fare', 'distance'], 'sql'),
            (['null', 'missing', 'outlier'], 'profiler'),
            (['overview', 'summary', 'describe'], 'profiler'),
            (['chart', 'plot', 'visualize', 'bar', 'line'], 'chart'),
            (['what is', 'explain', 'meaning of'], 'explainer'),
        ]

    def route(self, question: str) -> str:
        q = question.lower()
        st.session_state["logs"].append(f"[RouterAgent] Raw question: {question}")
        for keywords, intent in self.intent_keywords:
            if any(word in q for word in keywords):
                st.session_state["logs"].append(f"[RouterAgent] classified intent as: {intent}")
                return intent
        st.session_state["logs"].append("[RouterAgent] Fallback: classified as explainer")
        return 'explainer'
