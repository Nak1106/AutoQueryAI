"""
Profiler Agent: Provides summary stats, nulls, outliers, etc.
"""
from typing import Any

class ProfilerAgent:
    def __init__(self, llm):
        self.llm = llm

    def profile(self, df: Any) -> str:
        prompt = f"Profile this DataFrame:\n{df.head(5)}"
        return self.llm.generate(prompt)
