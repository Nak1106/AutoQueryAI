"""
RouterAgent: Classifies user questions and routes to the appropriate agent.
Returns one of: 'sql', 'pandas', 'explainer', 'profiler', 'chart'.
"""
import streamlit as st

class RouterAgent:
    def __init__(self):
        self.intent_keywords = [
            (['null', 'missing', 'outlier'], 'profiler'),
            (['overview', 'summary', 'describe'], 'profiler'),
            (['what is', 'explain', 'meaning of'], 'explainer'),
            (['chart', 'plot', 'visualize', 'bar', 'line'], 'chart'),
            (['show', 'top', 'most', 'sum', 'count', 'group by', 'highest', 'lowest', 'average', 'minimum', 'maximum', 'min', 'max', 'largest', 'smallest', 'biggest', 'least', 'greatest', 'common', 'compare', 'by payment type'], 'sql'),
        ]

    def route(self, question: str) -> str:
        q = question.lower()
        st.session_state["logs"].append(f"[RouterAgent] Raw question: {question}")
        for keywords, intent in self.intent_keywords:
            if any(word in q for word in keywords):
                st.session_state["logs"].append(f"[RouterAgent] classified intent as: {intent}")
                return intent
        # Fallback: if question structure involves grouping/metric analysis, classify as sql
        if ' by ' in q or 'compare' in q or 'average' in q or 'sum' in q:
            st.session_state["logs"].append("[RouterAgent] Fallback: classified as sql (group/metric)")
            return 'sql'
        st.session_state["logs"].append("[RouterAgent] Fallback: classified as sql")
        return 'sql'
