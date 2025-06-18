"""
RouterAgent: Classifies user questions and routes to the appropriate agent.
Returns one of: 'sql', 'pandas', 'explainer', 'profiler', 'chart'.
"""
import re
import streamlit as st

class RouterAgent:
    def __init__(self):
        # Regex patterns for robust routing
        self.numeric_pattern = re.compile(r"\b(highest|lowest|average|sum|count|max|min|total|fare|tip|distance|amount|mean|median|std|variance|minimum|maximum|number|percent|percentage|ratio|proportion|frequency|most|least|top|bottom)\b", re.IGNORECASE)
        self.profiler_pattern = re.compile(r"\b(what is this data|what is this dataset|give me an overview|describe this data|data overview|dataset overview|summary of data|summarize data|profile|data profile|show me the data|what columns|what fields|what tables|what are the columns|what are the fields|what are the tables|schema|structure)\b", re.IGNORECASE)
        self.chart_pattern = re.compile(r"\b(chart|plot|visualize|bar|line|scatter|histogram|pie|draw|graph|visualization)\b", re.IGNORECASE)

    def route(self, question: str) -> str:
        q = question.lower()
        st.session_state["logs"].append(f"[RouterAgent] Raw question: {question}")
        if self.numeric_pattern.search(q):
            st.session_state["logs"].append("[RouterAgent] classified intent as: sql")
            return 'sql'
        if self.profiler_pattern.search(q):
            st.session_state["logs"].append("[RouterAgent] classified intent as: profiler")
            return 'profiler'
        if self.chart_pattern.search(q):
            st.session_state["logs"].append("[RouterAgent] classified intent as: chart")
            return 'chart'
        # Fallback: if question starts with 'what is', 'explain', etc., but not a profiler
        if q.startswith('what is') or q.startswith('explain') or 'meaning of' in q:
            st.session_state["logs"].append("[RouterAgent] classified intent as: explainer")
            return 'explainer'
        st.session_state["logs"].append("[RouterAgent] Fallback: classified as sql")
        return 'sql'
