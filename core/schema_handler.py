"""
Schema handler for AutoQueryAI.
Handles schema preview, ERD, and profiling summary generation.
"""
import pandas as pd
from typing import Dict, Any

def preview_schema(schema: Dict[str, Any]) -> str:
    """
    Return a human-readable schema preview.
    """
    lines = [f"Columns ({schema['num_columns']}):"]
    for col in schema['columns']:
        lines.append(f"- {col['name']} ({col['dtype']}), unique: {col['unique']}, nulls: {col['nulls']}")
    lines.append(f"Rows: {schema['num_rows']}")
    return '\n'.join(lines)

def generate_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a simple profiling summary (can be extended with pandas-profiling).
    """
    profile = {
        'head': df.head(5).to_dict(orient='records'),
        'describe': df.describe(include='all').to_dict(),
        'nulls': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.apply(str).to_dict()
    }
    return profile
