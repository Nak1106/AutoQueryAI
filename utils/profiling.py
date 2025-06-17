"""
Profiling utility using pandas-profiling.
"""
import pandas as pd
from ydata_profiling import ProfileReport

def generate_profile_report(df: pd.DataFrame, output_path: str):
    profile = ProfileReport(df, title="Data Profile Report")
    profile.to_file(output_path)
