"""
RouterAgent: Classifies user questions and routes to the appropriate agent.
Returns one of: 'sql', 'pandas', 'explainer', 'profiler', 'chart'.
"""
import re
import streamlit as st

class RouterAgent:
    def __init__(self):
        # Prioritized keyword matching for intent classification
        self.intent_keywords = [
            (['highest', 'lowest', 'average', 'sum', 'max', 'min', 'total', 'count', 'fare', 'tip', 'group by', 'distance', 'most', 'common'], 'sql'),
            (['null', 'missing', 'outlier'], 'profiler'),
            (['overview', 'summary', 'describe', 'what is this data'], 'profiler'),
            (['chart', 'plot', 'visualize', 'bar', 'line', 'graph'], 'chart'),
            (['meaning of', 'definition of', 'explain', 'what does'], 'explainer')
        ]

    def route(self, question: str) -> str:
        q = question.lower()
        st.session_state["logs"].append(f"[RouterAgent] Raw question: {question}")
        for keywords, intent in self.intent_keywords:
            for word in keywords:
                if word in q:
                    st.session_state["logs"].append(f"[RouterAgent] FINAL intent: {intent} (matched on '{word}')")
                    return intent
        st.session_state["logs"].append("[RouterAgent] FINAL intent: sql (fallback)")
        return 'sql'
