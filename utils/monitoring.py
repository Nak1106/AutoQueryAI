"""
Monitoring utilities for prompt latency, LLM cost, and error rates (Part 6).
"""
import time

class Monitoring:
    def __init__(self):
        self.metrics = []

    def log(self, event, value):
        self.metrics.append({'event': event, 'value': value, 'timestamp': time.time()})

    def get_metrics(self):
        return self.metrics
